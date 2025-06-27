# digital_filters.py (UPDATED: Removed default kernel_size and alpha from signature)
import cv2
import numpy as np

class DigitalFilters:
    def __init__(self):
        """
        Initializes the DigitalFilters module. This module is responsible for applying
        various digital image processing effects, often guided by masks.
        """
        print("Digital Makeup: DigitalFilters: Initialized.")

    def __enter__(self):
        """Context manager entry point."""
        print("Digital Makeup: DigitalFilters: Ready to apply effects.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        print("Digital Makeup: DigitalFilters: Finished applying effects.")
        pass

    def apply_targeted_blur(self, 
                            image: cv2.Mat, 
                            target_mask: cv2.Mat, 
                            kernel_size: tuple[int, int], # NO DEFAULT HERE
                            alpha: float) -> cv2.Mat:    # NO DEFAULT HERE
        """
        Applies a Gaussian blur to specific regions of an image defined by a binary mask.
        The effect is blended with the original image for a natural look.

        Args:
            image (cv2.Mat): The original BGR image.
            target_mask (cv2.Mat): A grayscale binary mask (0 or 255) where 255 indicates areas
                                    to be blurred.
            kernel_size (tuple[int, int]): The size of the Gaussian blur kernel (width, height).
                                           Should be odd and positive.
            alpha (float): The blending factor for the blur effect (0.0 to 1.0).
                           0.0 means no blur (original image), 1.0 means full blur.

        Returns:
            cv2.Mat: The image with the targeted blur applied.
        """
        if target_mask is None or np.all(target_mask == 0):
            return image

        # Ensure kernel size is odd and at least 3x3
        if kernel_size[0] % 2 == 0: kernel_size = (kernel_size[0] + 1, kernel_size[1])
        if kernel_size[1] % 2 == 0: kernel_size = (kernel_size[0], kernel_size[1] + 1)
        
        if kernel_size[0] < 3: kernel_size = (3, kernel_size[1])
        if kernel_size[1] < 3: kernel_size = (kernel_size[0], 3)

        # 1. Create a blurred version of the entire image
        blurred_full_image = cv2.GaussianBlur(image, kernel_size, 0)

        # Ensure the mask is 3-channel if the image is BGR
        mask_3_channel = cv2.merge([target_mask, target_mask, target_mask])
        
        # 2. Extract the blurred region using the mask
        blurred_region = cv2.bitwise_and(blurred_full_image, mask_3_channel)
        
        # 3. Extract the non-blurred region from the original image
        inverse_mask_3_channel = cv2.bitwise_not(mask_3_channel) 
        original_non_blurred_region = cv2.bitwise_and(image, inverse_mask_3_channel)

        # 4. Combine the non-blurred original parts and the blurred parts
        combined_image = cv2.bitwise_or(original_non_blurred_region, blurred_region)

        # 5. Apply blending if alpha < 1.0
        if alpha < 1.0:
            output_image = cv2.addWeighted(image, 1.0 - alpha, combined_image, alpha, 0)
            return output_image
        else:
            # If alpha is 1.0, return the fully combined (blurred where masked) image directly
            return combined_image