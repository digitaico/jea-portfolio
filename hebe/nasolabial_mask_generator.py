# nasolabial_mask_generator.py
import cv2
import numpy as np
import mediapipe as mp # To access landmark definitions

# NEW IMPORT: Import the specific protobuf type for NormalizedLandmarkList
from mediapipe.framework.formats import landmark_pb2

class NasolabialMaskGenerator:
    def __init__(self):
        """
        Initializes the NasolabialMaskGenerator.
        Defines the landmark indices relevant to the nasolabial fold areas.
        """
        # These landmark indices are approximate for the nasolabial fold region.
        # You might need to fine-tune them based on visual inspection and desired smoothing area.
        # MediaPipe Face Mesh has 468 landmarks (0-467).
        # We'll define points for the left and right nasolabial folds.

        # Left Nasolabial Fold (viewer's right, subject's left)
        # From side of nose down to mouth corner/chin area
        self.left_fold_indices = [
            161, 163, 162, 174, # Roughly outlining the left side of the nose/upper cheek
            200, 201, 196,     # Inner cheek/under eye towards nose
            41, 45, 273, 274, 275, # Upper lip corner surrounding area (adjust as needed)
            291, # Mouth corner (left)
            397, 398, 399, 400, # Lower cheek/jawline (to make a closed region)
            322, 323, 365, 366 # Around mouth corner for a more complete fold area
        ]
        
        # Right Nasolabial Fold (viewer's left, subject's right)
        self.right_fold_indices = [
            390, 392, 389, 403, # Roughly outlining the right side of the nose/upper cheek
            420, 421, 417,     # Inner cheek/under eye towards nose
            295, 299, 49, 50, 51, # Upper lip corner surrounding area (adjust as needed)
            61, # Mouth corner (right)
            171, 172, 173, 174, # Lower cheek/jawline (to make a closed region)
            93, 94, 95, 96 # Around mouth corner for a more complete fold area
        ]

        # Combine for easier processing
        self.all_fold_indices = self.left_fold_indices + self.right_fold_indices
        print("NasolabialMaskGenerator: Initialized.")

    # MODIFIED LINE: Use landmark_pb2.NormalizedLandmarkList for type hinting
    def generate_mask(self, image_shape: tuple, face_landmarks: landmark_pb2.NormalizedLandmarkList) -> np.ndarray:
        """
        Generates a binary mask for the nasolabial fold areas.

        Args:
            image_shape (tuple): The shape of the original image (height, width, channels).
            face_landmarks (mediapipe.framework.formats.landmark_pb2.NormalizedLandmarkList):
                The detected face landmarks from MediaPipe.

        Returns:
            np.ndarray: A binary mask (255 for mask area, 0 otherwise) of the same shape
                        as the input image, with the nasolabial fold regions marked.
        """
        mask = np.zeros(image_shape[:2], dtype=np.uint8) # Create a black mask (height x width)

        # Helper function to get landmark coordinates in pixel values
        def _get_coords(idx):
            landmark = face_landmarks.landmark[idx]
            x = int(landmark.x * image_shape[1])
            y = int(landmark.y * image_shape[0])
            return x, y

        # Process each fold area separately to create polygons
        # Left Fold
        left_points = np.array([_get_coords(idx) for idx in self.left_fold_indices], dtype=np.int32)
        if len(left_points) >= 3: # Need at least 3 points for a polygon
            hull_left = cv2.convexHull(left_points) # Get the convex hull to form a closed shape
            cv2.fillConvexPoly(mask, hull_left, 255) # Fill the polygon with white (255)

        # Right Fold
        right_points = np.array([_get_coords(idx) for idx in self.right_fold_indices], dtype=np.int32)
        if len(right_points) >= 3:
            hull_right = cv2.convexHull(right_points)
            cv2.fillConvexPoly(mask, hull_right, 255)

        # You might want to apply a slight blur to the mask edges to avoid harsh transitions
        # This will make the smoothing effect blend more naturally.
        mask = cv2.GaussianBlur(mask, (21, 21), 0) # Apply blur to the mask itself
        mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)[1] # Re-binarize after blur if desired, or keep it grayscale for alpha blending

        return mask

# Example Usage (for independent testing of this module)
if __name__ == "__main__":
    print("--- Nasolabial Mask Generator Test ---")
    print("This test generates a sample mask on a dummy image.")

    # Create a dummy image (e.g., black with a white circle for "face")
    dummy_height, dummy_width = 480, 640
    dummy_image = np.zeros((dummy_height, dummy_width, 3), dtype=np.uint8)
    cv2.circle(dummy_image, (dummy_width // 2, dummy_height // 2), 150, (0, 255, 0), -1) # Green circle

    # Simulate MediaPipe face_landmarks (very simplified for a dummy test)
    # In a real scenario, these would come from FaceMeshProcessor
    class MockLandmark:
        def __init__(self, x, y, z=0.0):
            self.x = x
            self.y = y
            self.z = z

    class MockFaceLandmarks:
        def __init__(self, landmarks_list):
            self.landmark = landmarks_list

    # Define some dummy landmarks approximating a face for the mock data structure
    mock_all_landmarks = [MockLandmark(0,0)] * 468 # Initialize with dummy landmarks

    # Manually set some key landmark positions for a basic test,
    # mapping roughly to the indices used for nasolabial folds
    # These are normalized coordinates (0.0 to 1.0)
    mock_all_landmarks[161] = MockLandmark(0.40, 0.45) # Nose left
    mock_all_landmarks[163] = MockLandmark(0.41, 0.48)
    mock_all_landmarks[162] = MockLandmark(0.42, 0.50)
    mock_all_landmarks[174] = MockLandmark(0.45, 0.53) # Below nose
    mock_all_landmarks[200] = MockLandmark(0.38, 0.50) # Cheek inner left
    mock_all_landmarks[201] = MockLandmark(0.39, 0.52)
    mock_all_landmarks[196] = MockLandmark(0.37, 0.47)
    mock_all_landmarks[291] = MockLandmark(0.40, 0.58) # Mouth corner left
    mock_all_landmarks[397] = MockLandmark(0.35, 0.60) # Lower cheek left
    mock_all_landmarks[398] = MockLandmark(0.36, 0.62)
    mock_all_landmarks[399] = MockLandmark(0.38, 0.64)
    mock_all_landmarks[400] = MockLandmark(0.39, 0.65)

    mock_all_landmarks[390] = MockLandmark(0.60, 0.45) # Nose right
    mock_all_landmarks[392] = MockLandmark(0.59, 0.48)
    mock_all_landmarks[389] = MockLandmark(0.58, 0.50)
    mock_all_landmarks[403] = MockLandmark(0.55, 0.53) # Below nose
    mock_all_landmarks[420] = MockLandmark(0.62, 0.50) # Cheek inner right
    mock_all_landmarks[421] = MockLandmark(0.61, 0.52)
    mock_all_landmarks[417] = MockLandmark(0.63, 0.47)
    mock_all_landmarks[61] = MockLandmark(0.60, 0.58) # Mouth corner right
    mock_all_landmarks[171] = MockLandmark(0.65, 0.60) # Lower cheek right
    mock_all_landmarks[172] = MockLandmark(0.64, 0.62)
    mock_all_landmarks[173] = MockLandmark(0.62, 0.64)
    mock_all_landmarks[174] = MockLandmark(0.61, 0.65)

    mock_face_landmarks = MockFaceLandmarks(mock_all_landmarks)

    mask_generator = NasolabialMaskGenerator()
    mask = mask_generator.generate_mask(dummy_image.shape, mock_face_landmarks)

    # Display the mask
    cv2.imshow('Generated Nasolabial Mask', mask)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print("--- Mask Generator Test Finished ---")