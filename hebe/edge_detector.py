# edge_detector.py (NEW FILE for Step 4)
import cv2
import numpy as np

class EdgeDetector:
    def __init__(self):
        """
        Initializes the EdgeDetector. This module provides general edge detection capabilities.
        """
        print("Digital Makeup: EdgeDetector: Initialized.")

    def __enter__(self):
        """Context manager entry point."""
        print("Digital Makeup: EdgeDetector: Ready for use.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        print("Digital Makeup: EdgeDetector: Closed.")
        pass

    def extract_face_edges(self, image_bgr: cv2.Mat, face_points_list: list[list[tuple[int, int]]], edge_color: tuple[int, int, int] = (0, 255, 0)) -> cv2.Mat:
        """
        Extracts edges/features (like wrinkles) from the detected face regions in an image
        and returns them as a colored BGR image on a black background, ready for overlay.

        Args:
            image_bgr (cv2.Mat): The original BGR image.
            face_points_list (list[list[tuple[int, int]]]): A list of lists, where each inner list
                                                            contains (x, y) pixel coordinates
                                                            for all landmarks of a single detected face.
            edge_color (tuple[int, int, int]): The BGR color to draw the detected edges.

        Returns:
            cv2.Mat: A BGR image of the same size as image_bgr, with detected edges colored
                     on a black background. Returns a black image if no faces are detected.
        """
        # Create a black BGR canvas of the same size as the original image
        edges_output_frame = np.zeros_like(image_bgr, dtype=np.uint8) 
        
        if not face_points_list:
            return edges_output_frame # Return empty black image if no faces
        
        for face_points in face_points_list:
            if not face_points:
                continue

            # Calculate bounding box for the current face
            min_x = min(p[0] for p in face_points)
            max_x = max(p[0] for p in face_points)
            min_y = min(p[1] for p in face_points)
            max_y = max(0, min(p[1] for p in face_points)) # Ensure min_y is not negative
            
            # Add a small padding to the bounding box
            padding = 10
            min_x = max(0, min_x - padding)
            max_x = min(image_bgr.shape[1] - 1, max_x + padding)
            min_y = max(0, min_y - padding)
            max_y = min(image_bgr.shape[0] - 1, max_y + padding)

            # Crop the face region
            face_region = image_bgr[min_y:max_y, min_x:max_x]
            if face_region.shape[0] == 0 or face_region.shape[1] == 0:
                continue # Skip if region is empty

            # Convert to grayscale for edge detection
            face_region_gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)

            # Apply Canny edge detection
            edges = cv2.Canny(face_region_gray, 100, 200) # These thresholds can be fine-tuned

            # Create a BGR version of the edges, with the specified color
            colored_edges = np.zeros_like(face_region)
            colored_edges[edges > 0] = edge_color # Set desired color where edges are detected

            # Place the colored edges back onto the correct region of the final BGR output frame
            edges_output_frame[min_y:max_y, min_x:max_x] = colored_edges

        return edges_output_frame
    
    # You can add more general edge detection methods here later.