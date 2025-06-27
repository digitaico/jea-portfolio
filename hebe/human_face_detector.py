# human_face_detector.py (RENAMED from face_detector.py and CORRECTED)
import mediapipe as mp
import cv2
import sys
import numpy as np
from typing import Any # Corrected import for MediaPipe results type hinting

class HumanFaceDetector: # Renamed class
    def __init__(self, static_image_mode: bool = False, max_num_faces: int = 1,
                 min_detection_confidence: float = 0.5, min_tracking_confidence: float = 0.5):
        """
        Initializes the HumanFaceDetector for the Digital Makeup application using MediaPipe Face Mesh.
        This module is responsible for detecting human faces and extracting their raw landmark data.
        """
        self.static_image_mode = static_image_mode
        self.max_num_faces = max_num_faces
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh_model = None 

        print("Digital Makeup: HumanFaceDetector: Initializing MediaPipe Face Mesh.")

    def __enter__(self):
        """
        Context manager entry point: Initializes the MediaPipe Face Mesh model.
        """
        print("Digital Makeup: HumanFaceDetector: Loading Face Mesh model...")
        self.face_mesh_model = self.mp_face_mesh.FaceMesh(
            static_image_mode=self.static_image_mode,
            max_num_faces=self.max_num_faces,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )
        print("Digital Makeup: HumanFaceDetector: Face Mesh model loaded successfully.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point: Releases MediaPipe Face Mesh resources.
        """
        if self.face_mesh_model:
            print("Digital Makeup: HumanFaceDetector: Closing Face Mesh model.")
            self.face_mesh_model.close()
        self.face_mesh_model = None

    def process_frame(self, image_bgr: cv2.Mat) -> tuple[Any | None, cv2.Mat, list, list]: # Corrected type hint
        """
        Processes a single BGR image frame to detect human face landmarks and extract raw drawing data.

        Args:
            image_bgr (cv2.Mat): The input image frame in BGR format (from OpenCV).

        Returns:
            tuple[Any | None, cv2.Mat, list[list[tuple[int, int]]], list[list[tuple[tuple[int, int], tuple[int, int]]]]]:
                A tuple containing:
                1. The MediaPipe results object (type Any | None if no faces detected).
                2. The original image.
                3. A list of lists, where each inner list contains (x, y) pixel coordinates
                   for all landmarks of a single detected face.
                4. A list of lists, where each inner list contains ((x1, y1), (x2, y2))
                   pixel line segments for the tessellation and contours of a single face.
        """
        if self.face_mesh_model is None:
            raise RuntimeError("Digital Makeup: HumanFaceDetector: Face Mesh model not initialized. Call __enter__ first.")

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        results = self.face_mesh_model.process(image_rgb)
        
        h, w, _ = image_bgr.shape
        
        all_faces_points = [] 
        all_faces_lines = []  

        if results and results.multi_face_landmarks: # Added 'results and' check for robustness
            for face_landmarks in results.multi_face_landmarks:
                current_face_points = []
                for landmark in face_landmarks.landmark:
                    cx, cy = int(landmark.x * w), int(landmark.y * h)
                    current_face_points.append((cx, cy))
                all_faces_points.append(current_face_points)

                current_face_lines = []
                for connection in self.mp_face_mesh.FACEMESH_TESSELATION:
                    start_idx = connection[0]
                    end_idx = connection[1]
                    if start_idx < len(current_face_points) and end_idx < len(current_face_points):
                        pt1 = current_face_points[start_idx]
                        pt2 = current_face_points[end_idx]
                        current_face_lines.append((pt1, pt2))
                
                for connection in self.mp_face_mesh.FACEMESH_CONTOURS:
                    start_idx = connection[0]
                    end_idx = connection[1]
                    if start_idx < len(current_face_points) and end_idx < len(current_face_points):
                        pt1 = current_face_points[start_idx]
                        pt2 = current_face_points[end_idx]
                        current_face_lines.append((pt1, pt2))
                
                all_faces_lines.append(current_face_lines)

        return results, image_bgr, all_faces_points, all_faces_lines