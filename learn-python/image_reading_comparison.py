"""
Image Reading Methods in Python - A Comprehensive Comparison

This script demonstrates different ways to read images in Python,
from native libraries to popular third-party options.
"""

import os
import sys
from pathlib import Path

# Native Python libraries
from PIL import Image  # Pillow (PIL fork) - Most popular native option
import io

# Standard library (limited but available)
import base64

# Third-party libraries
import numpy as np
import cv2

# For demonstration
import urllib.request
import tempfile


class ImageReaderComparison:
    """Demonstrates different methods to read images in Python."""
    
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.image_data = None
    
    def read_with_pillow(self):
        """Read image using Pillow (PIL) - Most popular native option."""
        print("=== Reading with Pillow (PIL) ===")
        try:
            # Pillow is the most popular "native" image library
            # It's a fork of PIL (Python Imaging Library)
            image = Image.open(self.image_path)
            
            print(f"Image format: {image.format}")
            print(f"Image mode: {image.mode}")
            print(f"Image size: {image.size}")
            print(f"Image info: {image.info}")
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array if needed
            image_array = np.array(image)
            print(f"Numpy array shape: {image_array.shape}")
            
            return image, image_array
            
        except Exception as e:
            print(f"Error reading with Pillow: {e}")
            return None, None
    
    def read_with_opencv(self):
        """Read image using OpenCV."""
        print("\n=== Reading with OpenCV ===")
        try:
            # OpenCV reads images as BGR (not RGB)
            image = cv2.imread(self.image_path)
            
            if image is not None:
                print(f"Image shape: {image.shape}")
                print(f"Image dtype: {image.dtype}")
                print(f"Image channels: {image.shape[2] if len(image.shape) > 2 else 1}")
                
                # Convert BGR to RGB for consistency
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                return image, image_rgb
            else:
                print("Failed to load image with OpenCV")
                return None, None
                
        except Exception as e:
            print(f"Error reading with OpenCV: {e}")
            return None, None
    
    def read_with_numpy(self):
        """Read image using NumPy (limited support)."""
        print("\n=== Reading with NumPy ===")
        try:
            # NumPy can read some image formats directly
            # But it's limited and not recommended for general use
            image_array = np.fromfile(self.image_path, dtype=np.uint8)
            print(f"Raw bytes loaded: {len(image_array)} bytes")
            
            # This is just raw bytes - not a proper image
            # NumPy alone can't decode most image formats
            return None, image_array
            
        except Exception as e:
            print(f"Error reading with NumPy: {e}")
            return None, None
    
    def read_with_standard_library(self):
        """Read image using only standard library (very limited)."""
        print("\n=== Reading with Standard Library ===")
        try:
            # Standard library can only read raw bytes
            with open(self.image_path, 'rb') as f:
                raw_bytes = f.read()
            
            print(f"Raw bytes: {len(raw_bytes)} bytes")
            
            # Convert to base64 for demonstration
            base64_data = base64.b64encode(raw_bytes).decode('utf-8')
            print(f"Base64 length: {len(base64_data)} characters")
            
            return raw_bytes, base64_data
            
        except Exception as e:
            print(f"Error reading with standard library: {e}")
            return None, None
    
    def compare_methods(self):
        """Compare all reading methods."""
        print("🔍 COMPARING IMAGE READING METHODS")
        print("=" * 50)
        
        # Check if file exists
        if not os.path.exists(self.image_path):
            print(f"❌ Image file not found: {self.image_path}")
            return
        
        print(f"📁 Reading image: {self.image_path}")
        print(f"📊 File size: {os.path.getsize(self.image_path)} bytes")
        print()
        
        # Test each method
        results = {}
        
        # Pillow (most popular "native" option)
        pillow_image, pillow_array = self.read_with_pillow()
        results['pillow'] = {
            'success': pillow_image is not None,
            'type': type(pillow_image).__name__ if pillow_image else None,
            'shape': pillow_array.shape if pillow_array is not None else None
        }
        
        # OpenCV
        opencv_image, opencv_rgb = self.read_with_opencv()
        results['opencv'] = {
            'success': opencv_image is not None,
            'type': type(opencv_image).__name__ if opencv_image else None,
            'shape': opencv_image.shape if opencv_image is not None else None
        }
        
        # NumPy (limited)
        numpy_image, numpy_array = self.read_with_numpy()
        results['numpy'] = {
            'success': numpy_array is not None,
            'type': type(numpy_array).__name__ if numpy_array else None,
            'shape': numpy_array.shape if numpy_array is not None else None
        }
        
        # Standard library
        stdlib_image, stdlib_base64 = self.read_with_standard_library()
        results['stdlib'] = {
            'success': stdlib_image is not None,
            'type': type(stdlib_image).__name__ if stdlib_image else None,
            'shape': len(stdlib_image) if stdlib_image else None
        }
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 SUMMARY")
        print("=" * 50)
        
        for method, result in results.items():
            status = "✅" if result['success'] else "❌"
            print(f"{status} {method.upper():<10} - {result['type'] or 'Failed'}")
            if result['shape']:
                print(f"    Shape/Size: {result['shape']}")
        
        print("\n💡 RECOMMENDATIONS:")
        print("- Pillow (PIL): Best for general image processing")
        print("- OpenCV: Best for computer vision and image analysis")
        print("- NumPy: Use with Pillow/OpenCV for array operations")
        print("- Standard Library: Only for raw byte access")


def demonstrate_native_alternatives():
    """Demonstrate native Python alternatives to OpenCV."""
    print("\n" + "=" * 60)
    print("🐍 NATIVE PYTHON IMAGE PROCESSING ALTERNATIVES")
    print("=" * 60)
    
    # Example image path
    image_path = "sources/images.jpeg"
    
    if not os.path.exists(image_path):
        print(f"❌ Test image not found: {image_path}")
        print("Please ensure you have an image file to test with.")
        return
    
    # Create comparison instance
    comparison = ImageReaderComparison(image_path)
    comparison.compare_methods()
    
    print("\n" + "=" * 60)
    print("🎯 KEY INSIGHTS")
    print("=" * 60)
    
    print("""
1. **Pillow (PIL)** - The "native" Python image library:
   ✅ Most popular and widely supported
   ✅ Handles many image formats
   ✅ Good for basic image processing
   ✅ Pure Python (with C extensions)
   ❌ Slower than OpenCV for large images
   ❌ Limited computer vision features

2. **OpenCV** - Computer vision focused:
   ✅ Fast and efficient
   ✅ Advanced computer vision features
   ✅ Excellent for image analysis
   ✅ Industry standard
   ❌ C++ library with Python bindings
   ❌ BGR color format (not RGB)

3. **NumPy** - Numerical computing:
   ✅ Fast array operations
   ✅ Memory efficient
   ✅ Great for mathematical operations
   ❌ Cannot read image formats directly
   ❌ Needs other libraries for image I/O

4. **Standard Library** - Raw access only:
   ✅ No external dependencies
   ✅ Direct file access
   ❌ Cannot decode image formats
   ❌ Limited to raw bytes
    """)


if __name__ == "__main__":
    demonstrate_native_alternatives() 