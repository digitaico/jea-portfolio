#!/usr/bin/env python3
"""
Tests for the image transformer.
"""

import pytest
import numpy as np
import cv2
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from image_transformer import ImageColorTransformer


class TestImageColorTransformer:
    """Test cases for ImageColorTransformer class."""
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        # Create a simple test image (100x100 RGB)
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        return image
    
    @pytest.fixture
    def temp_image_path(self, sample_image):
        """Create a temporary image file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            cv2.imwrite(f.name, sample_image)
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def transformer(self, temp_image_path):
        """Create ImageColorTransformer instance for testing."""
        return ImageColorTransformer(temp_image_path)
    
    def test_init_with_path(self, temp_image_path):
        """Test initialization with image path."""
        transformer = ImageColorTransformer(temp_image_path)
        assert transformer.image_path == temp_image_path
        assert transformer.image is not None
        assert transformer.original_image is not None
    
    def test_init_with_url(self):
        """Test initialization with URL."""
        # Mock URL loading
        with patch('image_transformer.ImageColorTransformer._load_image_from_url') as mock_load:
            mock_load.return_value = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            transformer = ImageColorTransformer("https://example.com/image.jpg")
            assert transformer.image_path == "https://example.com/image.jpg"
    
    def test_load_image(self, transformer, temp_image_path):
        """Test loading image from path."""
        # Reset transformer
        transformer.image = None
        transformer.original_image = None
        
        transformer.load_image(temp_image_path)
        assert transformer.image is not None
        assert transformer.original_image is not None
        assert transformer.image_path == temp_image_path
    
    def test_load_image_invalid_path(self, transformer):
        """Test loading image with invalid path."""
        with pytest.raises(ValueError):
            transformer.load_image("nonexistent_image.jpg")
    
    def test_reset_to_original(self, transformer):
        """Test resetting to original image."""
        # Modify the image
        original_image = transformer.image.copy()
        transformer.adjust_brightness(1.5)
        
        # Reset
        transformer.reset_to_original()
        assert np.array_equal(transformer.image, original_image)
    
    def test_adjust_brightness(self, transformer):
        """Test brightness adjustment."""
        original_image = transformer.image.copy()
        transformer.adjust_brightness(1.5)
        
        # Check that image has changed
        assert not np.array_equal(transformer.image, original_image)
        
        # Check that brightness increased
        assert np.mean(transformer.image) > np.mean(original_image)
    
    def test_adjust_contrast(self, transformer):
        """Test contrast adjustment."""
        original_image = transformer.image.copy()
        transformer.adjust_contrast(1.5)
        
        # Check that image has changed
        assert not np.array_equal(transformer.image, original_image)
    
    def test_adjust_saturation(self, transformer):
        """Test saturation adjustment."""
        original_image = transformer.image.copy()
        transformer.adjust_saturation(1.5)
        
        # Check that image has changed
        assert not np.array_equal(transformer.image, original_image)
    
    def test_shift_hue(self, transformer):
        """Test hue shifting."""
        original_image = transformer.image.copy()
        transformer.shift_hue(30)
        
        # Check that image has changed
        assert not np.array_equal(transformer.image, original_image)
    
    def test_apply_gamma_correction(self, transformer):
        """Test gamma correction."""
        original_image = transformer.image.copy()
        transformer.apply_gamma_correction(1.5)
        
        # Check that image has changed
        assert not np.array_equal(transformer.image, original_image)
    
    def test_apply_sepia_filter(self, transformer):
        """Test sepia filter application."""
        original_image = transformer.image.copy()
        transformer.apply_sepia()
        
        # Check that image has changed
        assert not np.array_equal(transformer.image, original_image)
    
    def test_apply_grayscale(self, transformer):
        """Test grayscale conversion."""
        original_image = transformer.image.copy()
        transformer.to_grayscale()
        
        # Check that image has changed
        assert not np.array_equal(transformer.image, original_image)
        
        # Check that it's grayscale (single channel or BGR with same values)
        if len(transformer.image.shape) == 3:
            # If still BGR, check that channels are similar (grayscale effect)
            b, g, r = cv2.split(transformer.image)
            assert np.allclose(b, g, atol=5)
            assert np.allclose(g, r, atol=5)
    
    def test_apply_invert(self, transformer):
        """Test color inversion."""
        original_image = transformer.image.copy()
        transformer.invert_colors()
        
        # Check that image has changed
        assert not np.array_equal(transformer.image, original_image)
        
        # Check that colors are inverted
        inverted_expected = 255 - original_image
        assert np.array_equal(transformer.image, inverted_expected)
    
    def test_apply_gaussian_blur(self, transformer):
        """Test Gaussian blur application."""
        original_image = transformer.image.copy()
        transformer.apply_gaussian_blur(5)
        
        # Check that image has changed
        assert not np.array_equal(transformer.image, original_image)
    
    def test_apply_gaussian_blur_invalid_kernel(self, transformer):
        """Test Gaussian blur with invalid kernel size."""
        with pytest.raises(ValueError):
            transformer.apply_gaussian_blur(4)  # Even number
    
    def test_save_image(self, transformer):
        """Test saving image."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            output_path = f.name
        
        try:
            transformer.save_image(output_path)
            assert os.path.exists(output_path)
            
            # Check that saved image can be loaded
            saved_image = cv2.imread(output_path)
            assert saved_image is not None
        finally:
            os.unlink(output_path)
    
    def test_get_image_info(self, transformer):
        """Test getting image information."""
        info = transformer.get_image_info()
        
        assert "shape" in info
        assert "dtype" in info
        assert "size" in info
        assert "channels" in info
        
        assert info["shape"] == transformer.image.shape
        assert info["dtype"] == str(transformer.image.dtype)
        assert info["channels"] == transformer.image.shape[2] if len(transformer.image.shape) == 3 else 1
    
    def test_store_and_load_stored_image(self, transformer):
        """Test storing and loading images."""
        # Store image
        image_id = "test_image_001"
        transformer.store_image(image_id)
        
        # Check that image is stored
        assert image_id in transformer.stored_images
        
        # Load stored image
        loaded_image = transformer.load_stored_image(image_id)
        assert loaded_image is not None
        assert np.array_equal(loaded_image, transformer.original_image)
    
    def test_list_stored_images(self, transformer):
        """Test listing stored images."""
        # Store some images
        transformer.store_image("test_001")
        transformer.store_image("test_002")
        
        stored_images = transformer.list_stored_images()
        assert "test_001" in stored_images
        assert "test_002" in stored_images
    
    def test_remove_stored_image(self, transformer):
        """Test removing stored image."""
        # Store image
        image_id = "test_image_001"
        transformer.store_image(image_id)
        assert image_id in transformer.stored_images
        
        # Remove image
        transformer.remove_stored_image(image_id)
        assert image_id not in transformer.stored_images
    
    @pytest.mark.skipif(not hasattr(cv2, 'GaussianBlur'), reason="OpenCV not available")
    def test_pillow_methods_available(self, transformer):
        """Test Pillow-based methods if available."""
        # Test if Pillow methods are available
        if hasattr(transformer, 'adjust_brightness_pillow'):
            original_image = transformer.image.copy()
            transformer.adjust_brightness_pillow(1.5)
            assert not np.array_equal(transformer.image, original_image)
    
    def test_validate_image_path(self, transformer):
        """Test image path validation."""
        # Valid path
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            valid_path = f.name
            os.unlink(valid_path)
        
        # Create a dummy file
        with open(valid_path, 'w') as f:
            f.write("dummy")
        
        try:
            # Should not raise exception for valid path
            transformer._validate_image_path(valid_path)
        finally:
            os.unlink(valid_path)
        
        # Invalid path should raise exception
        with pytest.raises(ValueError):
            transformer._validate_image_path("nonexistent.jpg")
    
    def test_check_image_loaded(self, transformer):
        """Test checking if image is loaded."""
        # Image is loaded
        transformer._check_image_loaded()
        
        # Image not loaded
        transformer.image = None
        with pytest.raises(ValueError):
            transformer._check_image_loaded()


class TestImageTransformerIntegration:
    """Integration tests for ImageColorTransformer."""
    
    @pytest.fixture
    def sample_image_path(self):
        """Create a sample image file for integration testing."""
        # Create a simple test image
        image = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            cv2.imwrite(f.name, image)
            yield f.name
        os.unlink(f.name)
    
    def test_full_workflow(self, sample_image_path):
        """Test complete image transformation workflow."""
        # Initialize transformer
        transformer = ImageColorTransformer(sample_image_path)
        
        # Apply multiple transformations
        transformer.adjust_brightness(1.2)
        transformer.adjust_contrast(1.3)
        transformer.apply_sepia()
        
        # Save transformed image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            output_path = f.name
        
        try:
            transformer.save_image(output_path)
            assert os.path.exists(output_path)
            
            # Load saved image and verify it's different from original
            saved_image = cv2.imread(output_path)
            original_image = cv2.imread(sample_image_path)
            
            assert not np.array_equal(saved_image, original_image)
        finally:
            os.unlink(output_path)
    
    def test_method_chaining(self, sample_image_path):
        """Test method chaining for transformations."""
        transformer = ImageColorTransformer(sample_image_path)
        
        # Chain multiple transformations
        transformer.adjust_brightness(1.2).adjust_contrast(1.3).apply_sepia()
        
        # Verify transformations were applied
        assert transformer.image is not None
        assert not np.array_equal(transformer.image, transformer.original_image)


if __name__ == "__main__":
    pytest.main([__file__])
