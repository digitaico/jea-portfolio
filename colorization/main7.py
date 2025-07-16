import cv2
import numpy as np
import pandas as pd
import os

def hex_to_bgr(hex_color: str) -> tuple[int, int, int]:
    """
    Converts a hexadecimal color string (e.g., '#RRGGBB') to a BGR tuple.
    Returns (B, G, R) where each component is 0-255.
    """
    hex_color = hex_color.lstrip('#')
    if not all(c in '0123456789abcdefABCDEF' for c in hex_color) or len(hex_color) != 6:
        raise ValueError(f"Invalid hex color format: {hex_color}. Expected '#RRGGBB'.")
    return tuple(int(hex_color[i:i+2], 16) for i in (4, 2, 0)) # BGR

def colorize_region_alternative(original_image_bgr: np.ndarray, region_mask_3ch: np.ndarray, target_hex_color: str, alternative_mode: int = 3) -> np.ndarray:
    """
    Applies a target color to a specific region of an image based on the chosen alternative mode.

    Args:
        original_image_bgr (np.ndarray): The original BGR image (template_img).
        region_mask_3ch (np.ndarray): The 3-channel binary mask for the region to colorize.
        target_hex_color (str): The hexadecimal color string (e.g., '#RRGGBB').
        alternative_mode (int):
            1: HSV with Saturation/Value boost
            2: Weighted Blending (Grayscale + Solid Color)
            3: Lab with L-Channel Enhancement (default)

    Returns:
        np.ndarray: The colorized region as a BGR image.
    """
    if original_image_bgr is None:
        raise ValueError("Original BGR image cannot be None for colorization.")
    if region_mask_3ch is None:
        raise ValueError("Region mask cannot be None for colorization.")

    target_bgr = hex_to_bgr(target_hex_color)
    
    # Initialize the colorized section with zeros
    colorized_section = np.zeros_like(original_image_bgr, dtype=np.uint8)

    # --- Alternative 1: HSV with Saturation/Value Boost ---
    if alternative_mode == 1:
        # Convert original image to HSV
        original_hsv = cv2.cvtColor(original_image_bgr, cv2.COLOR_BGR2HSV)
        H_orig, S_orig, V_orig = cv2.split(original_hsv)

        # Convert target color to HSV
        target_hsv_single_pixel = cv2.cvtColor(np.array([[target_bgr]], dtype=np.uint8), cv2.COLOR_BGR2HSV)
        H_target, S_target, V_target = cv2.split(target_hsv_single_pixel)

        # Use original V (luminosity), but new H and S
        # Optional: Boost saturation and/or value
        SAT_BOOST_FACTOR = 1.2 # Adjust this (e.g., 1.0 for no change, >1.0 for more saturation)
        VALUE_OFFSET = 0    # Adjust this (e.g., 0 for no change, >0 for brighter)

        S_new = np.full_like(S_orig, S_target[0,0] * SAT_BOOST_FACTOR, dtype=np.float32)
        S_new = np.clip(S_new, 0, 255).astype(np.uint8) # Ensure values are within range

        # Use original V, but apply offset for brightness
        V_new = np.clip(V_orig + VALUE_OFFSET, 0, 255).astype(np.uint8)
        
        # Merge new H, S, V
        combined_hsv = cv2.merge([np.full_like(H_orig, H_target[0,0], dtype=np.uint8), S_new, V_new])
        colorized_result_bgr = cv2.cvtColor(combined_hsv, cv2.COLOR_HSV2BGR)
        colorized_section = cv2.bitwise_and(colorized_result_bgr, region_mask_3ch)

    # --- Alternative 2: Weighted Blending (Grayscale + Solid Color) ---
    elif alternative_mode == 2:
        # Get grayscale version of original image (3 channels)
        original_gray_3ch = cv2.cvtColor(cv2.cvtColor(original_image_bgr, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
        
        # Create a solid color image with the target BGR
        solid_color_img = np.full_like(original_image_bgr, target_bgr, dtype=np.uint8)

        # Blending factor: Adjust this for desired intensity
        BLEND_ALPHA = 0.5 # 0.0 (more original) to 1.0 (more new color)
        
        # Blend the solid color with the grayscale image
        blended_result = cv2.addWeighted(original_gray_3ch, 1.0 - BLEND_ALPHA, solid_color_img, BLEND_ALPHA, 0)
        
        colorized_section = cv2.bitwise_and(blended_result, region_mask_3ch)

    # --- Alternative 3: Lab with L-Channel Enhancement ---
    else: # Default or if alternative_mode == 3
        original_lab = cv2.cvtColor(original_image_bgr, cv2.COLOR_BGR2Lab)
        L_orig, a_orig, b_orig = cv2.split(original_lab)

        target_color_lab_single_pixel = cv2.cvtColor(np.array([[target_bgr]], dtype=np.uint8), cv2.COLOR_BGR2Lab)
        _, a_target, b_target = cv2.split(target_color_lab_single_pixel)

        # Create new 'a' and 'b' channels of the full image size
        a_new = np.full_like(a_orig, a_target[0,0], dtype=np.uint8)
        b_new = np.full_like(b_orig, b_target[0,0], dtype=np.uint8)

        # --- Enhancement to L_orig (Optional, adjust carefully) ---
        # You can try simple scaling and offset, or more complex operations
        # L_orig_enhanced = cv2.equalizeHist(L_orig) # Example: Histogram equalization
        # L_orig_enhanced = np.clip(L_orig * 1.1 + 10, 0, 255).astype(np.uint8) # Example: Brightness/Contrast
        L_orig_enhanced = L_orig # Default: No enhancement (original behavior)

        combined_lab = cv2.merge([L_orig_enhanced, a_new, b_new])
        colorized_result_bgr = cv2.cvtColor(combined_lab, cv2.COLOR_Lab2BGR)
        colorized_section = cv2.bitwise_and(colorized_result_bgr, region_mask_3ch)

    return colorized_section


def colorize_image_with_masks_mvp(template_path: str, body_mask_path: str, pockets_mask_path: str, webbings_mask_path: str, output_dir: str, color_combinations_df: pd.DataFrame, current_alternative_mode: int = 3):
    """
    Colorizes an image using provided masks and color combinations,
    applying colors based on the chosen alternative mode.

    Args:
        template_path (str): Path to the template image.
        body_mask_path (str): Path to the body mask image.
        pockets_mask_path (str): Path to the pockets mask image.
        webbings_mask_path (str): Path to the webbings mask image.
        output_dir (str): Directory to save the output images.
        color_combinations_df (pd.DataFrame): DataFrame containing color combinations.
        current_alternative_mode (int): The alternative mode to use for colorization (1, 2, or 3).
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    template_img = cv2.imread(template_path)
    if template_img is None:
        print(f"Error: Could not load template image at {template_path}")
        return

    body_mask = cv2.imread(body_mask_path, cv2.IMREAD_GRAYSCALE)
    pockets_mask = cv2.imread(pockets_mask_path, cv2.IMREAD_GRAYSCALE)
    webbings_mask = cv2.imread(webbings_mask_path, cv2.IMREAD_GRAYSCALE)

    if any(m is None for m in [body_mask, pockets_mask, webbings_mask]):
        print("Error: One or more masks could not be loaded. Please check paths.")
        return

    _, body_mask = cv2.threshold(body_mask, 128, 255, cv2.THRESH_BINARY)
    _, pockets_mask = cv2.threshold(pockets_mask, 128, 255, cv2.THRESH_BINARY)
    _, webbings_mask = cv2.threshold(webbings_mask, 128, 255, cv2.THRESH_BINARY)

    body_mask_3ch = cv2.cvtColor(body_mask, cv2.COLOR_GRAY2BGR)
    pockets_mask_3ch = cv2.cvtColor(pockets_mask, cv2.COLOR_GRAY2BGR)
    webbings_mask_3ch = cv2.cvtColor(webbings_mask, cv2.COLOR_GRAY2BGR)

    apparel_mask_raw = cv2.bitwise_or(body_mask, pockets_mask)
    apparel_mask_raw = cv2.bitwise_or(apparel_mask_raw, webbings_mask)
    _, apparel_mask_binary = cv2.threshold(apparel_mask_raw, 1, 255, cv2.THRESH_BINARY)
    apparel_mask_3ch = cv2.cvtColor(apparel_mask_binary, cv2.COLOR_GRAY2BGR)
    background_mask_3ch = cv2.bitwise_not(apparel_mask_3ch)

    original_webbings = cv2.bitwise_and(template_img, webbings_mask_3ch)


    for index, row in color_combinations_df.iterrows():
        filename = row['filename']
        body_color_hex = row['body_color']
        pockets_color_hex = row['pockets_color']

        # Call the new colorize_region_alternative function
        body_section = colorize_region_alternative(template_img, body_mask_3ch, body_color_hex, current_alternative_mode)
        pockets_section = colorize_region_alternative(template_img, pockets_mask_3ch, pockets_color_hex, current_alternative_mode)

        # --- Combine All Layers into Final Image ---
        output_img = np.full_like(template_img, (255, 255, 255), dtype=np.uint8)
        output_img = cv2.bitwise_and(output_img, background_mask_3ch)
        
        apparel_composite = np.zeros_like(template_img, dtype=np.uint8)
        apparel_composite = cv2.add(apparel_composite, body_section)
        apparel_composite = cv2.add(apparel_composite, pockets_section)
        apparel_composite = cv2.add(apparel_composite, original_webbings)

        final_image = cv2.add(output_img, apparel_composite)

        output_path = os.path.join(output_dir, filename)
        cv2.imwrite(output_path, final_image)
        print(f"Generated: {output_path} using Alternative {current_alternative_mode}")

# --- Main Execution Block ---
if __name__ == "__main__":
    assets_dir = 'assets'
    data_dir = 'data'
    output_dir = 'output_images_mvp'

    template_file = os.path.join(assets_dir, 'template.jpg')
    body_mask_file = os.path.join(assets_dir, 'body_mask.png')
    pockets_mask_file = os.path.join(assets_dir, 'pockets_mask.png')
    webbings_mask_file = os.path.join(assets_dir, 'webbings_mask.png')
    color_combinations_file = os.path.join(data_dir, 'color_combinations.csv')

    try:
        color_df = pd.read_csv(color_combinations_file)
        required_cols = ['filename', 'body_color', 'pockets_color']
        if not all(col in color_df.columns for col in required_cols):
            print(f"Error: CSV is missing required columns. Expected: {required_cols}")
            exit()
    except (FileNotFoundError, Exception) as e:
        print(f"Error loading color combinations CSV: {e}")
        exit()

    # --- CHOOSE YOUR ALTERNATIVE HERE ---
    # Uncomment ONE of the following lines to test a specific alternative:
    current_alternative_to_test = 3 # Default to the refined Lab (Alternative 3)

    # current_alternative_to_test = 1 # Test HSV with Saturation/Value Boost
    # current_alternative_to_test = 2 # Test Weighted Blending (Grayscale + Solid Color)
    # current_alternative_to_test = 3 # Test Lab with L-Channel Enhancement

    print(f"Running MVP script with Alternative {current_alternative_to_test}...")
    colorize_image_with_masks_mvp(
        template_file,
        body_mask_file,
        pockets_mask_file,
        webbings_mask_file,
        output_dir,
        color_df,
        current_alternative_to_test
    )
    print("MVP script execution complete. Check the 'output_images_mvp' directory.")