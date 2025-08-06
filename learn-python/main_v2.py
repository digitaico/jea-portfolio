#!/usr/bin/env python3
"""
Main Script v2 - Database Integration (Stage 3+)
================================================

This is version 2 of the main script that adds database integration
to the original image transformation functionality.

Version History:
- v1: Basic image transformations (Stage 1) - standalone, no database
- v2: Database integration (Stage 3+) - stores transformation history

Features:
- All original image transformations from v1
- Database storage of transformation history
- Progress tracking and logging
- Error handling and validation

Usage:
    python3 main_v2.py [image_path]
    
Examples:
    python3 main_v2.py /path/to/image.jpg
    python3 main_v2.py  # Will prompt for image path
"""

import warnings
import sys
import os
import time
from pathlib import Path

# Import from previous stages
from image_transformer import ImageColorTransformer
from database import db_manager, TransformationHistory
from config import settings, ensure_directories


def ensure_output_directory():
    """Create output directory if it doesn't exist."""
    output_dir = settings.output_dir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    return output_dir


def save_transformation_to_db(image_path: str, transformation_type: str, 
                            output_path: str, parameters: dict = None, 
                            processing_time: int = None) -> bool:
    """Save transformation to database."""
    try:
        transformation = db_manager.save_transformation(
            image_path=image_path,
            transformation_type=transformation_type,
            parameters=parameters or {},
            output_path=output_path,
            processing_time=processing_time
        )
        
        if transformation:
            print(f"✅ Transformation saved to database (ID: {transformation.id})")
            return True
        else:
            print("⚠️  Failed to save transformation to database")
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def apply_transformation_with_db(transformer: ImageColorTransformer, 
                               transformation_type: str, 
                               output_filename: str,
                               parameters: dict = None):
    """Apply transformation and save to database."""
    start_time = time.time()
    
    try:
        # Apply transformation based on type
        if transformation_type == "brightness":
            factor = parameters.get("factor", 1.3) if parameters else 1.3
            transformer.adjust_brightness(factor)
        elif transformation_type == "contrast":
            factor = parameters.get("factor", 1.5) if parameters else 1.5
            transformer.adjust_contrast(factor)
        elif transformation_type == "sepia":
            transformer.apply_sepia()
        elif transformation_type == "grayscale":
            transformer.to_grayscale()
        elif transformation_type == "invert":
            transformer.invert_colors()
        elif transformation_type == "gaussian_blur":
            kernel_size = parameters.get("kernel_size", 5) if parameters else 5
            transformer.apply_gaussian_blur(kernel_size)
        elif transformation_type == "gaussian_blur_pillow":
            radius = parameters.get("radius", 2.0) if parameters else 2.0
            transformer.apply_gaussian_blur_pillow(radius)
        elif transformation_type == "saturation_pillow":
            factor = parameters.get("factor", 1.5) if parameters else 1.5
            transformer.adjust_saturation_pillow(factor)
        else:
            raise ValueError(f"Unknown transformation type: {transformation_type}")
        
        # Save transformed image
        output_path = os.path.join(settings.output_dir, output_filename)
        transformer.save_image(output_path)
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
        
        # Save to database
        success = save_transformation_to_db(
            image_path=transformer.image_path,
            transformation_type=transformation_type,
            output_path=output_path,
            parameters=parameters,
            processing_time=processing_time
        )
        
        if success:
            print(f"✅ {transformation_type} completed in {processing_time}ms")
        else:
            print(f"⚠️  {transformation_type} completed but not saved to database")
        
        return success
        
    except Exception as e:
        print(f"❌ Error applying {transformation_type}: {e}")
        return False


def main():
    """Main function with database integration (v2)."""
    try:
        print("=== Image Color Transformer v2 - Database Integration ===")
        print(f"Version: 2.0 (Database Integration)")
        print(f"Stage: 3+ (Database Integration)")
        print(f"Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")
        print(f"Schema: image_processor")
        
        # Ensure directories exist
        ensure_directories()
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
        
        # Check if image is loaded properly (fix for NumPy array truthiness)
        if transformer.image is None:
            print("❌ No valid image loaded. Exiting.")
            return
        
        print(f"✅ Image loaded: {transformer.image_path}")
        print(f"Image size: {transformer.image.shape if hasattr(transformer.image, 'shape') else 'Unknown'}")
        
        # Apply transformations and store in database (same as v1 but with DB storage)
        print("\n=== Applying transformations and storing in database ===")
        
        # Brightness adjustment
        print("1. Applying brightness adjustment...")
        success1 = apply_transformation_with_db(
            transformer, "brightness", "output_bright.jpg", {"factor": 1.3}
        )
        
        # Contrast adjustment
        print("2. Applying contrast adjustment...")
        transformer.reset()
        success2 = apply_transformation_with_db(
            transformer, "contrast", "output_contrast.jpg", {"factor": 1.5}
        )
        
        # Sepia filter
        print("3. Applying sepia filter...")
        transformer.reset()
        success3 = apply_transformation_with_db(
            transformer, "sepia", "output_sepia.jpg", {}
        )
        
        # Grayscale
        print("4. Converting to grayscale...")
        transformer.reset()
        success4 = apply_transformation_with_db(
            transformer, "grayscale", "output_grayscale.jpg", {}
        )
        
        # Invert colors
        print("5. Inverting colors...")
        transformer.reset()
        success5 = apply_transformation_with_db(
            transformer, "invert", "output_inverted.jpg", {}
        )
        
        # Gaussian blur
        print("6. Applying Gaussian blur (5x5 kernel)...")
        transformer.reset()
        success6 = apply_transformation_with_db(
            transformer, "gaussian_blur", "output_gaussian_blur.jpg", {"kernel_size": 5}
        )
        
        # Pillow methods demonstration
        print("\n=== Pillow Methods Demo (with DB storage) ===")
        
        # Pillow brightness adjustment
        print("7. Applying Pillow brightness adjustment...")
        transformer.reset()
        success7 = apply_transformation_with_db(
            transformer, "brightness", "output_pillow_bright.jpg", {"factor": 1.4}
        )
        
        # Pillow saturation adjustment
        print("8. Applying Pillow saturation adjustment...")
        transformer.reset()
        success8 = apply_transformation_with_db(
            transformer, "saturation_pillow", "output_pillow_saturated.jpg", {"factor": 1.6}
        )
        
        # Pillow Gaussian blur
        print("9. Applying Pillow Gaussian blur...")
        transformer.reset()
        success9 = apply_transformation_with_db(
            transformer, "gaussian_blur_pillow", "output_pillow_blur.jpg", {"radius": 3.0}
        )
        
        # Summary
        successful_transformations = sum([success1, success2, success3, success4, success5, success6, success7, success8, success9])
        total_transformations = 9
        
        print(f"\n=== Transformation Summary (v2) ===")
        print(f"✅ Successful transformations: {successful_transformations}/{total_transformations}")
        print(f"📁 Output directory: {output_dir}")
        print(f"🗄️  Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")
        print(f"📊 Schema: image_processor")
        
        # Show recent transformations from database
        print(f"\n=== Recent Database Entries ===")
        try:
            recent_transformations = db_manager.get_transformation_history(limit=5)
            if recent_transformations:
                for transformation in recent_transformations:
                    print(f"  ID: {transformation.id} | Type: {transformation.transformation_type} | Time: {transformation.processing_time}ms")
            else:
                print("  No transformations found in database")
        except Exception as e:
            print(f"  ⚠️  Could not retrieve database entries: {e}")
        
    except Exception as e:
        print(f"❌ Error in main v2: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 