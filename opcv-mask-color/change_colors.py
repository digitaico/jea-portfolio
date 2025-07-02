import cv2
import numpy as np
import os
import json

def change_colors(image_path, body_mask_path, pockets_mask_path, webbing_mask_path, output_path, body_bgr, over_bgr, new_background_bgr=None, debug_mode=False):
    """
    Change the colors of the body and overlay in an image, preserving realism (shadows, wrinkles).
    Webbing areas are preserved in their original color.
    Optionally changes the background color and provides debug visualization.
    Args:
        image_path (str): Path to the input image (colored apparel template, e.g., 'template.jpg').
        body_mask_path (str): Path to the black-and-white mask of the body only.
        pockets_mask_path (str): Path to the black-and-white mask of the pockets only.
        webbing_mask_path (str): Path to the black-and-white mask of the webbing only.
        output_path (str): Path to save the output image.
        body_bgr (tuple): BGR color for the body (e.g., (0, 0, 255) for red).
        over_bgr (tuple): BGR color for the overlay (e.g., (0, 255, 0) for green).
        new_background_bgr (tuple, optional): BGR color tuple for the new background.
                                               If None, original background is retained.
        debug_mode (bool): If True, displays intermediate masks for debugging.
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Main image '{image_path}' not found!")
        return  

    # --- Load all manual masks ---
    mask_body_raw = cv2.imread(body_mask_path, cv2.IMREAD_GRAYSCALE)
    mask_pockets_raw = cv2.imread(pockets_mask_path, cv2.IMREAD_GRAYSCALE)
    mask_webbing = cv2.imread(webbing_mask_path, cv2.IMREAD_GRAYSCALE)

    # Validate and prepare each mask
    if mask_body_raw is None:
        print(f"Error: Body mask not found! Check path: '{body_mask_path}'")
        return
    if img.shape[:2] != mask_body_raw.shape[:2]:
        print(f"Warning: Body mask dimensions ({mask_body_raw.shape[:2]}) do not match image dimensions ({img.shape[:2]}). Resizing...")
        mask_body_raw = cv2.resize(mask_body_raw, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
    mask_body_raw = cv2.threshold(mask_body_raw, 128, 255, cv2.THRESH_BINARY)[1]

    if mask_pockets_raw is None:
        print(f"Error: Pockets mask not found! Check path: '{pockets_mask_path}'")
        return
    if img.shape[:2] != mask_pockets_raw.shape[:2]:
        print(f"Warning: Pockets mask dimensions ({mask_pockets_raw.shape[:2]}) do not match image dimensions ({img.shape[:2]}). Resizing...")
        mask_pockets_raw = cv2.resize(mask_pockets_raw, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
    mask_pockets_raw = cv2.threshold(mask_pockets_raw, 128, 255, cv2.THRESH_BINARY)[1]

    if mask_webbing is None:
        print(f"Error: Webbing mask not found! Check path: '{webbing_mask_path}'")
        return
    if img.shape[:2] != mask_webbing.shape[:2]:
        print(f"Warning: Webbing mask dimensions ({mask_webbing.shape[:2]}) do not match image dimensions ({img.shape[:2]}). Resizing...")
        mask_webbing = cv2.resize(mask_webbing, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
    mask_webbing = cv2.threshold(mask_webbing, 128, 255, cv2.THRESH_BINARY)[1]

    # --- DILATE the webbing mask slightly to ensure full coverage of original webbing pixels ---
    kernel_dilate_webbing = np.ones((3,3), np.uint8) # Small 3x3 kernel for dilation
    mask_webbing = cv2.dilate(mask_webbing, kernel_dilate_webbing, iterations=1)


    # --- Pre-processing: Gaussian Blur for noise reduction on the colored image ---
    img_blurred = cv2.GaussianBlur(img, (5, 5), 0)

    # --- Transform image to HSV for luminosity extraction ---
    hsv_original = cv2.cvtColor(img_blurred, cv2.COLOR_BGR2HSV)
    h_orig, s_orig, v_orig = cv2.split(hsv_original)

    # --- Combine all raw masks to create the overall apparel mask ---
    # This ensures mask_apparel_overall is perfect as it combines segmented parts
    mask_apparel_overall = cv2.bitwise_or(mask_body_raw, mask_pockets_raw)
    mask_apparel_overall = cv2.bitwise_or(mask_apparel_overall, mask_webbing)


    # --- Final Mask Logic: Ensure no overlaps and webbing is always excluded ---
    # Start with the body mask, then subtract pockets and webbing
    mask_body_final = mask_body_raw.copy()
    mask_body_final = cv2.subtract(mask_body_final, mask_pockets_raw) # Remove pockets from body
    mask_body_final = cv2.subtract(mask_body_final, mask_webbing)      # Remove webbing from body

    # Start with pockets mask, then subtract body and webbing
    mask_pockets_final = mask_pockets_raw.copy()
    mask_pockets_final = cv2.subtract(mask_pockets_final, mask_body_raw) # Remove body from pockets (should be minimal overlap, but good for safety)
    mask_pockets_final = cv2.subtract(mask_pockets_final, mask_webbing)  # Remove webbing from pockets

    # --- Debugging: Show final masks before color application ---
    if debug_mode:
        display_width = 400 # Smaller width for multiple debug windows
        display_height = 400 # Smaller height for multiple debug windows

        height, width = img_blurred.shape[:2]
        aspect_ratio = width / height   
        if aspect_ratio > 1: # Landscape
            new_width = display_width
            new_height = int(new_width / aspect_ratio)
        else: # Portrait or Square
            new_height = display_height
            new_width = int(new_height * aspect_ratio)      

        cv2.namedWindow("Debug: Mask - Apparel Overall", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Debug: Mask - Body (Final)", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Debug: Mask - Pockets (Final)", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Debug: Mask - Webbings", cv2.WINDOW_NORMAL)

        cv2.resizeWindow("Debug: Mask - Apparel Overall", new_width, new_height)
        cv2.resizeWindow("Debug: Mask - Body (Final)", new_width, new_height)
        cv2.resizeWindow("Debug: Mask - Pockets (Final)", new_width, new_height)
        cv2.resizeWindow("Debug: Mask - Webbings", new_width, new_height)

        # Position windows - adjust these values if they don't fit your screen layout perfectly
        cv2.moveWindow("Debug: Mask - Apparel Overall", 0, 0)
        cv2.moveWindow("Debug: Mask - Body (Final)", new_width + 10, 0)
        cv2.moveWindow("Debug: Mask - Pockets (Final)", (new_width + 10) * 2, 0)
        cv2.moveWindow("Debug: Mask - Webbings", 0, new_height + 40) 

        cv2.imshow("Debug: Mask - Apparel Overall", mask_apparel_overall)
        cv2.imshow("Debug: Mask - Body (Final)", mask_body_final) 
        cv2.imshow("Debug: Mask - Pockets (Final)", mask_pockets_final)
        cv2.imshow("Debug: Mask - Webbings", mask_webbing)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


    # --- Create new colored regions and apply to image while preserving realism ---
    hsv_modified = hsv_original.copy() 

    # Convert desired BGR colors to HSV to get their Hue and Saturation
    body_new_hsv_flat = cv2.cvtColor(np.array([[body_bgr]], dtype=np.uint8), cv2.COLOR_BGR2HSV)[0][0]
    overlay_new_hsv_flat = cv2.cvtColor(np.array([[over_bgr]], dtype=np.uint8), cv2.COLOR_BGR2HSV)[0][0]

    body_new_h, body_new_s = body_new_hsv_flat[0], body_new_hsv_flat[1]
    overlay_new_h, overlay_new_s = overlay_new_hsv_flat[0], overlay_new_hsv_flat[1]

    # Apply new body color (preserving original V) only to the 'body-only' regions
    hsv_modified[:, :, 0] = np.where(mask_body_final == 255, body_new_h, hsv_modified[:, :, 0])
    hsv_modified[:, :, 1] = np.where(mask_body_final == 255, body_new_s, hsv_modified[:, :, 1])

    # Apply new overlay color (preserving original V) - this is for pockets
    hsv_modified[:, :, 0] = np.where(mask_pockets_final == 255, overlay_new_h, hsv_modified[:, :, 0])
    hsv_modified[:, :, 1] = np.where(mask_pockets_final == 255, overlay_new_s, hsv_modified[:, :, 1])

    # Convert the modified HSV image back to BGR
    result = cv2.cvtColor(hsv_modified, cv2.COLOR_HSV2BGR)

    # --- Apply new background color if specified ---
    # To apply a new background, we need to create a mask for the background.
    # The background is anything that is NOT part of mask_apparel_overall
    if new_background_bgr is not None:
        mask_background = cv2.bitwise_not(mask_apparel_overall)
        colored_background = np.full_like(img, new_background_bgr, dtype=np.uint8)
        result = np.where(mask_background[:, :, None] == 255, colored_background, result)

    # --- FINAL STEP: Convert the output image from BGR to RGB for correct display in most viewers ---
    result = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)


    # --- Save the output image ---
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    try:
        cv2.imwrite(output_path, result, [cv2.IMWRITE_WEBP_QUALITY, 90])
        print(f"Successfully generated: {output_path}")
    except Exception as e:
        print(f"Error saving image {output_path}: {e}")

# List of color combinations (using contrasting BGR tuples, but output will be RGB)
color_combinations = [
    {
       "file": "output/apron-body-pockets-green-test.webp", # Output filename
       "body": (0, 255, 0),        # Green (BGR)
       "overlay": (255, 0, 0),    # Blue (BGR) (for pockets)
       "background": (0, 0, 0) # Black background
    },
    {
       "file": "output/apron-body-pockets-blue-test.webp", # Output filename
       "body": (255, 0, 0),        # Blue (BGR)
       "overlay": (0, 255, 0),    # Green (BGR) (for pockets)
       "background": (255, 255, 255) # White background
    }
]

# 3. Input image paths and manual masks
input_image_template = 'template.jpg' # Our main template image
body_mask_image = 'body_mask.png'     # Your new body mask
pockets_mask_image = 'pockets_mask.png' # Your new pockets mask
webbing_mask_image = 'webbing_mask.png' # Your webbing mask

# 4. Loop through combinations and generate and save images.   
print(f"\n--- Starting batch generation of apparel images from '{input_image_template}' ---")
for combo in color_combinations:
    output_filename = combo["file"]
    body_bgr_color = combo['body']
    overlay_bgr_color = combo['overlay']
    new_bg_color = combo.get('background', None) # Get background color, default None

    print(f"Generating {output_filename} with body color {body_bgr_color} and overlay color {overlay_bgr_color}")
    
    # <<< Set debug_mode=True to see the masks clearly! >>>
    change_colors(input_image_template, body_mask_image, pockets_mask_image, webbing_mask_image, output_filename, body_bgr_color, overlay_bgr_color, new_background_bgr=new_bg_color, debug_mode=True) 

print("\n--- Batch generation completed ---")