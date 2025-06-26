# face_mesh_processor.py
import cv2
import mediapipe as mp
import numpy as np # For type hinting

class FaceMeshProcessor:
    def __init__(self, static_image_mode: bool = False, max_num_faces: int = 1,
                 refine_landmarks: bool = True, min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5):
        """
        Initializes the FaceMeshProcessor to detect facial landmarks using MediaPipe.

        Args:
            static_image_mode (bool): Whether to treat the input images as a static collection or a video stream.
                                      For live video, set to False.
            max_num_faces (int): Maximum number of faces to detect.
            refine_landmarks (bool): Whether to further refine the landmark coordinates around eyes and lips.
            min_detection_confidence (float): Minimum confidence value ([0.0, 1.0]) for face detection to be considered successful.
            min_tracking_confidence (float): Minimum confidence value ([0.0, 1.0]) for the landmark tracker to be considered successful.
        """
        self.static_image_mode = static_image_mode
        self.max_num_faces = max_num_faces
        self.refine_landmarks = refine_landmarks
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        # Initialize MediaPipe Face Mesh model
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=self.static_image_mode,
            max_num_faces=self.max_num_faces,
            refine_landmarks=self.refine_landmarks,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )
        print("FaceMeshProcessor: MediaPipe Face Mesh initialized.")

    def process_frame(self, image: np.ndarray):
        """
        Processes a single image frame to detect facial landmarks.

        Args:
            image (np.ndarray): The input image frame (BGR format from OpenCV).

        Returns:
            tuple: A tuple containing:
                - processed_image (np.ndarray): The image with optional landmark drawings.
                                               Returns the original image if no drawing is enabled or no face found.
                - results (mediapipe.python.solution_base.SolutionResults): The raw MediaPipe results object,
                                                                             containing landmarks, etc.
                                                                             Will be None if no face is detected.
        """
        # Convert the BGR image to RGB as MediaPipe solutions primarily use RGB.
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # To improve performance, optionally mark the image as not writeable to pass by reference.
        image_rgb.flags.writeable = False
        results = self.face_mesh.process(image_rgb)
        image_rgb.flags.writeable = True # Re-enable writeability if you modify image_rgb later

        # Optionally draw the face mesh landmarks on the image (for visualization/debugging)
        # For the final smoothed output, we typically won't draw these directly on the main stream.
        # However, it's useful for verifying detection.
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # You can choose to draw specific connections or all of them.
                # Here, we'll draw the default face mesh connections.
                self.mp_drawing.draw_landmarks(
                    image=image, # Draw on the original BGR image for output
                    landmark_list=face_landmarks,
                    connections=self.mp_face_mesh.FACEMESH_TESSELATION, # Or FACEMESH_CONTOURS, FACEMESH_FACE_OVAL, etc.
                    landmark_drawing_spec=None, # No individual dots
                    connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
                )
                # You might also want to draw the face oval or contours
                self.mp_drawing.draw_landmarks(
                    image=image,
                    landmark_list=face_landmarks,
                    connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style()
                )

        return image, results

    def __del__(self):
        """
        Ensures the MediaPipe Face Mesh resources are released when the object is destroyed.
        """
        if self.face_mesh:
            self.face_mesh.close()
            print("FaceMeshProcessor: MediaPipe Face Mesh resources released.")


# Example of how to use it (for testing purposes)
if __name__ == "__main__":
    # This example requires a webcam
    print("--- Face Mesh Processor Test ---")
    print("Opening webcam. Press 'q' to quit.")

    cap = cv2.VideoCapture(0) # Use your physical camera index, e.g., 0 or 1
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        exit()

    processor = FaceMeshProcessor()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # Process the frame
        processed_frame, results = processor.process_frame(frame)

        # Display the processed frame (with landmarks drawn)
        cv2.imshow('Face Mesh Test', processed_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("--- Face Mesh Processor Test Finished ---")