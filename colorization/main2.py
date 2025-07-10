# --- BY CLAUDE ---

import cv2
import numpy as np
import pandas as pd
import os
from PIL import Image, ImageEnhance
from skimage import color

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
    
    # Debug info
    print(f"  Target color RGB: {target_color}")
    print(f"  Pixels to be colored: {np.sum(mask_array > 0.1)}")
    
    # Ensure mask is 2D
    if len(mask_array.shape) > 2:
        mask_array = mask_array[:, :, 0]
    
    # Create binary mask for areas to colorize
    color_mask = mask_array > 0.1
    
    if method == 'lab_colorize':
        # Convert RGB to LAB color space
        lab_image = color.rgb2lab(img_array)
        
        # Convert target color to LAB
        target_rgb_norm = np.array(target_color).reshape(1, 1, 3) / 255.0
        target_lab = color.rgb2lab(target_rgb_norm)[0, 0]
        
        print(f"  Target color LAB: L={target_lab[0]:.1f}, A={target_lab[1]:.1f}, B={target_lab[2]:.1f}")
        
        # Apply color only to A and B channels, preserve L (luminance)
        result_lab = lab_image.copy()
        
        # Smoothly blend A and B channels while keeping original luminance
        blend_strength = 0.9
        result_lab[:, :, 1] = np.where(color_mask, 
                                       lab_image[:, :, 1] * (1 - mask_array * blend_strength) + 
                                       target_lab[1] * mask_array * blend_strength,
                                       lab_image[:, :, 1])
        
        result_lab[:, :, 2] = np.where(color_mask,
                                       lab_image[:, :, 2] * (1 - mask_array * blend_strength) + 
                                       target_lab[2] * mask_array * blend_strength,
                                       lab_image[:, :, 2])
        
        # Convert back to RGB
        result_rgb = color.lab2rgb(result_lab)
        
    elif method == 'hsv_colorize':
        # Alternative: HSV method - preserve value (brightness)
        hsv_image = color.rgb2hsv(img_array)
        
        # Convert target color to HSV
        target_rgb_norm = np.array(target_color).reshape(1, 1, 3) / 255.0
        target_hsv = color.rgb2hsv(target_rgb_norm)[0, 0]
        
        result_hsv = hsv_image.copy()
        
        # Apply target hue and saturation, preserve value (brightness)
        blend_strength = 0.7
        result_hsv[:, :, 0] = np.where(color_mask,
                                       target_hsv[0] * mask_array * blend_strength + 
                                       hsv_image[:, :, 0] * (1 - mask_array * blend_strength),
                                       hsv_image[:, :, 0])
        
        result_hsv[:, :, 1] = np.where(color_mask,
                                       target_hsv[1] * mask_array * blend_strength + 
                                       hsv_image[:, :, 1] * (1 - mask_array * blend_strength),
                                       hsv_image[:, :, 1])
        
        # Convert back to RGB
        result_rgb = color.hsv2rgb(result_hsv)
    
    else:
        # Fallback to original overlay method
        result_rgb = img_array.copy()
        target_normalized = np.array(target_color) / 255.0
        
        for i in range(3):
            result_rgb[:, :, i] = np.where(
                color_mask,
                img_array[:, :, i] * (1 - mask_array * 0.7) + target_normalized[i] * mask_array * 0.7,
                img_array[:, :, i]
            )
    
    # Convert back to 0-255 range and ensure valid values
    result_rgb = np.clip(result_rgb, 0, 1)
    result_uint8 = (result_rgb * 255).astype(np.uint8)
    
    # Check if any pixels were actually changed
    changes = np.sum(np.abs(result_uint8 - (img_array * 255).astype(np.uint8)) > 1)
    print(f"  Pixels changed: {changes}")
    
    return Image.fromarray(result_uint8)

def load_images_and_masks():
    """Load template image and all masks"""
    template = Image.open('assets/template.jpg').convert('RGB')
    
    masks = {
        'body': Image.open('assets/body_mask.png').convert('L'),
        'pockets': Image.open('assets/pockets_mask.png').convert('L'),
        'webbings': Image.open('assets/webbing_mask.png').convert('L')
    }
    
    return template, masks

def generate_color_variants():
    """Main function to generate all color variants"""
    
    # Load template and masks
    print("Loading template and masks...")
    template, masks = load_images_and_masks()
    
    # Debug: Check template properties
    print(f"Template size: {template.size}")
    print(f"Template mode: {template.mode}")
    
    # Debug: Check each mask
    for name, mask in masks.items():
        print(f"\n{name} mask size: {mask.size}")
        print(f"{name} mask mode: {mask.mode}")
        mask_array = np.array(mask)
        print(f"{name} mask values: min={mask_array.min()}, max={mask_array.max()}")
        print(f"{name} mask non-zero pixels: {np.sum(mask_array > 0)}")
    
    # Read color combinations
    print("\nReading color combinations...")
    color_data = pd.read_csv('data/color_combinations.csv')
    print(f"CSV columns: {color_data.columns.tolist()}")
    print(f"First row: {color_data.iloc[0].to_dict()}")
    
    # Create output directory
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each color combination
    print(f"\nProcessing {len(color_data)} color combinations...")
    
    for index, row in color_data.iterrows():
        print(f"\n--- Processing variant {index + 1}/{len(color_data)}: {row['filename']} ---")
        
        # Start with template copy
        working_image = template.copy()
        
        # Apply body color if specified
        body_color = hex_to_rgb(row['body_color'])
        print(f"Applying body color: {row['body_color']} -> {body_color}")
        working_image = apply_color_to_region(
            working_image, 
            masks['body'], 
            body_color, 
            method='lab_colorize'
        )
        
        # Apply overlay color to pockets if specified
        overlay_color = hex_to_rgb(row['overlay_color'])
        print(f"Applying overlay color to pockets: {row['overlay_color']} -> {overlay_color}")
        working_image = apply_color_to_region(
            working_image, 
            masks['pockets'], 
            overlay_color, 
            method='lab_colorize'
        )
        
        # Save the result
        output_path = os.path.join(output_dir, row['filename'])
        working_image.save(output_path, 'JPEG', quality=95)
        print(f"Saved: {output_path}")
    
    print("\nAll variants generated successfully!")

def create_sample_csv():
    """Create a sample CSV file for testing"""
    sample_data = {
        'filename': [
            'apron_red_blue_yellow.jpg',
            'apron_green_purple_orange.jpg',
            'apron_black_white_red.jpg',
            'apron_blue_red.jpg',
            'apron_yellow_green_blue.jpg'
        ],
        'body_color': [
            '#FF0000',  # Red
            '#00FF00',  # Green
            '#000000',  # Black
            '#0000FF',  # Blue
            '#FFFF00'   # Yellow
        ],
        'pockets_color': [
            '#0000FF',  # Blue
            '#800080',  # Purple
            '#FFFFFF',  # White
            '#FF0000',  # Red
            '#00FF00'   # Green
        ],
        'webbings_color': [
            '#FFFF00',  # Yellow
            '#FFA500',  # Orange
            '#FF0000',  # Red
            '',         # No color (empty)
            '#0000FF'   # Blue
        ]
    }
    
    df = pd.DataFrame(sample_data)
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/color_combinations.csv', index=False)
    print("Sample CSV created at data/color_combinations.csv")

if __name__ == "__main__":
    # Check if CSV exists, if not create sample
    if not os.path.exists('data/color_combinations.csv'):
        print("CSV file not found, creating sample...")
        create_sample_csv()
    
    # Generate color variants
    generate_color_variants()