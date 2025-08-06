"""
Enhanced Image Transformer - Demonstrating Advanced Python Concepts

This enhanced version shows:
- Logging and error handling
- Configuration management
- JSON data handling
- Decorators
- Context managers
- List comprehensions
- Type hints
- File system operations
"""

import numpy as np
import cv2
import os
import warnings
import urllib.request
import tempfile
import json
import logging
import time
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path
import configparser


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_transformer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TransformationConfig:
    """Configuration for image transformations."""
    brightness_factor: float = 1.0
    contrast_factor: float = 1.0
    saturation_factor: float = 1.0
    output_format: str = 'jpg'
    quality: int = 95


def timer_decorator(func):
    """Decorator to measure function execution time."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper


class ImageMetadata:
    """Context manager for handling image metadata."""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.metadata = {}
    
    def __enter__(self):
        logger.info(f"Starting metadata collection for {self.filename}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"Error processing {self.filename}: {exc_val}")
        else:
            logger.info(f"Completed metadata collection for {self.filename}")
        return False


class EnhancedImageColorTransformer:
    """Enhanced image transformer with advanced Python features."""
    
    def __init__(self, image_source: Optional[str] = None, config_file: str = 'config.ini'):
        self.image = None
        self.original_image = None
        self.stored_images: Dict[str, np.ndarray] = {}
        self.transformation_history: List[Dict] = []
        self.config = self._load_config(config_file)
        
        if image_source:
            self._load_image_source(image_source)
        else:
            self._get_image_from_user()
    
    def _load_config(self, config_file: str) -> TransformationConfig:
        """Load configuration from file."""
        config = TransformationConfig()
        
        if os.path.exists(config_file):
            parser = configparser.ConfigParser()
            parser.read(config_file)
            
            if 'DEFAULT' in parser:
                config.brightness_factor = parser.getfloat('DEFAULT', 'brightness_factor', fallback=1.0)
                config.contrast_factor = parser.getfloat('DEFAULT', 'contrast_factor', fallback=1.0)
                config.saturation_factor = parser.getfloat('DEFAULT', 'saturation_factor', fallback=1.0)
                config.output_format = parser.get('DEFAULT', 'output_format', fallback='jpg')
                config.quality = parser.getint('DEFAULT', 'quality', fallback=95)
        
        return config
    
    def _is_url(self, source: str) -> bool:
        """Check if the source is a URL."""
        return source.startswith(('http://', 'https://'))
    
    def _load_image_source(self, image_source: str) -> bool:
        """Load image from URL or local path."""
        try:
            if self._is_url(image_source):
                return self._load_image_from_url(image_source)
            else:
                return self.load_image(image_source)
        except Exception as e:
            logger.error(f"Failed to load image from {image_source}: {e}")
            return False
    
    @timer_decorator
    def _load_image_from_url(self, image_url: str) -> bool:
        """Load image from URL with timing."""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                temp_path = tmp_file.name
            
            logger.info(f"Downloading image from {image_url}")
            urllib.request.urlretrieve(image_url, temp_path)
            
            self.image = cv2.imread(temp_path)
            os.unlink(temp_path)
            
            if self.image is not None:
                self.original_image = self.image.copy()
                self._save_metadata('url_load', {'url': image_url})
                return True
            else:
                logger.warning(f"Failed to load image from URL: {image_url}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading image from URL {image_url}: {e}")
            return False
    
    def _validate_image_path(self, image_path: str) -> bool:
        """Validate if the image path is valid and file exists."""
        if not image_path or not isinstance(image_path, str):
            logger.warning("Image path must be a non-empty string")
            return False
        
        if not os.path.exists(image_path):
            logger.warning(f"Image file does not exist: {image_path}")
            return False
        
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        file_ext = Path(image_path).suffix.lower()
        
        if file_ext not in valid_extensions:
            logger.warning(f"Unsupported image format: {file_ext}")
            return False
        
        return True
    
    @timer_decorator
    def load_image(self, image_path: str) -> bool:
        """Load an image from local path with timing."""
        try:
            if not self._validate_image_path(image_path):
                return False
            
            self.image = cv2.imread(image_path)
            if self.image is not None:
                self.original_image = self.image.copy()
                self._save_metadata('file_load', {'path': image_path})
                return True
            else:
                logger.warning(f"Failed to load image: {image_path}")
                return False
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            return False
    
    def _get_image_from_user(self):
        """Ask user for image URL or local path and load it."""
        while True:
            image_source = input("Please provide an image URL or local file path: ").strip()
            
            if not image_source:
                print("Source cannot be empty. Please try again.")
                continue
            
            if self._load_image_source(image_source):
                break
            else:
                print("Failed to load image. Please check the source and try again.")
    
    def _check_image_loaded(self) -> bool:
        """Check if image is loaded and log warning if not."""
        if self.image is None:
            logger.warning("No image loaded. Please load an image first.")
            return False
        return True
    
    def _save_metadata(self, operation: str, details: Dict):
        """Save transformation metadata."""
        metadata = {
            'timestamp': time.time(),
            'operation': operation,
            'details': details,
            'image_shape': self.image.shape if self.image is not None else None
        }
        self.transformation_history.append(metadata)
    
    def store_image(self, name: str) -> bool:
        """Store the current image with a given name."""
        if not self._check_image_loaded():
            return False
        
        if not name or not isinstance(name, str):
            logger.warning("Image name must be a non-empty string")
            return False
        
        self.stored_images[name] = self.image.copy()
        self._save_metadata('store', {'name': name})
        logger.info(f"Stored image as '{name}'")
        return True
    
    def load_stored_image(self, name: str) -> bool:
        """Load a previously stored image by name."""
        if name not in self.stored_images:
            logger.warning(f"Stored image '{name}' not found")
            return False
        
        self.image = self.stored_images[name].copy()
        self._save_metadata('load_stored', {'name': name})
        return True
    
    def list_stored_images(self) -> List[str]:
        """Return list of stored image names."""
        return list(self.stored_images.keys())
    
    def remove_stored_image(self, name: str) -> bool:
        """Remove a stored image by name."""
        if name in self.stored_images:
            del self.stored_images[name]
            self._save_metadata('remove_stored', {'name': name})
            return True
        else:
            logger.warning(f"Stored image '{name}' not found")
            return False
    
    @timer_decorator
    def adjust_brightness(self, factor: float):
        """Adjust image brightness with timing."""
        if self._check_image_loaded():
            self.image = np.clip(self.image * factor, 0, 255).astype(np.uint8)
            self._save_metadata('brightness', {'factor': factor})
    
    @timer_decorator
    def adjust_contrast(self, factor: float):
        """Adjust image contrast with timing."""
        if self._check_image_loaded():
            mean = np.mean(self.image)
            self.image = np.clip((self.image - mean) * factor + mean, 0, 255).astype(np.uint8)
            self._save_metadata('contrast', {'factor': factor})
    
    @timer_decorator
    def apply_sepia(self):
        """Apply sepia filter with timing."""
        if self._check_image_loaded():
            sepia_matrix = np.array([
                [0.393, 0.769, 0.189],
                [0.349, 0.686, 0.168],
                [0.272, 0.534, 0.131]
            ])
            self.image = cv2.transform(self.image.astype(np.float32), sepia_matrix)
            self.image = np.clip(self.image, 0, 255).astype(np.uint8)
            self._save_metadata('sepia', {})
    
    @timer_decorator
    def to_grayscale(self):
        """Convert to grayscale with timing."""
        if self._check_image_loaded():
            gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            self.image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            self._save_metadata('grayscale', {})
    
    @timer_decorator
    def invert_colors(self):
        """Invert image colors with timing."""
        if self._check_image_loaded():
            self.image = 255 - self.image
            self._save_metadata('invert', {})
    
    def save_image(self, output_path: str) -> bool:
        """Save the current image."""
        if not self._check_image_loaded():
            return False
        
        try:
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            success = cv2.imwrite(output_path, self.image)
            if success:
                self._save_metadata('save', {'path': output_path})
                logger.info(f"Image saved successfully: {output_path}")
            return success
        except Exception as e:
            logger.error(f"Error saving image to {output_path}: {e}")
            return False
    
    def reset(self):
        """Reset to original image."""
        if self.original_image is not None:
            self.image = self.original_image.copy()
            self._save_metadata('reset', {})
        else:
            logger.warning("No original image available to reset to")
    
    def get_transformation_history(self) -> List[Dict]:
        """Get the transformation history."""
        return self.transformation_history.copy()
    
    def save_transformation_history(self, filename: str = 'transformation_history.json'):
        """Save transformation history to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(self.transformation_history, f, indent=2, default=str)
            logger.info(f"Transformation history saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving transformation history: {e}")
    
    def apply_multiple_transformations(self, transformations: List[Tuple[str, Dict]]):
        """Apply multiple transformations in sequence."""
        for transform_name, params in transformations:
            logger.info(f"Applying {transform_name} with params: {params}")
            
            if transform_name == 'brightness':
                self.adjust_brightness(params.get('factor', 1.0))
            elif transform_name == 'contrast':
                self.adjust_contrast(params.get('factor', 1.0))
            elif transform_name == 'sepia':
                self.apply_sepia()
            elif transform_name == 'grayscale':
                self.to_grayscale()
            elif transform_name == 'invert':
                self.invert_colors()
            else:
                logger.warning(f"Unknown transformation: {transform_name}")
    
    def get_image_info(self) -> Dict:
        """Get comprehensive image information."""
        if not self._check_image_loaded():
            return {}
        
        return {
            'shape': self.image.shape,
            'dtype': str(self.image.dtype),
            'channels': self.image.shape[2] if len(self.image.shape) > 2 else 1,
            'size': self.image.size,
            'min_value': float(np.min(self.image)),
            'max_value': float(np.max(self.image)),
            'mean_value': float(np.mean(self.image)),
            'stored_images_count': len(self.stored_images),
            'transformation_count': len(self.transformation_history)
        } 