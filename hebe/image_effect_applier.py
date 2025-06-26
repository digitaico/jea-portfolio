# image_effect_applier.py
import cv2
import numpy as np

class ImageEffectApplier:
    def __init__(self):
        """
        Initializes the ImageEffectApplier.
        """
        print("ImageEffectApplier: Initialized.")

    def apply_gaussian_blur(self, image: np.ndarray, mask: np.ndarray, kernel_size: tuple = (45, 45), sigmaX: float = 0) -> np.ndarray:
        """
        Applies a Gaussian blur to specific regions of an image defined by a mask.

        Args:
            image (np.ndarray): The original input image (BGR).
            mask (np.ndarray): A grayscale binary mask (0 or 255) of the same height/width as the image,
                               where 255 indicates areas to blur.
            kernel_size (tuple): The size of the Gaussian kernel (width, height). Must be odd and positive.
            sigmaX (float): Gaussian kernel standard deviation in X direction. If 0, it is calculated from kernel size.

        Returns:
            np.ndarray: The image with the specified areas blurred.
        """
        if image.shape[:2] != mask.shape:
            raise ValueError("Image and mask must have the same height and width.")
        
        # Ensure mask is 1-channel grayscale if it somehow came as 3 channels
        if len(mask.shape) == 3:
             mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

        # Ensure mask values are between 0 and 255
        mask = np.clip(mask, 0, 255).astype(np.uint8)

        # Apply Gaussian blur to the entire image
        blurred_image = cv2.GaussianBlur(image, kernel_size, sigmaX)

        # Blend the original image and the blurred image using the mask
        # Create a float mask for blending (0.0 to 1.0)
        alpha = mask.astype(float) / 255.0
        alpha = cv2.cvtColor(alpha, cv2.COLOR_GRAY2BGR) # Convert to 3 channels to match image

        # Blend using alpha composition: blurred_image * alpha + original_image * (1 - alpha)
        # This will apply the blur gradually on the mask edges if the mask itself was blurred
        blended_image = (blurred_image * alpha + image * (1 - alpha)).astype(np.uint8)

        return blended_image

# Example Usage (for independent testing of this module)
if __name__ == "__main__":
    print("--- Image Effect Applier Test ---")

    # Create a dummy image
    dummy_image = np.zeros((300, 400, 3), dtype=np.uint8)
    cv2.rectangle(dummy_image, (50, 50), (350, 250), (0, 255, 0), -1) # Green rectangle
    cv2.putText(dummy_image, "Original", (150, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Create a dummy mask (blur a circle in the middle)
    mask = np.zeros((300, 400), dtype=np.uint8)
    cv2.circle(mask, (200, 150), 80, 255, -1) # White circle in mask

    applier = ImageEffectApplier()
    blurred_image = applier.apply_gaussian_blur(dummy_image, mask, kernel_size=(35, 35))

    cv2.imshow('Original Image', dummy_image)
    cv2.imshow('Mask', mask)
    cv2.imshow('Blurred Region', blurred_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print("--- Image Effect Applier Test Finished ---")