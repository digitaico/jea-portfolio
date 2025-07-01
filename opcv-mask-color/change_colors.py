import cv2
import numpy as np
import os
import json

def change_colors(image_path, output_path, body_bgr, over_bgr, new_background_bgr=None, debug_mode=False):
    """
    Change the colors of the body and overlay in an image, preserving realism (shadows, wrinkles).
    Optionally changes the background color and provides debug visualization.
    Args:
        image_path (str): Path to the input image.
        output_path (str): Path to save the output image.
        body_bgr (tuple): BGR color for the body (e.g., (0, 0, 255) for red).
        over_bgr (tuple): BGR color for the overlay (e.g., (0, 255, 0) for green).
        new_background_bgr (tuple, optional): BGR color tuple for the new background.
                                               If None, original background is retained.
        debug_mode (bool): If True, displays intermediate masks for debugging.
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Image '{image_path}' not found!")
        return  

    # --- 1. Pre-processing: Gaussian Blur for noise reduction ---
    img_blurred = cv2.GaussianBlur(img, (3, 3), 0)

    # --- 1.1 Isolate figure (apparel item) from background ---
    lower_white = np.array([220, 220, 220]) 
    upper_white = np.array([255, 255, 255])

    mask_background = cv2.inRange(img_blurred, lower_white, upper_white)
    mask_apparel_overall = cv2.bitwise_not(mask_background)

    kernel_apron_close = np.ones((10, 10), np.uint8)
    kernel_apron_open = np.ones((7, 7), np.uint8)
    mask_apparel_overall = cv2.morphologyEx(mask_apparel_overall, cv2.MORPH_CLOSE, kernel_apron_close)
    mask_apparel_overall = cv2.morphologyEx(mask_apparel_overall, cv2.MORPH_OPEN, kernel_apron_open) 

    # --- Window sizing and positioning for debug mode ---
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

        cv2.namedWindow("Debug: Mask - Apparel Overall (after morph)", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Debug: Mask - Body (Final)", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Debug: Mask - Overlay (Final)", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Debug: Mask - Body OR Overlay", cv2.WINDOW_NORMAL)

        cv2.resizeWindow("Debug: Mask - Apparel Overall (after morph)", new_width, new_height)
        cv2.resizeWindow("Debug: Mask - Body (Final)", new_width, new_height)
        cv2.resizeWindow("Debug: Mask - Overlay (Final)", new_width, new_height)
        cv2.resizeWindow("Debug: Mask - Body OR Overlay", new_width, new_height)

        # Position windows - adjust these values if they don't fit your screen layout perfectly
        cv2.moveWindow("Debug: Mask - Apparel Overall (after morph)", 0, 0)
        cv2.moveWindow("Debug: Mask - Body (Final)", new_width + 10, 0)
        cv2.moveWindow("Debug: Mask - Overlay (Final)", (new_width + 10) * 2, 0)
        cv2.moveWindow("Debug: Mask - Body OR Overlay", 0, new_height + 40) # Below the first row

        cv2.imshow("Debug: Mask - Apparel Overall (after morph)", mask_apparel_overall)


    # --- 1.2 Transform image to HSV for color-based segmentation and luminosity extraction ---
    hsv_original = cv2.cvtColor(img_blurred, cv2.COLOR_BGR2HSV)
    h_orig, s_orig, v_orig = cv2.split(hsv_original)

    # --- 1.3 Define HSV ranges for body and overlay based on original apron-1.jpg ---
    # UPDATED HSV values for BODY to include bartacks
    lower_body_hsv = np.array([0, 100, 100])     
    upper_body_hsv = np.array([179, 255, 255])   
    
    # Keeping previous overlay values as a placeholder - you'll need to re-tune these for precision
    lower_overlay_hsv = np.array([68, 31, 0]) 
    upper_overlay_hsv = np.array([179, 255, 255])   

    # --- 1.4 Create masks for body and overlay based on their HSV ranges ---
    mask_body_color = cv2.inRange(hsv_original, lower_body_hsv, upper_body_hsv)
    mask_overlay_color = cv2.inRange(hsv_original, lower_overlay_hsv, upper_overlay_hsv)

    # --- 1.5 Combine masks with the overall apparel mask ---
    mask_body = cv2.bitwise_and(mask_body_color, mask_apparel_overall) 
    mask_overlay = cv2.bitwise_and(mask_overlay_color, mask_apparel_overall) 

    # --- 1.6 Morphological operations to clean body and overlay masks ---
    kernel_body_open = np.ones((7,7), np.uint8)
    kernel_body_close = np.ones((10,10), np.uint8)
    mask_body = cv2.morphologyEx(mask_body, cv2.MORPH_OPEN, kernel_body_open)
    mask_body = cv2.morphologyEx(mask_body, cv2.MORPH_CLOSE, kernel_body_close)

    kernel_overlay_close = np.ones((20,20), np.uint8)
    kernel_overlay_open = np.ones((7,7), np.uint8)
    mask_overlay = cv2.morphologyEx(mask_overlay, cv2.MORPH_CLOSE, kernel_overlay_close)
    mask_overlay = cv2.morphologyEx(mask_overlay, cv2.MORPH_OPEN, kernel_overlay_open)

    # --- Dilate masks slightly to ensure full coverage and smoother edges ---
    dilation_kernel_size = np.ones((3,3), np.uint8)
    mask_body = cv2.dilate(mask_body, dilation_kernel_size, iterations=1)
    mask_overlay = cv2.dilate(mask_overlay, dilation_kernel_size, iterations=1)
    
    # --- Debugging: Show final masks before color application ---
    if debug_mode:
        cv2.imshow("Debug: Mask - Body (Final)", mask_body) 
        cv2.imshow("Debug: Mask - Overlay (Final)", mask_overlay) 
        combined_mask = cv2.bitwise_or(mask_body, mask_overlay)
        cv2.imshow("Debug: Mask - Body OR Overlay", combined_mask)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # --- 1.7 Create new colored regions and apply to image while preserving realism ---
    hsv_modified = hsv_original.copy() 

    # Convert desired BGR colors to HSV to get their Hue and Saturation
    body_new_hsv_flat = cv2.cvtColor(np.array([[body_bgr]], dtype=np.uint8), cv2.COLOR_BGR2HSV)[0][0]
    overlay_new_hsv_flat = cv2.cvtColor(np.array([[over_bgr]], dtype=np.uint8), cv2.COLOR_BGR2HSV)[0][0]

    body_new_h, body_new_s = body_new_hsv_flat[0], body_new_hsv_flat[1]
    overlay_new_h, overlay_new_s = overlay_new_hsv_flat[0], overlay_new_hsv_flat[1]

    # Prioritize Overlay coloring if regions overlap (mask_body_only is correctly calculated here)
    mask_body_only = cv2.subtract(mask_body, mask_overlay)

    # Apply new body color (preserving original V) only to the 'body-only' regions
    hsv_modified[:, :, 0] = np.where(mask_body_only == 255, body_new_h, hsv_modified[:, :, 0])
    hsv_modified[:, :, 1] = np.where(mask_body_only == 255, body_new_s, hsv_modified[:, :, 1])

    # Apply new overlay color (preserving original V)
    hsv_modified[:, :, 0] = np.where(mask_overlay == 255, overlay_new_h, hsv_modified[:, :, 0])
    hsv_modified[:, :, 1] = np.where(mask_overlay == 255, overlay_new_s, hsv_modified[:, :, 1])

    # Convert the modified HSV image back to BGR
    result = cv2.cvtColor(hsv_modified, cv2.COLOR_HSV2BGR)

    # --- Apply new background color if specified ---
    # if new_background_bgr is not None:
    #     colored_background = np.full_like(img, new_background_bgr, dtype=np.uint8)
    #     result = np.where(mask_apparel_overall[:, :, None] == 0, colored_background, result)


    # --- 1.8 Save the output image ---
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    try:
        cv2.imwrite(output_path, result, [cv2.IMWRITE_WEBP_QUALITY, 90])
        print(f"Successfully generated: {output_path}")
    except Exception as e:
        print(f"Error saving image {output_path}: {e}")

# List of color combinations (using contrasting BGR tuples)
color_combinations = [
    {
       "file": "output/apron-body-pockets-green-test.webp", # Output filename
       "body": (0, 255, 0),        # Green
       "overlay": (255, 0, 0),    # Blue (Placeholder, needs tuning)
       "background": (0, 0, 0) # Dummy BGR, won't be applied to background
    },
    {
       "file": "output/apron-body-pockets-blue-test.webp", # Output filename
       "body": (255, 0, 0),        # Blue
       "overlay": (0, 255, 0),    # Green (Placeholder, needs tuning)
       "background": (0, 0, 0) # Dummy BGR, won't be applied to background
    }
]

# 3. Input image path
input_image_base = 'apron-1.jpg'

# 4. Loop through combinations and generate and save images.   
print(f"\n--- Starting batch generation of apparel images from '{input_image_base}' ---")
for combo in color_combinations:
    output_filename = combo["file"]
    body_bgr_color = combo['body']
    overlay_bgr_color = combo['overlay']
    new_bg_color = combo.get('background', None)

    print(f"Generating {output_filename} with body color {body_bgr_color} and overlay color {overlay_bgr_color}")
    
    # <<< Set debug_mode=True to see the masks clearly! >>>
    change_colors(input_image_base, output_filename, body_bgr_color, overlay_bgr_color, new_background_bgr=new_bg_color, debug_mode=True) 

print("\n--- Batch generation completed ---")