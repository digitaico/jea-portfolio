import numpy as np
import cv2
import os
import warnings
import urllib.request
import tempfile
from typing import Optional, Dict

# Pillow for additional image processing capabilities
try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    warnings.warn("Pillow not available. Pillow methods will not work.", UserWarning)


class ImageColorTransformer:
    """Simple class to transform image colors using NumPy."""
    
    def __init__(self, image_source: Optional[str] = None):
        self.image = None
        self.original_image = None
        self.image_path = None  # Store the image path
        self.stored_images: Dict[str, np.ndarray] = {}
        
        if image_source:
            # Try to load from the provided source (URL or local path)
            if self._is_url(image_source):
                if not self._load_image_from_url(image_source):
                    raise ValueError(f"Failed to load image from URL: {image_source}")
            else:
                if not self.load_image(image_source):
                    raise ValueError(f"Failed to load image from path: {image_source}")
        else:
            # Ask user for image source
            self._get_image_from_user()
    
    def _is_url(self, source: str) -> bool:
        """Check if the source is a URL."""
        return source.startswith(('http://', 'https://'))
    
    def _get_image_from_user(self):
        """Ask user for image URL or local path and load it."""
        while True:
            image_source = input("Please provide an image URL or local file path: ").strip()
            
            if not image_source:
                print("Source cannot be empty. Please try again.")
                continue
            
            if self._is_url(image_source):
                if self._load_image_from_url(image_source):
                    print(f"Successfully loaded image from URL: {image_source}")
                    break
                else:
                    print("Failed to load image from URL. Please check the URL and try again.")
            else:
                if self.load_image(image_source):
                    print(f"Successfully loaded image from path: {image_source}")
                    break
                else:
                    print("Failed to load image from path. Please check the path and try again.")
    
    def _load_image_from_url(self, image_url: str) -> bool:
        """Load image from URL."""
        try:
            # Create a temporary file to store the downloaded image
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                temp_path = tmp_file.name
            
            # Download the image
            print("Downloading image...")
            urllib.request.urlretrieve(image_url, temp_path)
            
            # Load the image using OpenCV
            self.image = cv2.imread(temp_path)
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            if self.image is not None:
                self.original_image = self.image.copy()
                self.image_path = image_url  # Store the URL
                return True
            else:
                warnings.warn(f"Failed to load image from URL: {image_url}", UserWarning)
                return False
                
        except Exception as e:
            warnings.warn(f"Error loading image from URL {image_url}: {str(e)}", UserWarning)
            return False
    
    def _validate_image_path(self, image_path: str) -> bool:
        """Validate if the image path is valid and file exists."""
        if not image_path or not isinstance(image_path, str):
            warnings.warn("Image path must be a non-empty string", UserWarning)
            return False
        
        if not os.path.exists(image_path):
            warnings.warn(f"Image file does not exist: {image_path}", UserWarning)
            return False
        
        # Check file extension
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        file_ext = os.path.splitext(image_path)[1].lower()
        
        if file_ext not in valid_extensions:
            warnings.warn(f"Unsupported image format: {file_ext}. Supported formats: {valid_extensions}", UserWarning)
            return False
        
        return True
    
    def load_image(self, image_path: str) -> bool:
        """Load an image from local path."""
        try:
            if not self._validate_image_path(image_path):
                return False
            
            self.image = cv2.imread(image_path)
            if self.image is not None:
                self.original_image = self.image.copy()
                self.image_path = image_path  # Store the image path
                return True
            else:
                warnings.warn(f"Failed to load image: {image_path}", UserWarning)
                return False
        except Exception as e:
            warnings.warn(f"Error loading image {image_path}: {str(e)}", UserWarning)
            return False
    
    def _check_image_loaded(self):
        """Check if image is loaded and raise warning if not."""
        if self.image is None:
            warnings.warn("No image loaded. Please load an image first.", UserWarning)
            return False
        return True
    
    def store_image(self, name: str) -> bool:
        """Store the current image with a given name."""
        if not self._check_image_loaded():
            return False
        
        if not name or not isinstance(name, str):
            warnings.warn("Image name must be a non-empty string", UserWarning)
            return False
        
        self.stored_images[name] = self.image.copy()
        return True
    
    def load_stored_image(self, name: str) -> bool:
        """Load a previously stored image by name."""
        if name not in self.stored_images:
            warnings.warn(f"Stored image '{name}' not found", UserWarning)
            return False
        
        self.image = self.stored_images[name].copy()
        return True
    
    def list_stored_images(self) -> list:
        """Return list of stored image names."""
        return list(self.stored_images.keys())
    
    def remove_stored_image(self, name: str) -> bool:
        """Remove a stored image by name."""
        if name in self.stored_images:
            del self.stored_images[name]
            return True
        else:
            warnings.warn(f"Stored image '{name}' not found", UserWarning)
            return False
    
    def adjust_brightness(self, factor: float):
        """Adjust image brightness."""
        if self._check_image_loaded():
            self.image = np.clip(self.image * factor, 0, 255).astype(np.uint8)
    
    def adjust_contrast(self, factor: float):
        """Adjust image contrast."""
        if self._check_image_loaded():
            mean = np.mean(self.image)
            self.image = np.clip((self.image - mean) * factor + mean, 0, 255).astype(np.uint8)
    
    def apply_sepia(self):
        """Apply sepia filter."""
        if self._check_image_loaded():
            sepia_matrix = np.array([
                [0.393, 0.769, 0.189],
                [0.349, 0.686, 0.168],
                [0.272, 0.534, 0.131]
            ])
            self.image = cv2.transform(self.image.astype(np.float32), sepia_matrix)
            self.image = np.clip(self.image, 0, 255).astype(np.uint8)
    
    def to_grayscale(self):
        """Convert to grayscale."""
        if self._check_image_loaded():
            gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            self.image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    
    def invert_colors(self):
        """Invert image colors."""
        if self._check_image_loaded():
            self.image = 255 - self.image
    
    def apply_gaussian_blur(self, kernel_size: int = 5):
        """
        Apply Gaussian blur to the image.
        
        Args:
            kernel_size: Size of the Gaussian kernel (must be odd number).
                        Default is 5 for a 5x5 kernel.
        """
        if self._check_image_loaded():
            # Ensure kernel size is odd (required for Gaussian blur)
            if kernel_size % 2 == 0:
                kernel_size += 1
                warnings.warn(f"Kernel size must be odd. Using {kernel_size} instead.", UserWarning)
            
            # Apply Gaussian blur using OpenCV
            self.image = cv2.GaussianBlur(self.image, (kernel_size, kernel_size), 0)
    
    # ==================== PILLOW METHODS ====================
    
    def _convert_to_pillow(self):
        """Convert OpenCV image to Pillow image."""
        if not PILLOW_AVAILABLE:
            warnings.warn("Pillow not available. Cannot convert to Pillow image.", UserWarning)
            return None
        
        if self.image is None:
            return None
        
        # Convert BGR to RGB for Pillow
        rgb_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_image)
    
    def _convert_from_pillow(self, pillow_image):
        """Convert Pillow image back to OpenCV format."""
        if pillow_image is None:
            return
        
        # Convert to numpy array
        rgb_array = np.array(pillow_image)
        
        # Convert RGB to BGR for OpenCV
        self.image = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
    
    def adjust_brightness_pillow(self, factor: float):
        """
        Adjust image brightness using Pillow.
        
        Args:
            factor: Brightness factor (0.0 = black, 1.0 = original, >1.0 = brighter)
        """
        if not PILLOW_AVAILABLE:
            warnings.warn("Pillow not available. Use adjust_brightness() instead.", UserWarning)
            return
        
        if self._check_image_loaded():
            pillow_image = self._convert_to_pillow()
            if pillow_image:
                enhancer = ImageEnhance.Brightness(pillow_image)
                enhanced_image = enhancer.enhance(factor)
                self._convert_from_pillow(enhanced_image)
    
    def adjust_contrast_pillow(self, factor: float):
        """
        Adjust image contrast using Pillow.
        
        Args:
            factor: Contrast factor (0.0 = gray, 1.0 = original, >1.0 = more contrast)
        """
        if not PILLOW_AVAILABLE:
            warnings.warn("Pillow not available. Use adjust_contrast() instead.", UserWarning)
            return
        
        if self._check_image_loaded():
            pillow_image = self._convert_to_pillow()
            if pillow_image:
                enhancer = ImageEnhance.Contrast(pillow_image)
                enhanced_image = enhancer.enhance(factor)
                self._convert_from_pillow(enhanced_image)
    
    def adjust_saturation_pillow(self, factor: float):
        """
        Adjust image saturation using Pillow.
        
        Args:
            factor: Saturation factor (0.0 = grayscale, 1.0 = original, >1.0 = more saturated)
        """
        if not PILLOW_AVAILABLE:
            warnings.warn("Pillow not available.", UserWarning)
            return
        
        if self._check_image_loaded():
            pillow_image = self._convert_to_pillow()
            if pillow_image:
                enhancer = ImageEnhance.Color(pillow_image)
                enhanced_image = enhancer.enhance(factor)
                self._convert_from_pillow(enhanced_image)
    
    def apply_gaussian_blur_pillow(self, radius: float = 2.0):
        """
        Apply Gaussian blur using Pillow.
        
        Args:
            radius: Blur radius (higher values = more blur)
        """
        if not PILLOW_AVAILABLE:
            warnings.warn("Pillow not available. Use apply_gaussian_blur() instead.", UserWarning)
            return
        
        if self._check_image_loaded():
            pillow_image = self._convert_to_pillow()
            if pillow_image:
                blurred_image = pillow_image.filter(ImageFilter.GaussianBlur(radius=radius))
                self._convert_from_pillow(blurred_image)
    
    def apply_median_filter_pillow(self, size: int = 3):
        """
        Apply median filter using Pillow (good for noise reduction).
        
        Args:
            size: Filter size (3 = 3x3, 5 = 5x5, etc.)
        """
        if not PILLOW_AVAILABLE:
            warnings.warn("Pillow not available.", UserWarning)
            return
        
        if self._check_image_loaded():
            pillow_image = self._convert_to_pillow()
            if pillow_image:
                filtered_image = pillow_image.filter(ImageFilter.MedianFilter(size=size))
                self._convert_from_pillow(filtered_image)
    
    def apply_unsharp_mask_pillow(self, radius: float = 2.0, percent: int = 150, threshold: int = 3):
        """
        Apply unsharp mask using Pillow (sharpening filter).
        
        Args:
            radius: Blur radius for the mask
            percent: Sharpening strength (100 = no effect, 200 = double sharpness)
            threshold: Minimum brightness change to apply sharpening
        """
        if not PILLOW_AVAILABLE:
            warnings.warn("Pillow not available.", UserWarning)
            return
        
        if self._check_image_loaded():
            pillow_image = self._convert_to_pillow()
            if pillow_image:
                sharpened_image = pillow_image.filter(
                    ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold)
                )
                self._convert_from_pillow(sharpened_image)
    
    def rotate_pillow(self, angle: float, expand: bool = True):
        """
        Rotate image using Pillow.
        
        Args:
            angle: Rotation angle in degrees (positive = clockwise)
            expand: Whether to expand the image to fit the rotated content
        """
        if not PILLOW_AVAILABLE:
            warnings.warn("Pillow not available.", UserWarning)
            return
        
        if self._check_image_loaded():
            pillow_image = self._convert_to_pillow()
            if pillow_image:
                rotated_image = pillow_image.rotate(angle, expand=expand)
                self._convert_from_pillow(rotated_image)
    
    def resize_pillow(self, width: int, height: int, resample: str = 'lanczos'):
        """
        Resize image using Pillow.
        
        Args:
            width: New width in pixels
            height: New height in pixels
            resample: Resampling method ('nearest', 'bilinear', 'bicubic', 'lanczos')
        """
        if not PILLOW_AVAILABLE:
            warnings.warn("Pillow not available.", UserWarning)
            return
        
        if self._check_image_loaded():
            pillow_image = self._convert_to_pillow()
            if pillow_image:
                # Map resample string to Pillow constant
                resample_map = {
                    'nearest': Image.Resampling.NEAREST,
                    'bilinear': Image.Resampling.BILINEAR,
                    'bicubic': Image.Resampling.BICUBIC,
                    'lanczos': Image.Resampling.LANCZOS
                }
                
                resample_method = resample_map.get(resample.lower(), Image.Resampling.LANCZOS)
                resized_image = pillow_image.resize((width, height), resample_method)
                self._convert_from_pillow(resized_image)
    
    def apply_emboss_pillow(self):
        """Apply emboss effect using Pillow."""
        if not PILLOW_AVAILABLE:
            warnings.warn("Pillow not available.", UserWarning)
            return
        
        if self._check_image_loaded():
            pillow_image = self._convert_to_pillow()
            if pillow_image:
                embossed_image = pillow_image.filter(ImageFilter.EMBOSS)
                self._convert_from_pillow(embossed_image)
    
    def apply_find_edges_pillow(self):
        """Apply edge detection using Pillow."""
        if not PILLOW_AVAILABLE:
            warnings.warn("Pillow not available.", UserWarning)
            return
        
        if self._check_image_loaded():
            pillow_image = self._convert_to_pillow()
            if pillow_image:
                edges_image = pillow_image.filter(ImageFilter.FIND_EDGES)
                self._convert_from_pillow(edges_image)
    
    def apply_contour_pillow(self):
        """Apply contour effect using Pillow."""
        if not PILLOW_AVAILABLE:
            warnings.warn("Pillow not available.", UserWarning)
            return
        
        if self._check_image_loaded():
            pillow_image = self._convert_to_pillow()
            if pillow_image:
                contour_image = pillow_image.filter(ImageFilter.CONTOUR)
                self._convert_from_pillow(contour_image)
    
    def save_image(self, output_path: str) -> bool:
        """Save the current image."""
        if not self._check_image_loaded():
            return False
        
        try:
            return cv2.imwrite(output_path, self.image)
        except Exception as e:
            warnings.warn(f"Error saving image to {output_path}: {str(e)}", UserWarning)
            return False
    
    def reset(self):
        """Reset to original image."""
        if self.original_image is not None:
            self.image = self.original_image.copy()
        else:
            warnings.warn("No original image available to reset to", UserWarning) 