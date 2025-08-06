#!/usr/bin/env python3
"""
Main Script with Database Integration (Stage 3+)
================================================

This script demonstrates image transformations with database storage.
It integrates the image processing capabilities from Stage 1 with the
database functionality from Stage 3.

Features:
- Image transformations using ImageColorTransformer
- Database storage of transformation history
- Progress tracking and logging
- Error handling and validation

Usage:
    python3 main_with_db.py [image_path]
    
Examples:
    python3 main_with_db.py /path/to/image.jpg
    python3 main_with_db.py  # Will prompt for image path
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
                               parameters: dict = None,
                               **kwargs):
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
        elif transformation_type == "unsharp_mask":
            radius = parameters.get("radius", 2.0) if parameters else 2.0
            percent = parameters.get("percent", 150) if parameters else 150
            threshold = parameters.get("threshold", 3) if parameters else 3
            transformer.apply_unsharp_mask_pillow(radius, percent, threshold)
        elif transformation_type == "emboss":
            transformer.apply_emboss_pillow()
        elif transformation_type == "find_edges":
            transformer.apply_find_edges_pillow()
        elif transformation_type == "contour":
            transformer.apply_contour_pillow()
        elif transformation_type == "rotate":
            angle = parameters.get("angle", 45) if parameters else 45
            expand = parameters.get("expand", True) if parameters else True
            transformer.rotate_pillow(angle, expand)
        elif transformation_type == "resize":
            width = parameters.get("width", 800) if parameters else 800
            height = parameters.get("height", 600) if parameters else 600
            resample = parameters.get("resample", "lanczos") if parameters else "lanczos"
            transformer.resize_pillow(width, height, resample)
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
    """Main function with database integration."""
    try:
        print("=== Image Color Transformer with Database Integration ===")
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
        
        if not transformer.image:
            print("❌ No valid image loaded. Exiting.")
            return
        
        print(f"✅ Image loaded: {transformer.image_path}")
        print(f"Image size: {transformer.image.shape if hasattr(transformer.image, 'shape') else 'Unknown'}")
        
        # Apply transformations and store in database
        print("\n=== Applying transformations and storing in database ===")
        
        transformations = [
            {
                "type": "brightness",
                "filename": "output_bright.jpg",
                "parameters": {"factor": 1.3},
                "description": "Brightness adjustment"
            },
            {
                "type": "contrast",
                "filename": "output_contrast.jpg",
                "parameters": {"factor": 1.5},
                "description": "Contrast enhancement"
            },
            {
                "type": "sepia",
                "filename": "output_sepia.jpg",
                "parameters": {},
                "description": "Sepia filter"
            },
            {
                "type": "grayscale",
                "filename": "output_grayscale.jpg",
                "parameters": {},
                "description": "Grayscale conversion"
            },
            {
                "type": "invert",
                "filename": "output_inverted.jpg",
                "parameters": {},
                "description": "Color inversion"
            },
            {
                "type": "gaussian_blur",
                "filename": "output_gaussian_blur.jpg",
                "parameters": {"kernel_size": 5},
                "description": "Gaussian blur (5x5 kernel)"
            },
            {
                "type": "gaussian_blur_pillow",
                "filename": "output_pillow_blur.jpg",
                "parameters": {"radius": 3.0},
                "description": "Pillow Gaussian blur"
            },
            {
                "type": "saturation_pillow",
                "filename": "output_pillow_saturated.jpg",
                "parameters": {"factor": 1.6},
                "description": "Pillow saturation adjustment"
            },
            {
                "type": "unsharp_mask",
                "filename": "output_unsharp_mask.jpg",
                "parameters": {"radius": 2.0, "percent": 150, "threshold": 3},
                "description": "Unsharp mask"
            },
            {
                "type": "emboss",
                "filename": "output_emboss.jpg",
                "parameters": {},
                "description": "Emboss effect"
            },
            {
                "type": "find_edges",
                "filename": "output_edges.jpg",
                "parameters": {},
                "description": "Edge detection"
            },
            {
                "type": "rotate",
                "filename": "output_rotated.jpg",
                "parameters": {"angle": 45, "expand": True},
                "description": "45-degree rotation"
            },
            {
                "type": "resize",
                "filename": "output_resized.jpg",
                "parameters": {"width": 800, "height": 600, "resample": "lanczos"},
                "description": "Resize to 800x600"
            }
        ]
        
        successful_transformations = 0
        total_transformations = len(transformations)
        
        for i, transformation in enumerate(transformations, 1):
            print(f"\n{i}/{total_transformations}. {transformation['description']}...")
            
            # Reset transformer for each transformation
            transformer.reset()
            
            # Apply transformation
            success = apply_transformation_with_db(
                transformer=transformer,
                transformation_type=transformation["type"],
                output_filename=transformation["filename"],
                parameters=transformation["parameters"]
            )
            
            if success:
                successful_transformations += 1
        
        # Summary
        print(f"\n=== Transformation Summary ===")
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
        print(f"❌ Error in main: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 