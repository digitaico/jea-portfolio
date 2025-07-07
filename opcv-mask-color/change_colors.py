import cv2
import numpy as np
import os
import json
import csv
from PIL import Image # Import Pillow
from openai import opencv_client

client = opencv_client.OpenCVClient()

def hex_to_bgr(hex_color):
    hex_color = hex_color.lstrip('#')
    lv = len(hex_color)
    rgb = tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    return (rgb[2], rgb[1], rgb[0])


def change_colors(image_path, body_mask_path, pockets_mask_path, webbing_mask_path, output_path, body_bgr, over_bgr, new_background_bgr=None, debug_mode=False):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Main image '{image_path}' not found!")
        return  
    
    img_height, img_width = img.shape[:2]

    # --- Load and validate Body Mask ---
    mask_body_raw = cv2.imread(body_mask_path, cv2.IMREAD_GRAYSCALE)
    if mask_body_raw is None:
        print(f"Error: Body mask not found! Check path: '{body_mask_path}'")
        return
    if mask_body_raw.shape[:2] != (img_height, img_width):
        print(f"Warning: Body mask dimensions ({mask_body_raw.shape[:2]}) do not match image dimensions ({img.shape[:2]}). Resizing...")
        mask_body_raw = cv2.resize(mask_body_raw, (img_width, img_height), interpolation=cv2.INTER_NEAREST)
    mask_body_raw = cv2.threshold(mask_body_raw, 128, 255, cv2.THRESH_BINARY)[1].astype(np.uint8)

    # --- Load and validate Pockets Mask ---
    mask_pockets_raw = cv2.imread(pockets_mask_path, cv2.IMREAD_GRAYSCALE)
    if mask_pockets_raw is None:
        print(f"Error: Pockets mask not found! Check path: '{pockets_mask_path}'")
        return
    if mask_pockets_raw.shape[:2] != (img_height, img_width):
        print(f"Warning: Pockets mask dimensions ({mask_pockets_raw.shape[:2]}) do not match image dimensions ({img.shape[:2]}). Resizing...")
        mask_pockets_raw = cv2.resize(mask_pockets_raw, (img_width, img_height), interpolation=cv2.INTER_NEAREST)
    mask_pockets_raw = cv2.threshold(mask_pockets_raw, 128, 255, cv2.THRESH_BINARY)[1].astype(np.uint8)

    # --- Load and validate Webbing Mask ---
    mask_webbing_raw = cv2.imread(webbing_mask_path, cv2.IMREAD_GRAYSCALE)
    if mask_webbing_raw is None:
        print(f"Error: Webbing mask not found! Check path: '{webbing_mask_path}'")
        return
    if mask_webbing_raw.shape[:2] != (img_height, img_width):
        print(f"Warning: Webbing mask dimensions ({mask_webbing_raw.shape[:2]}) do not match image dimensions ({img.shape[:2]}). Resizing...")
        mask_webbing_raw = cv2.resize(mask_webbing_raw, (img_width, img_height), interpolation=cv2.INTER_NEAREST)
    mask_webbing_raw = cv2.threshold(mask_webbing_raw, 128, 255, cv2.THRESH_BINARY)[1].astype(np.uint8)


    # --- DILATE the webbing mask slightly for better coverage ---
    kernel_dilate_webbing = np.ones((3,3), np.uint8) 
    mask_webbing_dilated = cv2.dilate(mask_webbing_raw, kernel_dilate_webbing, iterations=1)


    # --- Define Mutually Exclusive Final Masks with Subtraction ---
    # Start with raw body mask
    mask_body_final = mask_body_raw.copy()
    # Subtract pockets and dilated webbing from body mask
    mask_body_final = cv2.bitwise_and(mask_body_final, cv2.bitwise_not(mask_pockets_raw))
    mask_body_final = cv2.bitwise_and(mask_body_final, cv2.bitwise_not(mask_webbing_dilated))

    # Start with raw pockets mask
    mask_pockets_final = mask_pockets_raw.copy()
    # Subtract body and dilated webbing from pockets mask
    mask_pockets_final = cv2.bitwise_and(mask_pockets_final, cv2.bitwise_not(mask_body_raw))
    mask_pockets_final = cv2.bitwise_and(mask_pockets_final, cv2.bitwise_not(mask_webbing_dilated))

    # Final webbing mask (dilated, and remove any accidental overlap with body/pockets after their subtraction)
    mask_webbing_final = mask_webbing_dilated.copy()
    mask_webbing_final = cv2.bitwise_and(mask_webbing_final, cv2.bitwise_not(mask_body_final)) # Ensure no overlap with final body
    mask_webbing_final = cv2.bitwise_and(mask_webbing_final, cv2.bitwise_not(mask_pockets_final)) # Ensure no overlap with final pockets


    # --- Create overall apparel mask for background removal (union of all parts) ---
    mask_apparel_overall = cv2.bitwise_or(mask_body_final, mask_pockets_final)
    mask_apparel_overall = cv2.bitwise_or(mask_apparel_overall, mask_webbing_final)


    # --- Apply colors while preserving original luminosity/texture for both body and pockets ---

    # Convert original image to HSV once for luminosity extraction
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Get the HSV values for the target colors (body and pockets)
    body_hsv_color = cv2.cvtColor(
        np.array([[body_bgr]], dtype=np.uint8), cv2.COLOR_BGR2HSV
    )[0, 0]
    overlay_hsv_color = cv2.cvtColor(
        np.array([[over_bgr]], dtype=np.uint8), cv2.COLOR_BGR2HSV
    )[0, 0]

    # Create a mutable copy of the original image's HSV data to apply changes
    # All modifications to hue/saturation will happen on this copy, preserving original Value (luminosity)
    modified_apparel_hsv = img_hsv.copy()

    # --- Process Body Mask (with preserved texture) ---
    # Apply target Hue and Saturation to the body area where the mask is active
    modified_apparel_hsv[mask_body_final == 255, 0] = body_hsv_color[0] # Apply new Hue
    modified_apparel_hsv[mask_body_final == 255, 1] = body_hsv_color[1] # Apply new Saturation
    # The Value (luminosity) channel (index 2) is left untouched from original img_hsv for the body.

    # --- Process Pockets Mask (with preserved texture) ---
    # Apply target Hue and Saturation to the pockets area where the mask is active
    modified_apparel_hsv[mask_pockets_final == 255, 0] = overlay_hsv_color[0] # Apply new Hue
    modified_apparel_hsv[mask_pockets_final == 255, 1] = overlay_hsv_color[1] # Apply new Saturation
    # The Value (luminosity) channel (index 2) is left untouched from original img_hsv for the pockets.


    # Convert the fully modified HSV image (apparel parts now colored with preserved texture) back to BGR
    result_bgr_apparel_colored = cv2.cvtColor(modified_apparel_hsv, cv2.COLOR_HSV2BGR)

    # Start the final result image with the original image (to keep webbing, etc., intact)
    result_bgr = img.copy() 
    
    # Now, blend the newly colored apparel parts onto the original image.
    # Where the overall apparel mask is active, take pixels from result_bgr_apparel_colored.
    # Otherwise, keep pixels from the original image (which result_bgr currently is).
    result_bgr = np.where(mask_apparel_overall[:, :, None] == 255, result_bgr_apparel_colored, result_bgr)
    
    # This ensures that webbing (part of the original image but not explicitly colored)
    # and the original background (before new_background_bgr is applied) are preserved correctly.


    # --- Debugging: Show final masks and the direct BGR result ---
    if debug_mode:
        display_width = 400 
        display_height = 400 

        height, width = img.shape[:2] # Use original image dims for aspect ratio
        aspect_ratio = width / height   
        if aspect_ratio > 1: 
            new_width = display_width
            new_height = int(new_width / aspect_ratio)
        else: 
            new_height = display_height
            new_width = int(new_height * aspect_ratio)      

        # Row 1: Final Masks 
        cv2.namedWindow("Debug: Mask - Apparel Overall", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Debug: Mask - Body (Final)", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Debug: Mask - Pockets (Final)", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Debug: Mask - Webbings (Final)", cv2.WINDOW_NORMAL) 

        cv2.resizeWindow("Debug: Mask - Apparel Overall", new_width, new_height)
        cv2.resizeWindow("Debug: Mask - Body (Final)", new_width, new_height)
        cv2.resizeWindow("Debug: Mask - Pockets (Final)", new_width, new_height)
        cv2.resizeWindow("Debug: Mask - Webbings (Final)", new_width, new_height)

        cv2.moveWindow("Debug: Mask - Apparel Overall", 0, 0)
        cv2.moveWindow("Debug: Mask - Body (Final)", new_width + 10, 0)
        cv2.moveWindow("Debug: Mask - Pockets (Final)", (new_width + 10) * 2, 0)
        cv2.moveWindow("Debug: Mask - Webbings (Final)", (new_width + 10) * 3, 0) 

        cv2.imshow("Debug: Mask - Apparel Overall", mask_apparel_overall)
        cv2.imshow("Debug: Mask - Body (Final)", mask_body_final) 
        cv2.imshow("Debug: Mask - Pockets (Final)", mask_pockets_final)
        cv2.imshow("Debug: Mask - Webbings (Final)", mask_webbing_final)


        # Row 2: Raw Masks (Originals before any subtraction)
        cv2.namedWindow("Debug: Mask - Body (RAW)", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Debug: Mask - Pockets (RAW)", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Debug: Mask - Webbings (RAW)", cv2.WINDOW_NORMAL)

        cv2.resizeWindow("Debug: Mask - Body (RAW)", new_width, new_height)
        cv2.resizeWindow("Debug: Mask - Pockets (RAW)", new_width, new_height)
        cv2.resizeWindow("Debug: Mask - Webbings (RAW)", new_width, new_height)

        cv2.moveWindow("Debug: Mask - Body (RAW)", 0, new_height + 50) 
        cv2.moveWindow("Debug: Mask - Pockets (RAW)", new_width + 10, new_height + 50)
        cv2.moveWindow("Debug: Mask - Webbings (RAW)", (new_width + 10) * 2, new_height + 50)

        cv2.imshow("Debug: Mask - Body (RAW)", mask_body_raw)
        cv2.imshow("Debug: Mask - Pockets (RAW)", mask_pockets_raw)
        cv2.imshow("Debug: Mask - Webbings (RAW)", mask_webbing_raw)

        # Row 3: Direct BGR Result (Instead of HSV channels)
        cv2.namedWindow("Debug: Direct BGR Result (Colored)", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Debug: Direct BGR Result (Colored)", new_width, new_height)
        cv2.moveWindow("Debug: Direct BGR Result (Colored)", 0, new_height * 2 + 100)
        cv2.imshow("Debug: Direct BGR Result (Colored)", result_bgr) # Display the result_bgr directly

        cv2.waitKey(0)
        cv2.destroyAllWindows()


    if new_background_bgr is not None:
        mask_background = cv2.bitwise_not(mask_apparel_overall) 
        colored_background = np.full_like(img, new_background_bgr, dtype=np.uint8)
        result_bgr = np.where(mask_background[:, :, None] == 255, colored_background, result_bgr)

    # Convert to RGB for saving (Pillow expects RGB)
    result_rgb = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    try:
        # Save debug output in PNG format
        cv2.imwrite(os.path.join(output_dir, "debug_final_output.png"), result_rgb)
        print(f"Saved debug_final_output.png in {output_dir}")
        
        # --- Using Pillow to save the final output ---
        img_pil = Image.fromarray(result_rgb)
        
        ext = os.path.splitext(output_path)[1].lower()

        if ext == '.webp':
            img_pil.save(output_path, quality=90)
            print(f"Successfully generated (via Pillow): {output_path}")
        elif ext == '.png':
            img_pil.save(output_path)
            print(f"Successfully generated (via Pillow): {output_path}")
        elif ext == '.jpg' or ext == '.jpeg':
            img_pil.save(output_path, quality=90)
            print(f"Successfully generated (via Pillow): {output_path}")
        else:
            cv2.imwrite(output_path, result_rgb) 
            print(f"Warning: Output format {ext} not explicitly handled by Pillow with specific settings. Saved using OpenCV.")


    except Exception as e:
        print(f"Error saving image {output_path} or debug_final_output.png: {e}")

if __name__ == "__main__":
    input_image_template = 'template.jpg'
    body_mask_image = 'body_mask.png' 
    pockets_mask_image = 'pockets_mask.png'
    webbing_mask_image = 'webbing_mask.png' # Assuming this mask is still valid and present
    
    csv_file_path = 'color_combinations.csv' 

    color_combinations = []
    try:
        with open(csv_file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                color_combinations.append(row)
        print(f"Successfully loaded color combinations from '{csv_file_path}'")
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file_path}' not found. Please create it.")
        exit()
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        exit()

    print(f"\n--- Starting batch generation of apparel images from '{input_image_template}' ---")
    for combo in color_combinations:
        output_filename_base = combo["file"] 
        output_filename = os.path.join("output", output_filename_base)

        body_hex_color = combo['body']
        overlay_hex_color = combo['overlay']
        
        body_bgr_color = hex_to_bgr(body_hex_color)
        overlay_bgr_color = hex_to_bgr(overlay_hex_color)
        
        new_bg_color = (255, 255, 255) # White background

        print(f"Generating {output_filename} with body color {body_hex_color} and overlay color {overlay_hex_color}")
        
        # Ensure debug_mode=True for the first run to verify new masks and colors
        change_colors(input_image_template, body_mask_image, pockets_mask_image, webbing_mask_image, output_filename, body_bgr_color, overlay_bgr_color, new_background_bgr=new_bg_color, debug_mode=False) 

    print("\n--- Batch generation completed ---")