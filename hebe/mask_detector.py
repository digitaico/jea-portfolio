# mask_detector.py (UPDATED: create_nasolabial_mask for multiple faces)
import cv2
import numpy as np
import mediapipe as mp 

class MaskDetector:
    def __init__(self):
        """
        Initializes the MaskDetector. This module is responsible for generating binary masks
        of detected human faces based on landmark data, and now specific feature masks.
        """
        print("Digital Makeup: MaskDetector: Initialized.")

    def __enter__(self):
        """Context manager entry point."""
        print("Digital Makeup: MaskDetector: Ready for use.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        print("Digital Makeup: MaskDetector: Closed.")
        pass

    def create_face_mask(self, image_shape: tuple[int, int, int], face_points_list: list[list[tuple[int, int]]]) -> cv2.Mat:
        """
        Creates a binary mask for each detected face. The mask is white where the face is,
        and black elsewhere. For multiple faces, the mask will combine all face areas.

        Args:
            image_shape (tuple[int, int, int]): The shape (height, width, channels) of the original image.
            face_points_list (list[list[tuple[int, int]]]): A list of lists, where each inner list
                                                            contains (x, y) pixel coordinates
                                                            for all landmarks of a single detected face.

        Returns:
            cv2.Mat: A grayscale binary mask (np.uint8, 0 or 255) of the same height and width as the original image.
        """
        h, w, _ = image_shape
        # Create an empty black mask
        mask = np.zeros((h, w), dtype=np.uint8)

        if not face_points_list:
            return mask 

        for face_points in face_points_list:
            if not face_points:
                continue

            points_np = np.array(face_points, dtype=np.int32)
            hull = cv2.convexHull(points_np)
            cv2.fillPoly(mask, [hull], 255) 

        return mask

    def create_edge_roi_mask(self, image_shape: tuple[int, int, int], 
                             face_edges_visual: cv2.Mat, 
                             dilation_kernel_size: int = 3,
                             apply_general_face_mask: cv2.Mat | None = None) -> cv2.Mat:
        """
        Creates a binary mask defining ROIs around general detected edges (e.g., wrinkles).

        Args:
            image_shape (tuple[int, int, int]): The shape (height, width, channels) of the original image.
            face_edges_visual (cv2.Mat): The BGR image with colored edges (from EdgeDetector), rest is black.
            dilation_kernel_size (int): Size of the kernel for dilation. Larger values expand the ROI more.
            apply_general_face_mask (cv2.Mat | None): An optional general face mask (binary) to
                                                       confine the edge ROIs strictly to the face.

        Returns:
            cv2.Mat: A grayscale binary mask (np.uint8, 0 or 255) where white pixels define the
                     areas around edges.
        """
        h, w, _ = image_shape
        edge_roi_mask = np.zeros((h, w), dtype=np.uint8)

        if face_edges_visual is None or np.all(face_edges_visual == 0):
            return edge_roi_mask 

        gray_edges = cv2.cvtColor(face_edges_visual, cv2.COLOR_BGR2GRAY)
        _, binary_edges = cv2.threshold(gray_edges, 1, 255, cv2.THRESH_BINARY)

        kernel = np.ones((dilation_kernel_size, dilation_kernel_size), np.uint8)
        dilated_edges = cv2.dilate(binary_edges, kernel, iterations=1)

        if apply_general_face_mask is not None:
            edge_roi_mask = cv2.bitwise_and(dilated_edges, dilated_edges, mask=apply_general_face_mask)
        else:
            edge_roi_mask = dilated_edges

        return edge_roi_mask

    def create_nasolabial_mask(self, 
                               image_shape: tuple[int, int, int], 
                               all_faces_points: list[list[tuple[int, int]]], # Now accepts list of lists
                               dilation_kernel_size: int = 3, 
                               apply_general_face_mask: cv2.Mat | None = None) -> cv2.Mat:
        """
        Creates a binary mask for the nasolabial fold regions using specific MediaPipe landmarks.
        Handles multiple faces.

        Args:
            image_shape (tuple[int, int, int]): The shape (height, width, channels) of the original image.
            all_faces_points (list[list[tuple[int, int]]]): A list of lists, where each inner list
                                                            contains (x, y) pixel coordinates
                                                            for all landmarks of a single detected face.
            dilation_kernel_size (int): Size of the kernel for dilation to thicken the lines.
            apply_general_face_mask (cv2.Mat | None): An optional general face mask (binary) to
                                                       confine the nasolabial ROIs strictly to the face.

        Returns:
            cv2.Mat: A grayscale binary mask (np.uint8, 0 or 255) for nasolabial folds.
        """
        h, w, _ = image_shape
        combined_nasolabial_mask = np.zeros((h, w), dtype=np.uint8)

        if not all_faces_points:
            return combined_nasolabial_mask # Return empty if no faces

        # Define MediaPipe indices for approximate nasolabial fold paths (left and right)
        # These are empirical and can be fine-tuned based on visual inspection.
        nasolabial_paths_indices = [
            # Right fold (viewer's left side of face) - approximate path
            [203,206,216,212,186,92,64,129], 
            # Left fold (viewer's right side of face) - approximate path
            [294,423,426,436,287,410,294,478],     
        ]
        
        for face_points in all_faces_points:
            if not face_points:
                continue # Skip if an individual face has no points

            current_face_mask = np.zeros((h, w), dtype=np.uint8) # Mask for current face's nasolabial lines
            points_np = np.array(face_points, dtype=np.int32)

            for path_indices in nasolabial_paths_indices:
                current_path_points = [points_np[idx] for idx in path_indices if idx < len(points_np)]
                
                if len(current_path_points) > 1: # Need at least 2 points for a line
                    temp_mask_for_line = np.zeros((h, w), dtype=np.uint8)
                    cv2.polylines(temp_mask_for_line, [np.array(current_path_points)], isClosed=False, color=255, thickness=1)

                    kernel = np.ones((dilation_kernel_size, dilation_kernel_size), np.uint8)
                    dilated_line = cv2.dilate(temp_mask_for_line, kernel, iterations=1)
                    
                    current_face_mask = cv2.bitwise_or(current_face_mask, dilated_line)
            
            # Combine individual face nasolabial masks into the overall mask
            combined_nasolabial_mask = cv2.bitwise_or(combined_nasolabial_mask, current_face_mask)

        # Apply the general face mask to ensure ROIs are confined to the face
        if apply_general_face_mask is not None:
            combined_nasolabial_mask = cv2.bitwise_and(combined_nasolabial_mask, combined_nasolabial_mask, mask=apply_general_face_mask)

        return combined_nasolabial_mask