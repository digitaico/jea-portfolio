from image_transformer import ImageColorTransformer
import warnings
import sys
import os


def ensure_output_directory():
    """Create output directory if it doesn't exist."""
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    return output_dir


def main():
    try:
        print("=== Image Color Transformer ===")
        
        # Ensure output directory exists
        output_dir = ensure_output_directory()
        
        # Check if image source is provided as command line argument
        image_source = None
        if len(sys.argv) > 1:
            image_source = sys.argv[1]
            print(f"Using image source: {image_source}")
        else:
            print("No image source provided. Will prompt for input.")
        
        # Create transformer instance
        transformer = ImageColorTransformer(image_source)
        
        # Apply some transformations and store them
        print("\n=== Applying transformations and storing images ===")
        
        # Brightness adjustment
        print("1. Applying brightness adjustment...")
        transformer.adjust_brightness(1.3)
        transformer.store_image("bright")
        transformer.save_image(os.path.join(output_dir, "output_bright.jpg"))
        
        # Contrast adjustment
        print("2. Applying contrast adjustment...")
        transformer.reset()
        transformer.adjust_contrast(1.5)
        transformer.store_image("contrast")
        transformer.save_image(os.path.join(output_dir, "output_contrast.jpg"))
        
        # Sepia filter
        print("3. Applying sepia filter...")
        transformer.reset()
        transformer.apply_sepia()
        transformer.store_image("sepia")
        transformer.save_image(os.path.join(output_dir, "output_sepia.jpg"))
        
        # Grayscale
        print("4. Converting to grayscale...")
        transformer.reset()
        transformer.to_grayscale()
        transformer.store_image("grayscale")
        transformer.save_image(os.path.join(output_dir, "output_grayscale.jpg"))
        
        # Invert colors
        print("5. Inverting colors...")
        transformer.reset()
        transformer.invert_colors()
        transformer.store_image("inverted")
        transformer.save_image(os.path.join(output_dir, "output_inverted.jpg"))
        
        # Gaussian blur
        print("6. Applying Gaussian blur (5x5 kernel)...")
        transformer.reset()
        transformer.apply_gaussian_blur(5)
        transformer.store_image("gaussian_blur")
        transformer.save_image(os.path.join(output_dir, "output_gaussian_blur.jpg"))
        
        # Pillow methods demonstration
        print("\n=== Pillow Methods Demo ===")
        
        # Pillow brightness adjustment
        print("7. Applying Pillow brightness adjustment...")
        transformer.reset()
        transformer.adjust_brightness_pillow(1.4)
        transformer.store_image("pillow_bright")
        transformer.save_image(os.path.join(output_dir, "output_pillow_bright.jpg"))
        
        # Pillow saturation adjustment
        print("8. Applying Pillow saturation adjustment...")
        transformer.reset()
        transformer.adjust_saturation_pillow(1.6)
        transformer.store_image("pillow_saturated")
        transformer.save_image(os.path.join(output_dir, "output_pillow_saturated.jpg"))
        
        # Pillow Gaussian blur
        print("9. Applying Pillow Gaussian blur...")
        transformer.reset()
        transformer.apply_gaussian_blur_pillow(3.0)
        transformer.store_image("pillow_blur")
        transformer.save_image(os.path.join(output_dir, "output_pillow_blur.jpg"))
        
        # Pillow unsharp mask (sharpening)
        print("10. Applying Pillow unsharp mask (sharpening)...")
        transformer.reset()
        transformer.apply_unsharp_mask_pillow(radius=2.0, percent=200, threshold=3)
        transformer.store_image("pillow_sharp")
        transformer.save_image(os.path.join(output_dir, "output_pillow_sharp.jpg"))
        
        # Pillow emboss effect
        print("11. Applying Pillow emboss effect...")
        transformer.reset()
        transformer.apply_emboss_pillow()
        transformer.store_image("pillow_emboss")
        transformer.save_image(os.path.join(output_dir, "output_pillow_emboss.jpg"))
        
        # Pillow edge detection
        print("12. Applying Pillow edge detection...")
        transformer.reset()
        transformer.apply_find_edges_pillow()
        transformer.store_image("pillow_edges")
        transformer.save_image(os.path.join(output_dir, "output_pillow_edges.jpg"))
        
        # Demonstrate stored images functionality
        print("\n=== Stored Images Demo ===")
        stored_images = transformer.list_stored_images()
        print(f"Stored images: {stored_images}")
        
        # Load and save a stored image
        if "sepia" in stored_images:
            print("Loading stored sepia image...")
            transformer.load_stored_image("sepia")
            transformer.save_image(os.path.join(output_dir, "output_stored_sepia.jpg"))
            print("Stored sepia image loaded and saved!")
        
        # Remove a stored image
        if "inverted" in stored_images:
            print("Removing stored inverted image...")
            transformer.remove_stored_image("inverted")
            remaining_images = transformer.list_stored_images()
            print(f"Remaining stored images: {remaining_images}")
        
        print(f"\nAll transformations completed! Check the {output_dir}/ directory for output files.")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    # Configure warnings to show
    warnings.filterwarnings("always")
    main() 