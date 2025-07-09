import cv2
import numpy as np
import os
import json
import csv

def hex_to_bgr(hex_color):
    """Converts a hexadecimal color string to a BGR tuple.
    Includes basic validation for hex color format."""
    
    if not isinstance(hex_color, str) or not hex_color.startswith('#'):
        print(f"Warning: Invalid hex color format '{hex_color}'. Expected string starting with '#'. Using default white.")
        return (255, 255, 255) # Default to white BGR
    
    hex_color = hex_color.lstrip('#')
    
    if len(hex_color) == 3: # Handle shorthand hex like #RGB
        hex_color = ''.join([c*2 for c in hex_color])
    elif len(hex_color) != 6:
        print(f"Warning: Invalid hex color length '{hex_color}'. Expected 3 or 6 characters after '#'. Using default white.")
        return (255, 255, 255) # Default to white BGR

    try:
        rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        return (rgb[2], rgb[1], rgb[0]) # Convert RGB to BGR
    except ValueError:
        print(f"Warning: Could not parse hex color value '{hex_color}'. Using default white.")
        return (255, 255, 255) # Default to white BGR

def bgr_to_hex(bgr_tuple):
    """Converts a BGR tuple (B,G,R) back to hexadecimal string '#RRGGBB'."""
    if not isinstance(bgr_tuple, (tuple, list)) or len(bgr_tuple) != 3:
        return "#000000"
    r, g, b = int(bgr_tuple[2]), int(bgr_tuple[1]), int(bgr_tuple[0])
    return f"#{r:02x}{g:02x}{b:02x}"

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
        mask_body_raw = cv2.resize(mask_body_raw, (img_width, img_height))
    mask_body = cv2.threshold(mask_body_raw, 128, 255, cv2.THRESH_BINARY)[1]

    # --- Load and validate Pockets Mask ---
    mask_pockets_raw = cv2.imread(pockets_mask_path, cv2.IMREAD_GRAYSCALE)
    if mask_pockets_raw is None:
        print(f"Error: Pockets mask not found! Check path: '{pockets_mask_path}'")
        return
    if mask_pockets_raw.shape[:2] != (img_height, img_width):
        print(f"Warning: Pockets mask dimensions ({mask_pockets_raw.shape[:2]}) do not match image dimensions ({img.shape[:2]}). Resizing...")
        mask_pockets_raw = cv2.resize(mask_pockets_raw, (img_width, img_height))
    mask_pockets = cv2.threshold(mask_pockets_raw, 128, 255, cv2.THRESH_BINARY)[1]

    # --- Load and validate Webbing Mask ---
    mask_webbing_raw = cv2.imread(webbing_mask_path, cv2.IMREAD_GRAYSCALE)
    if mask_webbing_raw is None:
        print(f"Error: Webbing mask not found! Check path: '{webbing_mask_path}'")
        return
    if mask_webbing_raw.shape[:2] != (img_height, img_width):
        print(f"Warning: Webbing mask dimensions ({mask_webbing_raw.shape[:2]}) do not match image dimensions ({img.shape[:2]}). Resizing...")
        mask_webbing_raw = cv2.resize(mask_webbing_raw, (img_width, img_height))
    mask_webbing = cv2.threshold(mask_webbing_raw, 128, 255, cv2.THRESH_BINARY)[1]

    # Convert original image to LAB for easier color manipulation while preserving lightness
    lab_img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_orig, a_orig, b_orig = cv2.split(lab_img)

    # Apply colors
    # Body
    body_color_lab = cv2.cvtColor(np.array([[body_bgr]], dtype=np.uint8), cv2.COLOR_BGR2LAB)[0][0]
    a_orig[mask_body == 255] = body_color_lab[1] # Apply 'a' channel
    b_orig[mask_body == 255] = body_color_lab[2] # Apply 'b' channel

    # Pockets (Overlay) - Webbing is *not* included here to preserve its original color
    overlay_color_lab = cv2.cvtColor(np.array([[over_bgr]], dtype=np.uint8), cv2.COLOR_BGR2LAB)[0][0]
    
    # Use only pockets mask for overlay color application
    mask_overlay = mask_pockets 

    # Adjust chroma (a,b) channels
    a_orig[mask_overlay == 255] = overlay_color_lab[1]
    b_orig[mask_overlay == 255] = overlay_color_lab[2]

    # OPTIONAL: adjust L channel so that pocket region matches brightness of overlay colour while keeping texture
    overlay_l = int(overlay_color_lab[0])
    pocket_l_pixels = l_orig[mask_overlay == 255]
    if pocket_l_pixels.size > 0:
        mean_l = int(np.mean(pocket_l_pixels))
        if mean_l > 0:
            # Compute scaling factor but keep it within reasonable range
            factor = overlay_l / mean_l
            factor = np.clip(factor, 0.6, 1.4)  # avoid extreme washout/blowout
            adjusted_l = np.clip(pocket_l_pixels.astype(np.float32) * factor, 0, 255).astype(np.uint8)
            l_orig[mask_overlay == 255] = adjusted_l

    # Merge channels back and convert to BGR
    lab_colored = cv2.merge([l_orig, a_orig, b_orig]) # Keep original 'L' (lightness)
    colored_img = cv2.cvtColor(lab_colored, cv2.COLOR_LAB2BGR)

    # (No extra BGR override here). We rely solely on the LAB chroma replacement above, which keeps the
    # original L channel for realistic lighting while injecting the desired colour through a and b.

    # Change background if new_background_bgr is provided
    if new_background_bgr is not None:
        # Create a mask for the background (inverse of all combined foreground masks)
        # Include body, pockets, and webbing in overall foreground to preserve their initial states
        mask_all_foreground = cv2.bitwise_or(mask_body, cv2.bitwise_or(mask_pockets, mask_webbing))
        mask_background = cv2.bitwise_not(mask_all_foreground)
        
        # Create a solid color image for the new background
        background_layer = np.full(img.shape, new_background_bgr, dtype=np.uint8)
        
        # Apply the new background
        final_img = np.where(mask_background[:, :, None] == 255, background_layer, colored_img)
        # Re-apply the original image's webbing areas to the final_img to ensure they keep their raw color
        final_img = np.where(mask_webbing[:, :, None] == 255, img, final_img) 
    else:
        final_img = colored_img
        # If no new background, still restore original webbing color
        final_img = np.where(mask_webbing[:, :, None] == 255, img, final_img) 


    # Debug mode to show masks and intermediate steps
    if debug_mode:
        window_width = 800 
        window_height = 600 

        cv2.namedWindow("Original Image", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Original Image", window_width, window_height)
        cv2.imshow("Original Image", img)

        cv2.namedWindow("Body Mask", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Body Mask", window_width, window_height)
        cv2.imshow("Body Mask", mask_body)
        print(f"DEBUG: Sum of Body Mask pixels (255=white): {np.sum(mask_body)}")


        cv2.namedWindow("Pockets Mask", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Pockets Mask", window_width, window_height)
        cv2.imshow("Pockets Mask", mask_pockets)
        print(f"DEBUG: Sum of Pockets Mask pixels (255=white): {np.sum(mask_pockets)}")


        cv2.namedWindow("Webbing Mask", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Webbing Mask", window_width, window_height)
        cv2.imshow("Webbing Mask", mask_webbing)
        print(f"DEBUG: Sum of Webbing Mask pixels (255=white): {np.sum(mask_webbing)}")


        cv2.namedWindow("Overlay Mask (Pockets Only)", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Overlay Mask (Pockets Only)", window_width, window_height)
        cv2.imshow("Overlay Mask (Pockets Only)", mask_overlay)
        print(f"DEBUG: Sum of Overlay Mask (Pockets Only) pixels (255=white): {np.sum(mask_overlay)}")


        cv2.namedWindow("Colored Image (LAB Chroma Modified)", cv2.WINDOW_NORMAL) # Updated name
        cv2.resizeWindow("Colored Image (LAB Chroma Modified)", window_width, window_height) # Updated name
        cv2.imshow("Colored Image (LAB Chroma Modified)", colored_img) # Updated name

        if new_background_bgr is not None:
            cv2.namedWindow("Final Image with New Background and Original Webbing", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Final Image with New Background and Original Webbing", window_width, window_height)
            cv2.imshow("Final Image with New Background and Original Webbing", final_img)
        else:
            cv2.namedWindow("Final Image with Original Webbing", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Final Image with Original Webbing", window_width, window_height)
            cv2.imshow("Final Image with Original Webbing", final_img)

        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # Save the output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, final_img)
    print(f"Generated {output_path}")
    return final_img


if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    
    # IMPORTANT: Resource locations are based on the script provided by the user in the previous turn.
    input_image_template = os.path.join(script_dir, 'assets', 'template.jpg')
    body_mask_image = os.path.join(script_dir, 'assets', 'body_mask.png') # Note: User uploaded body_mask.jpg, but script expects .png. Ensure consistency.
    pockets_mask_image = os.path.join(script_dir, 'assets', 'pockets_mask.png')
    webbing_mask_image = os.path.join(script_dir, 'assets', 'webbing_mask.png')

    # CSV with color combinations
    csv_file_path = os.path.join(script_dir, 'data', 'color_combinations.csv')

    # Output directory
    output_folder = os.path.join(script_dir, 'output')
    os.makedirs(output_folder, exist_ok=True)

    # Load color combinations
    try:
        with open(csv_file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            color_combinations = list(reader)
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file_path}' not found. Please make sure it exists.")
        exit(1)
    except Exception as e:
        print(f"Error reading CSV file '{csv_file_path}': {e}")
        exit(1)

    print(f"Loaded {len(color_combinations)} color combinations from '{csv_file_path}'.")
    print(f"--- Starting batch generation using template '{input_image_template}' ---")

    for combo in color_combinations:
        source_filename = combo.get('file', '').strip()
        if not source_filename:
            print("Warning: Missing 'file' column in CSV row. Skipping.")
            continue
        base_name, _ = os.path.splitext(source_filename)

        body_hex = combo.get('body', '#FFFFFF').strip()
        overlay_hex = combo.get('overlay', '#FFFFFF').strip()

        body_bgr = hex_to_bgr(body_hex)
        overlay_bgr = hex_to_bgr(overlay_hex)

        # Audit: show requested vs converted colours
        print("  ↳ Body   requested:", body_hex, "→ applied:", bgr_to_hex(body_bgr))
        print("  ↳ Pockets requested:", overlay_hex, "→ applied:", bgr_to_hex(overlay_bgr))

        output_path_webp = os.path.join(output_folder, f"{base_name}.webp")
        output_path_jpg = os.path.join(output_folder, f"{base_name}.jpg")

        print(f"Generating '{output_path_webp}' and '{output_path_jpg}' with body={body_hex}, overlay={overlay_hex}")

        final_img = change_colors(
            input_image_template,
            body_mask_image,
            pockets_mask_image,
            webbing_mask_image,
            output_path_webp,
            body_bgr,
            overlay_bgr,
            new_background_bgr=None,
            debug_mode=False
        )

        # Save JPEG version
        if final_img is not None:
            cv2.imwrite(output_path_jpg, final_img)
            print(f"Generated {output_path_jpg}")
        else:
            print("Skipping JPEG generation due to earlier errors.")