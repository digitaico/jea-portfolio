import cv2
import numpy as np
import os
import json

def change_colors(image_path, output_path, body_bgr, over_bgr ):
    """
    Change the colors of the body and overlay in an image.
    Args:
        image_path (str): Path to the input image.
        output_path (str): Path to save the output image.
        body_bgr (tuple): BGR color for the body (e.g., (0, 0, 255) for red).
        over_bgr (tuple): BGR color for the overlay (e.g., (0, 255, 0) for green).
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Image '{image_path}' not found!")
        return  

    # 1.1 Isolate figure from background
    lower_white = np.array([240,240,240])
    upper_white = np.array([255,255,255])

    mask_background = cv2.inRange(img, lower_white, upper_white)
    mask_body_overall = cv2.bitwise_not(mask_background)

    # Clean body mask with morphological operations
    kernel = np.ones((5, 5), np.uint8)
    mask_body_overall = cv2.morphologyEx(mask_body_overall, cv2.MORPH_CLOSE, kernel)
    mask_body_overall = cv2.morphologyEx(mask_body_overall, cv2.MORPH_OPEN, kernel) 

    # 1.2 Transform image to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 1.3 Define HSV ranges for body and overlay
    lower_body_hsv = np.array([8, 89, 100])     
    upper_body_hsv = np.array([100, 255, 255])   
    lower_overlay_hsv = np.array([68, 31, 0])     
    upper_overlay_hsv = np.array([179, 255, 255])   

    # 1.4 Create masks for body and overlay
    mask_body_color = cv2.inRange(hsv, lower_body_hsv, upper_body_hsv)
    mask_overlay_color = cv2.inRange(hsv, lower_overlay_hsv, upper_overlay_hsv)

    # 1.5 Combine masks
    mask_body = cv2.bitwise_and(mask_body_color, mask_body_overall) 
    mask_overlay = cv2.bitwise_and(mask_overlay_color, mask_body_overall) 

    # Morphological operations to clean masks
    kernel_parts = np.ones((3,3), np.uint8)
    mask_body = cv2.morphologyEx(mask_body, cv2.MORPH_OPEN, kernel_parts)
    mask_body = cv2.morphologyEx(mask_body, cv2.MORPH_CLOSE, kernel_parts)
    mask_overlay = cv2.morphologyEx(mask_overlay, cv2.MORPH_OPEN, kernel_parts)
    mask_overlay = cv2.morphologyEx(mask_overlay, cv2.MORPH_CLOSE, kernel_parts)

    # 1.6 Create new colored regios and apply to image
    colored_body = np.full_like(img, body_bgr, dtype=np.uint8)
    colored_overlay = np.full_like(img, over_bgr, dtype=np.uint8)

    result = img.copy()

    # apply body color
    result = np.where(mask_body[:, :, None] == 255, colored_body, result)
    # apply overlay color
    result = np.where(mask_overlay[:, :, None] == 255, colored_overlay, result) 

    # 1.7 Save the output image
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    try:
        # Save as webP of high quality
        cv2.imwrite(output_path, result, [cv2.IMWRITE_WEBP_QUALITY, 90])
        print(f"Successfully generated: {output_path}")
    except Exception as e:
        print(f"Error saving image {output_path}: {e}")

# List of color combinations
color_combinations = [
    {
       "file": "apro-gaira.webp",
       "body": (0, 0, 255),  # Red
       "overlay": (0, 255, 0)   # Green
    },
    {
       "file": "apron-bureche.webp",
       "body": (0, 255, 0),  # Red
       "overlay": (255, 255, 0)   # Green
    }
]

# 3. Image path
input_image_base = 'apron-1.jpg'

#  4. Loop through combinations and generate and save images.   
print(f"\n--- Starting batch generation of apparel images from '{input_image_base}' ---")
for combo in color_combinations:
    output_filename = combo["file"]

    body_bgr_color = combo['body']
    overlay_bgr_color = combo['overlay']

    print(f"Generating {output_filename} with body color {body_bgr_color} and overlay color {overlay_bgr_color}")
    change_colors(input_image_base, output_filename, body_bgr_color, overlay_bgr_color)

print("\n --- Batch generation completed ---")
