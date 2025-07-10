import cv2
import numpy as np
import pandas as pd
import os

def hex_to_bgr(hex_color):
    """Converts a hexadecimal color string (e.g., '#RRGGBB') to a BGR tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (4, 2, 0)) # BGR

def colorize_image_with_masks(template_path, body_mask_path, pockets_mask_path, webbings_mask_path, output_dir, color_combinations_df):
    """
    Colorizes an image using provided masks and color combinations.

    Args:
        template_path (str): Path to the template image (e.g., 'assets/template.jpg').
        body_mask_path (str): Path to the body mask image (e.g., 'assets/body_mask.png').
        pockets_mask_path (str): Path to the pockets mask image (e.g., 'assets/pockets_mask.png').
        webbings_mask_path (str): Path to the webbings mask image (e.g., 'assets/webbings_mask.png').
        output_dir (str): Directory to save the output images.
        color_combinations_df (pd.DataFrame): DataFrame containing color combinations.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load the template image
    template_img = cv2.imread(template_path)
    if template_img is None:
        print(f"Error: Could not load template image at {template_path}")
        return

    # Load masks
    body_mask = cv2.imread(body_mask_path, cv2.IMREAD_GRAYSCALE)
    pockets_mask = cv2.imread(pockets_mask_path, cv2.IMREAD_GRAYSCALE)
    webbings_mask = cv2.imread(webbings_mask_path, cv2.IMREAD_GRAYSCALE)

    if body_mask is None or pockets_mask is None or webbings_mask is None:
        print("Error: One or more masks could not be loaded. Please check paths.")
        return

    # Ensure masks are binary (0 or 255)
    _, body_mask = cv2.threshold(body_mask, 128, 255, cv2.THRESH_BINARY)
    _, pockets_mask = cv2.threshold(pockets_mask, 128, 255, cv2.THRESH_BINARY)
    _, webbings_mask = cv2.threshold(webbings_mask, 128, 255, cv2.THRESH_BINARY)

    # Convert masks to 3 channels for element-wise multiplication with color images
    body_mask_3ch = cv2.cvtColor(body_mask, cv2.COLOR_GRAY2BGR)
    pockets_mask_3ch = cv2.cvtColor(pockets_mask, cv2.COLOR_GRAY2BGR)
    webbings_mask_3ch = cv2.cvtColor(webbings_mask, cv2.COLOR_GRAY2BGR)

    # Invert masks to get the background and other areas not to be touched by the specific mask
    # For example, body_mask_inv will be white where the body is NOT, and black where it IS.
    body_mask_inv = cv2.bitwise_not(body_mask_3ch)
    pockets_mask_inv = cv2.bitwise_not(pockets_mask_3ch)
    webbings_mask_inv = cv2.bitwise_not(webbings_mask_3ch)

    # Create a grayscale version of the template for intensity (shadows, wrinkles)
    template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
    template_gray_3ch = cv2.cvtColor(template_gray, cv2.COLOR_GRAY2BGR)

    # Determine the area that is the apparel (union of all masks)
    apparel_mask = cv2.bitwise_or(body_mask, pockets_mask)
    apparel_mask = cv2.bitwise_or(apparel_mask, webbings_mask)
    _, apparel_mask = cv2.threshold(apparel_mask, 1, 255, cv2.THRESH_BINARY) # Ensure it's binary
    apparel_mask_3ch = cv2.cvtColor(apparel_mask, cv2.COLOR_GRAY2BGR)
    background_mask_3ch = cv2.bitwise_not(apparel_mask_3ch)

    # Extract the original webbings
    original_webbings = cv2.bitwise_and(template_img, webbings_mask_3ch)

    for index, row in color_combinations_df.iterrows():
        filename = row['filename']
        body_color_hex = row['body_color']
        pockets_color_hex = row['pockets_color']

        body_bgr = hex_to_bgr(body_color_hex)
        pockets_bgr = hex_to_bgr(pockets_color_hex)

        # Create color images for blending
        body_color_img = np.full_like(template_img, body_bgr, dtype=np.uint8)
        pockets_color_img = np.full_like(template_img, pockets_bgr, dtype=np.uint8)

        # Apply body color preserving intensity
        # Convert template_gray_3ch to float for multiplication, then back to uint8
        body_colored = (template_gray_3ch * (np.array(body_bgr) / 255.0)).astype(np.uint8)
        body_section = cv2.bitwise_and(body_colored, body_mask_3ch)

        # Apply pockets color preserving intensity
        pockets_colored = (template_gray_3ch * (np.array(pockets_bgr) / 255.0)).astype(np.uint8)
        pockets_section = cv2.bitwise_and(pockets_colored, pockets_mask_3ch)

        # Start with a white background for the output image
        output_img = np.full_like(template_img, (255, 255, 255), dtype=np.uint8)

        # Overlay the apparel sections onto the white background
        # First, add the original white background where the apparel is not
        output_img = cv2.bitwise_and(output_img, background_mask_3ch)
        
        # Now, add the colored body and pockets
        # Create a blank canvas to build up the apparel
        apparel_composite = np.zeros_like(template_img, dtype=np.uint8)
        apparel_composite = cv2.add(apparel_composite, body_section)
        apparel_composite = cv2.add(apparel_composite, pockets_section)
        
        # Add the original webbings
        apparel_composite = cv2.add(apparel_composite, original_webbings)

        # Combine the white background with the apparel composite
        output_img = cv2.add(output_img, apparel_composite)


        output_path = os.path.join(output_dir, filename)
        cv2.imwrite(output_path, output_img)
        print(f"Generated: {output_path}")

# --- How to use the script ---
if __name__ == "__main__":
    # Define asset paths
    assets_dir = 'assets'
    data_dir = 'data'
    output_dir = 'output_images' # Directory where the results will be saved

    template_file = os.path.join(assets_dir, 'template.jpg')
    body_mask_file = os.path.join(assets_dir, 'body_mask.png')
    pockets_mask_file = os.path.join(assets_dir, 'pockets_mask.png')
    webbings_mask_file = os.path.join(assets_dir, 'webbings_mask.png')
    color_combinations_file = os.path.join(data_dir, 'color_combinations.csv')

    # Load color combinations
    try:
        color_df = pd.read_csv(color_combinations_file)
    except FileNotFoundError:
        print(f"Error: color_combinations.csv not found at {color_combinations_file}")
        exit()

    # Run the colorization process
    colorize_image_with_masks(
        template_file,
        body_mask_file,
        pockets_mask_file,
        webbings_mask_file,
        output_dir,
        color_df
    )