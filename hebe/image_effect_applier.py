import cv2
import numpy as np

class ImageEffectApplier:
    def __init__(self):
        print("ImageEffectApplier: Initialized.")

    def apply_gaussian_blur(self, image: np.ndarray, mask: np.ndarray, kernel_size: tuple = (45, 45), sigmaX: int = 0) -> np.ndarray:
        """
        Applies a Gaussian blur to parts of the image specified by the mask.

        Args:
            image (np.ndarray): The original image (BGR).
            mask (np.ndarray): A grayscale mask where non-zero values indicate areas to blur.
                               Should be 0-255 range (uint8) or 0.0-1.0 (float).
            kernel_size (tuple): Size of the Gaussian kernel (width, height).
            sigmaX (int): Gaussian kernel standard deviation in X direction.

        Returns:
            np.ndarray: The image with blur applied to masked regions.
        """
        # Ensure mask is of type uint8 and in range 0-255
        if mask.dtype == np.bool_:
            # Convert boolean mask to 0/255 uint8
            mask = mask.astype(np.uint8) * 255
        elif mask.dtype == np.float32 or mask.dtype == np.float64:
            # Assuming mask is normalized 0.0-1.0 if float, so scale to 0-255 and convert to uint8
            mask = (mask * 255).astype(np.uint8)
        elif mask.dtype != np.uint8:
            # For other integer types (e.g., int32), convert to uint8
            mask = mask.astype(np.uint8)

        # Create a blurred version of the original image
        blurred_image = cv2.GaussianBlur(image, kernel_size, sigmaX)

        # Ensure the mask has 3 channels to match the image for blending
        # The error occurred here because 'mask' (alpha) was CV_64F (float64)
        if mask.ndim == 2: # Check if it's a single-channel image
            mask_3_channel = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        else:
            # If the mask is already 3 channels (unlikely for a simple mask), use it directly
            mask_3_channel = mask 

        # Normalize the mask to 0.0-1.0 for alpha blending.
        # A value of 1.0 (255) in the mask means apply the blur (keep blurred_image).
        # A value of 0.0 (0) means keep the original_image.
        mask_normalized = mask_3_channel.astype(np.float32) / 255.0

        # Blend the original and blurred images using the mask
        # output = (blurred_image * mask_normalized) + (original_image * (1 - mask_normalized))
        output_image = (blurred_image * mask_normalized + image * (1 - mask_normalized)).astype(np.uint8)

        return output_image