#!/usr/bin/env python3
"""
Main Script v3 - Advanced Features (Stage 4+)
=============================================

This is version 3 of the main script that adds advanced features
beyond database integration.

Version History:
- v1: Basic image transformations (Stage 1) - standalone, no database
- v2: Database integration (Stage 3+) - stores transformation history
- v3: Advanced features (Stage 4+) - batch processing, enhanced error handling, more transformations

Features:
- All features from v1 and v2
- Batch processing capabilities
- Enhanced error handling and validation
- More transformation types
- Performance monitoring
- Detailed logging
- Configuration management

Usage:
    python3 main_v3.py [image_path] [--batch] [--config config.json]
    
Examples:
    python3 main_v3.py /path/to/image.jpg
    python3 main_v3.py /path/to/image.jpg --batch
    python3 main_v3.py --config custom_config.json
"""

import warnings
import sys
import os
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

# Import from previous stages
from image_transformer import ImageColorTransformer
from database import db_manager, TransformationHistory
from config import settings, ensure_directories


@dataclass
class TransformationConfig:
    """Configuration for a transformation."""
    type: str
    filename: str
    parameters: Dict[str, Any]
    description: str
    enabled: bool = True


@dataclass
class BatchResult:
    """Result of a batch transformation."""
    transformation_id: str
    type: str
    success: bool
    processing_time: int
    output_path: str
    error_message: Optional[str] = None


class AdvancedImageProcessor:
    """Advanced image processor with batch capabilities and enhanced features."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.transformations = self.load_transformations()
        self.results: List[BatchResult] = []
        self.start_time = time.time()
        
    def load_transformations(self) -> List[TransformationConfig]:
        """Load transformation configurations."""
        default_transformations = [
            TransformationConfig("brightness", "output_bright.jpg", {"factor": 1.3}, "Brightness adjustment"),
            TransformationConfig("contrast", "output_contrast.jpg", {"factor": 1.5}, "Contrast enhancement"),
            TransformationConfig("sepia", "output_sepia.jpg", {}, "Sepia filter"),
            TransformationConfig("grayscale", "output_grayscale.jpg", {}, "Grayscale conversion"),
            TransformationConfig("invert", "output_inverted.jpg", {}, "Color inversion"),
            TransformationConfig("gaussian_blur", "output_gaussian_blur.jpg", {"kernel_size": 5}, "Gaussian blur (5x5 kernel)"),
            TransformationConfig("gaussian_blur_pillow", "output_pillow_blur.jpg", {"radius": 3.0}, "Pillow Gaussian blur"),
            TransformationConfig("saturation_pillow", "output_pillow_saturated.jpg", {"factor": 1.6}, "Pillow saturation adjustment"),
            TransformationConfig("unsharp_mask", "output_unsharp_mask.jpg", {"radius": 2.0, "percent": 150, "threshold": 3}, "Unsharp mask"),
            TransformationConfig("emboss", "output_emboss.jpg", {}, "Emboss effect"),
            TransformationConfig("find_edges", "output_edges.jpg", {}, "Edge detection"),
            TransformationConfig("contour", "output_contour.jpg", {}, "Contour effect"),
            TransformationConfig("rotate", "output_rotated.jpg", {"angle": 45, "expand": True}, "45-degree rotation"),
            TransformationConfig("resize", "output_resized.jpg", {"width": 800, "height": 600, "resample": "lanczos"}, "Resize to 800x600"),
        ]
        
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    return [TransformationConfig(**t) for t in config_data.get('transformations', [])]
            except Exception as e:
                print(f"⚠️  Could not load config file: {e}. Using defaults.")
        
        return default_transformations
    
    def save_transformation_to_db(self, image_path: str, transformation_type: str, 
                                output_path: str, parameters: dict = None, 
                                processing_time: int = None) -> Optional[TransformationHistory]:
        """Save transformation to database with enhanced error handling."""
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
                return transformation
            else:
                print("⚠️  Failed to save transformation to database")
                return None
                
        except Exception as e:
            print(f"❌ Database error: {e}")
            return None
    
    def apply_transformation(self, transformer: ImageColorTransformer, 
                           config: TransformationConfig) -> BatchResult:
        """Apply a single transformation with enhanced error handling."""
        start_time = time.time()
        transformation_id = f"{config.type}_{int(time.time())}"
        
        try:
            # Apply transformation based on type
            if config.type == "brightness":
                factor = config.parameters.get("factor", 1.3)
                transformer.adjust_brightness(factor)
            elif config.type == "contrast":
                factor = config.parameters.get("factor", 1.5)
                transformer.adjust_contrast(factor)
            elif config.type == "sepia":
                transformer.apply_sepia()
            elif config.type == "grayscale":
                transformer.to_grayscale()
            elif config.type == "invert":
                transformer.invert_colors()
            elif config.type == "gaussian_blur":
                kernel_size = config.parameters.get("kernel_size", 5)
                transformer.apply_gaussian_blur(kernel_size)
            elif config.type == "gaussian_blur_pillow":
                radius = config.parameters.get("radius", 2.0)
                transformer.apply_gaussian_blur_pillow(radius)
            elif config.type == "saturation_pillow":
                factor = config.parameters.get("factor", 1.5)
                transformer.adjust_saturation_pillow(factor)
            elif config.type == "unsharp_mask":
                radius = config.parameters.get("radius", 2.0)
                percent = config.parameters.get("percent", 150)
                threshold = config.parameters.get("threshold", 3)
                transformer.apply_unsharp_mask_pillow(radius, percent, threshold)
            elif config.type == "emboss":
                transformer.apply_emboss_pillow()
            elif config.type == "find_edges":
                transformer.apply_find_edges_pillow()
            elif config.type == "contour":
                transformer.apply_contour_pillow()
            elif config.type == "rotate":
                angle = config.parameters.get("angle", 45)
                expand = config.parameters.get("expand", True)
                transformer.rotate_pillow(angle, expand)
            elif config.type == "resize":
                width = config.parameters.get("width", 800)
                height = config.parameters.get("height", 600)
                resample = config.parameters.get("resample", "lanczos")
                transformer.resize_pillow(width, height, resample)
            else:
                raise ValueError(f"Unknown transformation type: {config.type}")
            
            # Save transformed image
            output_path = os.path.join(settings.output_dir, config.filename)
            transformer.save_image(output_path)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            # Save to database
            db_transformation = self.save_transformation_to_db(
                image_path=transformer.image_path,
                transformation_type=config.type,
                output_path=output_path,
                parameters=config.parameters,
                processing_time=processing_time
            )
            
            return BatchResult(
                transformation_id=transformation_id,
                type=config.type,
                success=True,
                processing_time=processing_time,
                output_path=output_path
            )
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            return BatchResult(
                transformation_id=transformation_id,
                type=config.type,
                success=False,
                processing_time=processing_time,
                output_path="",
                error_message=str(e)
            )
    
    def process_image(self, image_path: str, batch_mode: bool = False) -> Dict[str, Any]:
        """Process an image with all enabled transformations."""
        print(f"\n=== Processing image: {image_path} ===")
        
        # Create transformer instance
        transformer = ImageColorTransformer(image_path)
        
        # Check if image is loaded properly (fix for NumPy array truthiness)
        if transformer.image is None:
            return {"success": False, "error": "No valid image loaded"}
        
        print(f"✅ Image loaded: {transformer.image_path}")
        print(f"Image size: {transformer.image.shape if hasattr(transformer.image, 'shape') else 'Unknown'}")
        
        # Process transformations
        enabled_transformations = [t for t in self.transformations if t.enabled]
        total_transformations = len(enabled_transformations)
        
        print(f"\n=== Applying {total_transformations} transformations ===")
        
        successful_transformations = 0
        failed_transformations = 0
        
        for i, config in enumerate(enabled_transformations, 1):
            print(f"\n{i}/{total_transformations}. {config.description}...")
            
            # Reset transformer for each transformation
            transformer.reset()
            
            # Apply transformation
            result = self.apply_transformation(transformer, config)
            self.results.append(result)
            
            if result.success:
                successful_transformations += 1
                print(f"✅ {config.type} completed in {result.processing_time}ms")
            else:
                failed_transformations += 1
                print(f"❌ {config.type} failed: {result.error_message}")
        
        # Summary
        total_time = int((time.time() - self.start_time) * 1000)
        
        summary = {
            "success": True,
            "image_path": image_path,
            "total_transformations": total_transformations,
            "successful_transformations": successful_transformations,
            "failed_transformations": failed_transformations,
            "total_processing_time": total_time,
            "average_time_per_transformation": total_time // total_transformations if total_transformations > 0 else 0,
            "results": [asdict(result) for result in self.results]
        }
        
        return summary


def main():
    """Main function with advanced features (v3)."""
    parser = argparse.ArgumentParser(description="Advanced Image Processor v3")
    parser.add_argument("image_path", nargs="?", help="Path to the image file")
    parser.add_argument("--batch", action="store_true", help="Enable batch processing mode")
    parser.add_argument("--config", help="Path to configuration JSON file")
    parser.add_argument("--list-transformations", action="store_true", help="List all available transformations")
    
    args = parser.parse_args()
    
    try:
        print("=== Image Color Transformer v3 - Advanced Features ===")
        print(f"Version: 3.0 (Advanced Features)")
        print(f"Stage: 4+ (Advanced Features)")
        print(f"Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")
        print(f"Schema: image_processor")
        
        # Ensure directories exist
        ensure_directories()
        output_dir = settings.output_dir
        print(f"📁 Output directory: {output_dir}")
        
        # Initialize processor
        processor = AdvancedImageProcessor(args.config)
        
        if args.list_transformations:
            print(f"\n=== Available Transformations ===")
            for i, config in enumerate(processor.transformations, 1):
                status = "✅ Enabled" if config.enabled else "❌ Disabled"
                print(f"{i:2d}. {config.type:20s} - {config.description} ({status})")
            return
        
        # Check if image source is provided
        image_source = args.image_path
        if not image_source:
            print("No image source provided. Will prompt for input.")
            image_source = input("Enter image path: ").strip()
        
        if not image_source:
            print("❌ No image source provided. Exiting.")
            return
        
        # Process image
        summary = processor.process_image(image_source, args.batch)
        
        if summary["success"]:
            print(f"\n=== Processing Summary (v3) ===")
            print(f"✅ Successful transformations: {summary['successful_transformations']}/{summary['total_transformations']}")
            print(f"❌ Failed transformations: {summary['failed_transformations']}")
            print(f"⏱️  Total processing time: {summary['total_processing_time']}ms")
            print(f"📊 Average time per transformation: {summary['average_time_per_transformation']}ms")
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
        else:
            print(f"❌ Processing failed: {summary.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ Error in main v3: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 