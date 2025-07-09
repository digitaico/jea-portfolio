import cv2
import numpy as np
import pandas as pd
import os
from PIL import Image, ImageEnhance
from skimage import color
import cv2.cuda


print(cv2.cuda.getCudaEnabledDeviceCount())

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""

    if pd.isna(hex_color) or hex_color == '':
        return None
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def apply_color_to_region(image, mask, target_color, method='lab_colorize'):
    """Apply color to specific region defined by mask while preserving luminosity"""
    if target_color is None:
        return image

    # Convert to numpy arrays
    img_array = np.array(image).astype(np.float32) / 255.0
    mask_array = np.array(mask).astype(np.float32) / 255.0

    # Ensure mask is 2D (grayscale)
    if len(mask_array.shape) > 2:
        mask_array = mask_array[:, :, 0]

    # Create a binary mask for areas to colorize
    # Use a threshold to make it strictly binary if it's not already
    color_mask = mask_array > 0.1

    if method == 'lab_colorize':
        # Convert original image to LAB color space
        lab_image = color.rgb2lab(img_array)

        # Convert target color to LAB
        target_color_rgb_normalized = np.array(target_color).astype(np.float32) / 255.0
        # Expand dimensions to (1,1,3) for color.rgb2lab to treat it as a single pixel color
        target_lab = color.rgb2lab(target_color_rgb_normalized[np.newaxis, np.newaxis, :])[0, 0, :]

        # Extract L, A, B channels
        L_channel = lab_image[:, :, 0]
        A_channel = lab_image[:, :, 1]
        B_channel = lab_image[:, :, 2]

        # Apply the target color's A and B channels to the masked region
        # while preserving the original L channel
        A_channel[color_mask] = target_lab[1]
        B_channel[color_mask] = target_lab[2]

        # Recombine LAB channels
        colorized_lab_image = np.stack([L_channel, A_channel, B_channel], axis=-1)

        # Convert back to RGB
        colorized_rgb_image = color.lab2rgb(colorized_lab_image)

        # Clip values to [0, 1] and convert back to 0-255 range for PIL
        colorized_rgb_image = np.clip(colorized_rgb_image, 0, 1) * 255.0
        return Image.fromarray(colorized_rgb_image.astype(np.uint8))

    return image # Return original image if method is not recognized

def process_image_variants(template_path, masks_data, csv_path, output_dir):
    """
    Generate image variants based on a template, masks, and color combinations from a CSV.
    """
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(csv_path)

    base_image = Image.open(template_path).convert("RGB")

    # Load masks once
    masks = {}
    for part, mask_file in masks_data.items():
        if os.path.exists(mask_file):
            mask = Image.open(mask_file).convert("L") # Ensure mask is grayscale (L mode)
            masks[part] = mask
            print(f"Loaded mask for {part}: {mask_file}")
        else:
            print(f"Warning: Mask file not found for {part}: {mask_file}")
            masks[part] = None

    for index, row in df.iterrows():
        filename = row['filename']
        body_color_hex = row['body_color']
        pockets_color_hex = row['pockets_color']

        print(f"\nProcessing {filename}...")

        current_image = base_image.copy()

        # Convert hex colors to RGB tuples
        body_rgb = hex_to_rgb(body_color_hex)
        pockets_rgb = hex_to_rgb(pockets_color_hex)

        # Apply colors using masks
        if 'body' in masks and body_rgb:
            print(f"Applying body color: {body_color_hex}")
            current_image = apply_color_to_region(current_image, masks['body'], body_rgb)
        else:
            print("Skipping body color application (mask or color missing).")

        if 'pockets' in masks and pockets_rgb:
            print(f"Applying pockets color: {pockets_color_hex}")
            current_image = apply_color_to_region(current_image, masks['pockets'], pockets_rgb)
        else:
            print("Skipping pockets color application (mask or color missing).")

        # As per your request, we will not apply webbing color
        # if 'webbings' in masks and webbings_rgb:
        #     print(f"Applying webbings color: {webbings_color_hex}")
        #     current_image = apply_color_to_region(current_image, masks['webbings'], webbings_rgb)
        # else:
        #     print("Skipping webbings color application (mask or color missing).")


        output_path = os.path.join(output_dir, filename)
        current_image.save(output_path)
        print(f"Saved: {output_path}")

    print("\nAll variants generated successfully!")

if __name__ == "__main__":
    # Create sample CSV if it doesn't exist (for testing)
    if not os.path.exists('data/color_combinations.csv'):
        create_sample_csv()

    # Define paths to your assets
    template_image_path = 'assets/template.jpg'
    body_mask_path = 'assets/body_mask.png'
    pockets_mask_path = 'assets/pockets_mask.png'
    webbing_mask_path = 'assets/webbing_mask.png' # Still define it, but it won't be used in apply_color_to_region

    masks_data = {
        'body': body_mask_path,
        'pockets': pockets_mask_path,
        'webbings': webbing_mask_path
    }
    csv_file_path = 'data/color_combinations.csv'
    output_directory = 'output/main_3/'

    # Ensure assets directory exists and template image is there (for user reference)
    os.makedirs('assets', exist_ok=True)
    # You would place your template.jpg and mask files into the 'assets' directory.
    # For example, if you place template.jpg, body_mask.png, pockets_mask.png, webbing_mask.png
    # inside an 'assets' folder in the same directory as your script.

    # Run the image processing
    process_image_variants(template_image_path, masks_data, csv_file_path, output_directory)