# nasolabial_mask_generator.py
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2
from skimage.feature import hessian_matrix, hessian_matrix_eigvals # NEW IMPORTS

class NasolabialMaskGenerator:
    def __init__(self):
        """
        Initializes the NasolabialMaskGenerator.
        Defines the landmark indices relevant to the nasolabial fold areas and parameters for line detection.
        """
        # Monolith specific nasolabial landmark indices (critical for target area)
        # These are the exact indices used in your working monolith's `process_roi_and_mask`
        self.right_nasolabial_indices = sorted(list(set([64, 49, 131, 36, 203, 206, 205, 207, 212, 216])))
        self.left_nasolabial_indices = sorted(list(set([371, 279, 266, 423, 425, 426, 427, 436, 432])))
        
        # Parameters for Hessian-based line detection (matching monolith)
        self.sigma_val = 1.5
        self.min_contour_area = 15
        self.padding = 1
        self.kernel_morphology = np.ones((7,7), np.uint8) # For morphological closing

        print("NasolabialMaskGenerator: Initialized.")

    def _get_coords(self, landmark, img_w, img_h):
        """Helper to convert normalized landmark coordinates to pixel coordinates."""
        x = int(landmark.x * img_w)
        y = int(landmark.y * img_h)
        return x, y

    def _process_roi_and_generate_line_mask(self, gray_frame: np.ndarray, landmarks_px: np.ndarray,
                                             indices: list, img_w: int, img_h: int) -> np.ndarray:
        """
        Processes a region of interest defined by landmarks to generate a mask of detected lines (wrinkles).
        Adapted from the monolith's `process_roi_and_mask`.
        """
        roi_points = np.array([landmarks_px[i] for i in indices if i < len(landmarks_px)], dtype=np.int32)
        
        if len(roi_points) < 3: # Need at least 3 points to form a polygon
            return np.zeros_like(gray_frame, dtype=np.uint8) 

        # Calculate bounding rectangle of the ROI
        x_base, y_base, w_base, h_base = cv2.boundingRect(roi_points)
        
        # Add padding and ensure coordinates are within image bounds
        x1 = max(0, x_base - self.padding)
        y1 = max(0, y_base - self.padding)
        x2 = min(img_w, x_base + w_base + self.padding)
        y2 = min(img_h, h_base + y_base + self.padding) 

        w_final = x2 - x1
        h_final = y2 - y1

        if w_final <= 0 or h_final <= 0:
            return np.zeros_like(gray_frame, dtype=np.uint8)
        
        # Create a mask for the convex polygon area of the ROI points
        mask_poly = np.zeros((img_h, img_w), dtype=np.uint8)
        # Use convex hull for the polygon area
        cv2.fillPoly(mask_poly, [cv2.convexHull(roi_points)], 255)

        # Apply the polygon mask to the grayscale frame
        masked_region_full = cv2.bitwise_and(gray_frame, gray_frame, mask=mask_poly)
        roi_cropped = masked_region_full[y1:y2, x1:x2] # Crop to the actual ROI for Hessian calculations

        if roi_cropped.shape[0] == 0 or roi_cropped.shape[1] == 0:
            return np.zeros_like(gray_frame, dtype=np.uint8)

        # Hessian Matrix calculations for line detection
        # Ensure roi_cropped is float for skimage
        # The `sigma_val` controls the scale of features detected (e.g., wider vs finer lines)
        H_elems = hessian_matrix(roi_cropped.astype(float), sigma=self.sigma_val)
        _, eigenvalues = hessian_matrix_eigvals(H_elems)
        
        # Detect wrinkles where eigenvalues are negative (dark lines/ridges)
        # This creates a binary mask of detected lines
        wrinkles_mask_region = (eigenvalues < 0).astype(np.uint8) * 255 

        current_region_line_mask = np.zeros_like(gray_frame, dtype=np.uint8)

        # Find contours of the detected wrinkles within the cropped ROI
        contours, _ = cv2.findContours(wrinkles_mask_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            # Filter by minimum contour area to remove noise
            if cv2.contourArea(contour) > self.min_contour_area:
                # Offset the contour back to the full frame coordinates
                contour_offset = contour + (x1, y1) 
                cv2.drawContours(current_region_line_mask, [contour_offset], -1, 255, -1) 

        # Apply morphological closing to refine the line mask (fill small gaps, connect nearby lines)
        current_region_line_mask = cv2.morphologyEx(current_region_line_mask, cv2.MORPH_CLOSE, self.kernel_morphology, iterations=3) 

        return current_region_line_mask


    def generate_mask(self, image: np.ndarray, face_landmarks: landmark_pb2.NormalizedLandmarkList) -> np.ndarray:
        """
        Generates a binary mask for the nasolabial fold lines, using Hessian matrix-based detection.

        Args:
            image (np.ndarray): The original input image (BGR).
            face_landmarks (mediapipe.framework.formats.landmark_pb2.NormalizedLandmarkList):
                The detected face landmarks from MediaPipe.

        Returns:
            np.ndarray: A binary mask (255 for lines area, 0 otherwise) of the same shape
                        as the input image, with the nasolabial line regions marked.
        """
        img_h, img_w, _ = image.shape
        full_nasolabial_line_mask = np.zeros((img_h, img_w), dtype=np.uint8)

        # Convert original image to grayscale for line detection
        gray_frame = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Convert normalized landmarks to pixel coordinates
        landmarks_px = []
        # Ensure we don't try to access landmarks beyond the list's bounds (if less than 468 landmarks are returned for some reason)
        max_landmark_idx = max(self.right_nasolabial_indices + self.left_nasolabial_indices)
        if len(face_landmarks.landmark) <= max_landmark_idx:
             # If not enough landmarks, return an empty mask as we can't define the ROI
             print("NasolabialMaskGenerator: Warning: Not enough landmarks detected to form nasolabial regions. Returning empty mask.")
             return full_nasolabial_line_mask


        for lm in face_landmarks.landmark:
            x, y = self._get_coords(lm, img_w, img_h)
            landmarks_px.append((x, y))
        landmarks_px = np.array(landmarks_px)


        # Generate mask for Right Nasolabial Fold
        current_right_mask = self._process_roi_and_generate_line_mask(
            gray_frame, landmarks_px, self.right_nasolabial_indices, img_w, img_h
        )
        if current_right_mask is not None:
            full_nasolabial_line_mask = cv2.bitwise_or(full_nasolabial_line_mask, current_right_mask)

        # Generate mask for Left Nasolabial Fold
        current_left_mask = self._process_roi_and_generate_line_mask(
            gray_frame, landmarks_px, self.left_nasolabial_indices, img_w, img_h
        )
        if current_left_mask is not None:
            full_nasolabial_line_mask = cv2.bitwise_or(full_nasolabial_line_mask, current_left_mask)
        
        # Monolith had an additional blur on the mask itself, which can help smooth the blend
        full_nasolabial_line_mask = cv2.GaussianBlur(full_nasolabial_line_mask, (5, 5), 0) # Small blur on the final mask


        return full_nasolabial_line_mask

# Example Usage (for independent testing of this module) - This test is now more meaningful
if __name__ == "__main__":
    print("--- Nasolabial Mask Generator Test with Hessian Logic (Requires `skimage`) ---")
    print("Please ensure you have `scikit-image` installed: `pip install scikit-image`")

    # Create a dummy image simulating a face with some synthetic lines
    dummy_height, dummy_width = 480, 640
    test_image = np.zeros((dummy_height, dummy_width, 3), dtype=np.uint8)
    
    # Draw a rough face shape
    cv2.ellipse(test_image, (dummy_width//2, dummy_height//2), (int(dummy_width*0.3), int(dummy_height*0.4)), 0, 0, 360, (50,50,50), -1)
    
    # Simulate nasolabial lines with white lines
    cv2.line(test_image, (int(dummy_width*0.4), int(dummy_height*0.5)), (int(dummy_width*0.45), int(dummy_height*0.65)), (200,200,200), 2)
    cv2.line(test_image, (int(dummy_width*0.6), int(dummy_height*0.5)), (int(dummy_width*0.55), int(dummy_height*0.65)), (200,200,200), 2)
    
    # Add some noise to make Hessian more interesting
    noise = np.random.randint(-10, 10, test_image.shape, dtype=np.int16)
    test_image = np.clip(test_image.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Simulate MediaPipe face_landmarks
    class MockLandmark:
        def __init__(self, x, y, z=0.0):
            self.x = x
            self.y = y
            self.z = z

    class MockFaceLandmarks:
        def __init__(self, landmarks_list):
            self.landmark = landmarks_list

    mock_all_landmarks = [MockLandmark(0,0)] * 468 # Initialize with dummy landmarks

    # Manually set some key landmark positions for a basic test,
    # mapping roughly to the indices used for nasolabial folds
    # These are normalized coordinates (0.0 to 1.0)
    # Right fold (viewer's left side of face)
    mock_all_landmarks[64] = MockLandmark(0.40, 0.48) 
    mock_all_landmarks[49] = MockLandmark(0.42, 0.53)
    mock_all_landmarks[131] = MockLandmark(0.44, 0.58)
    mock_all_landmarks[36] = MockLandmark(0.46, 0.63)
    mock_all_landmarks[203] = MockLandmark(0.38, 0.50)
    mock_all_landmarks[206] = MockLandmark(0.40, 0.55)
    mock_all_landmarks[205] = MockLandmark(0.42, 0.60)
    mock_all_landmarks[207] = MockLandmark(0.44, 0.65)
    mock_all_landmarks[212] = MockLandmark(0.48, 0.68)
    mock_all_landmarks[216] = MockLandmark(0.50, 0.70)

    # Left fold (viewer's right side of face)
    mock_all_landmarks[371] = MockLandmark(0.60, 0.48)
    mock_all_landmarks[279] = MockLandmark(0.58, 0.53)
    mock_all_landmarks[266] = MockLandmark(0.56, 0.58)
    mock_all_landmarks[423] = MockLandmark(0.54, 0.63)
    mock_all_landmarks[425] = MockLandmark(0.62, 0.50)
    mock_all_landmarks[426] = MockLandmark(0.60, 0.55)
    mock_all_landmarks[427] = MockLandmark(0.58, 0.60)
    mock_all_landmarks[436] = MockLandmark(0.56, 0.65)
    mock_all_landmarks[432] = MockLandmark(0.52, 0.68)

    mock_face_landmarks = MockFaceLandmarks(mock_all_landmarks)

    mask_generator = NasolabialMaskGenerator()
    
    # Call generate_mask with the actual test_image
    nasolabial_mask = mask_generator.generate_mask(test_image, mock_face_landmarks)

    # Display results
    cv2.imshow('Original Test Image', test_image)
    cv2.imshow('Detected Nasolabial Lines Mask', nasolabial_mask)
    
    # Apply a blur to the original image using the generated mask for visual confirmation
    blurred_test_image = cv2.GaussianBlur(test_image, (35,35), 0)
    final_blended_image = (blurred_test_image.astype(float) * (nasolabial_mask.astype(float)/255.0)[:,:,np.newaxis] + \
                           test_image.astype(float) * (1 - (nasolabial_mask.astype(float)/255.0)[:,:,np.newaxis])).astype(np.uint8)
    cv2.imshow('Blended Output', final_blended_image)

    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print("--- Mask Generator Test Finished ---")