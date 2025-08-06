"""
Pillow (PIL) Example - Native Python Image Processing

Pillow is the most popular "native" Python image library.
It's a fork of PIL (Python Imaging Library) and is considered
the standard for image processing in Python.
"""

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import os


class PillowImageProcessor:
    """Image processor using Pillow (PIL) - Native Python approach."""
    
    def __init__(self, image_path: str = None):
        self.image = None
        self.original_image = None
        
        if image_path:
            self.load_image(image_path)
    
    def load_image(self, image_path: str) -> bool:
        """Load image using Pillow."""
        try:
            if not os.path.exists(image_path):
                print(f"❌ Image file not found: {image_path}")
                return False
            
            # Load image with Pillow
            self.image = Image.open(image_path)
            self.original_image = self.image.copy()
            
            print(f"✅ Loaded image: {image_path}")
            print(f"   Format: {self.image.format}")
            print(f"   Mode: {self.image.mode}")
            print(f"   Size: {self.image.size}")
            
            # Convert to RGB if needed
            if self.image.mode != 'RGB':
                self.image = self.image.convert('RGB')
                print(f"   Converted to RGB mode")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading image: {e}")
            return False
    
    def adjust_brightness(self, factor: float):
        """Adjust image brightness using Pillow."""
        if self.image is None:
            print("❌ No image loaded")
            return
        
        enhancer = ImageEnhance.Brightness(self.image)
        self.image = enhancer.enhance(factor)
        print(f"✅ Brightness adjusted by factor: {factor}")
    
    def adjust_contrast(self, factor: float):
        """Adjust image contrast using Pillow."""
        if self.image is None:
            print("❌ No image loaded")
            return
        
        enhancer = ImageEnhance.Contrast(self.image)
        self.image = enhancer.enhance(factor)
        print(f"✅ Contrast adjusted by factor: {factor}")
    
    def adjust_saturation(self, factor: float):
        """Adjust image saturation using Pillow."""
        if self.image is None:
            print("❌ No image loaded")
            return
        
        enhancer = ImageEnhance.Color(self.image)
        self.image = enhancer.enhance(factor)
        print(f"✅ Saturation adjusted by factor: {factor}")
    
    def apply_sepia(self):
        """Apply sepia filter using Pillow."""
        if self.image is None:
            print("❌ No image loaded")
            return
        
        # Convert to numpy array for processing
        img_array = np.array(self.image)
        
        # Sepia transformation matrix
        sepia_matrix = np.array([
            [0.393, 0.769, 0.189],
            [0.349, 0.686, 0.168],
            [0.272, 0.534, 0.131]
        ])
        
        # Apply transformation
        sepia_array = np.dot(img_array, sepia_matrix.T)
        sepia_array = np.clip(sepia_array, 0, 255).astype(np.uint8)
        
        # Convert back to Pillow image
        self.image = Image.fromarray(sepia_array)
        print("✅ Sepia filter applied")
    
    def to_grayscale(self):
        """Convert to grayscale using Pillow."""
        if self.image is None:
            print("❌ No image loaded")
            return
        
        self.image = self.image.convert('L').convert('RGB')
        print("✅ Converted to grayscale")
    
    def apply_blur(self, radius: int = 2):
        """Apply blur filter using Pillow."""
        if self.image is None:
            print("❌ No image loaded")
            return
        
        self.image = self.image.filter(ImageFilter.GaussianBlur(radius=radius))
        print(f"✅ Blur applied with radius: {radius}")
    
    def resize(self, width: int, height: int):
        """Resize image using Pillow."""
        if self.image is None:
            print("❌ No image loaded")
            return
        
        self.image = self.image.resize((width, height), Image.Resampling.LANCZOS)
        print(f"✅ Image resized to: {width}x{height}")
    
    def rotate(self, angle: float):
        """Rotate image using Pillow."""
        if self.image is None:
            print("❌ No image loaded")
            return
        
        self.image = self.image.rotate(angle, expand=True)
        print(f"✅ Image rotated by {angle} degrees")
    
    def save_image(self, output_path: str) -> bool:
        """Save image using Pillow."""
        if self.image is None:
            print("❌ No image loaded")
            return False
        
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            self.image.save(output_path)
            print(f"✅ Image saved: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving image: {e}")
            return False
    
    def reset(self):
        """Reset to original image."""
        if self.original_image is None:
            print("❌ No original image available")
            return
        
        self.image = self.original_image.copy()
        print("✅ Reset to original image")
    
    def get_info(self) -> dict:
        """Get image information."""
        if self.image is None:
            return {}
        
        return {
            'format': self.image.format,
            'mode': self.image.mode,
            'size': self.image.size,
            'width': self.image.width,
            'height': self.image.height
        }


def demonstrate_pillow():
    """Demonstrate Pillow capabilities."""
    print("🐍 PILLOW (PIL) IMAGE PROCESSING DEMO")
    print("=" * 50)
    
    # Check for test image
    image_path = "sources/images.jpeg"
    
    if not os.path.exists(image_path):
        print(f"❌ Test image not found: {image_path}")
        print("Please ensure you have an image file to test with.")
        return
    
    # Create processor
    processor = PillowImageProcessor(image_path)
    
    if processor.image is None:
        print("❌ Failed to load image")
        return
    
    # Show original info
    info = processor.get_info()
    print(f"\n📊 Original image info: {info}")
    
    # Apply transformations
    print("\n🎨 Applying transformations...")
    
    # Brightness
    processor.adjust_brightness(1.3)
    processor.save_image("output/pillow_bright.jpg")
    
    # Reset and apply contrast
    processor.reset()
    processor.adjust_contrast(1.5)
    processor.save_image("output/pillow_contrast.jpg")
    
    # Reset and apply sepia
    processor.reset()
    processor.apply_sepia()
    processor.save_image("output/pillow_sepia.jpg")
    
    # Reset and convert to grayscale
    processor.reset()
    processor.to_grayscale()
    processor.save_image("output/pillow_grayscale.jpg")
    
    # Reset and apply blur
    processor.reset()
    processor.apply_blur(3)
    processor.save_image("output/pillow_blur.jpg")
    
    # Reset and resize
    processor.reset()
    processor.resize(800, 600)
    processor.save_image("output/pillow_resized.jpg")
    
    print("\n✅ All Pillow transformations completed!")
    print("📁 Check the output/ directory for results.")


if __name__ == "__main__":
    demonstrate_pillow() 