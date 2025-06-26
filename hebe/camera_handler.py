# camera_handler.py
import cv2
import numpy as np
import time

class CameraHandler:
    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480, fps: float = 30.0):
        """
        Initializes the CameraHandler for a physical webcam.

        Args:
            camera_index (int): The index of the camera device (e.g., 0, 1).
            width (int): Desired frame width.
            height (int): Desired frame height.
            fps (float): Desired frames per second.
        """
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None

    def __enter__(self):
        """
        Context manager entry point. Opens the camera.
        """
        print(f"CameraHandler: Attempting to open camera {self.camera_index}...")
        self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            raise IOError(f"Error: Could not open camera at index {self.camera_index}. It might be in use, or the index is incorrect.")

        # Set properties (these might not be exactly honored by all cameras)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        # Read actual properties after setting
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps == 0: # Some cameras report 0, default to 30
            self.fps = 30.0

        print(f"CameraHandler: Opened camera {self.camera_index} at {self.width}x{self.height} @ {self.fps:.2f} FPS.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point. Releases the camera.
        """
        if self.cap:
            self.cap.release()
            print(f"CameraHandler: Camera {self.camera_index} released.")

    def read_frame(self) -> tuple[bool, np.ndarray]:
        """
        Reads a single frame from the camera.

        Returns:
            tuple: A tuple containing:
                - bool: True if frame was read successfully, False otherwise.
                - np.ndarray: The captured frame (BGR format) or None if read failed.
        """
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            return ret, frame
        return False, None

# Example Usage (for independent testing of this module)
if __name__ == "__main__":
    print("--- Camera Handler Test ---")
    print("Opening webcam. Press 'q' to quit.")
    try:
        # Use your physical camera index, e.g., 0 or 1
        with CameraHandler(camera_index=0) as cam_handler:
            while True:
                ret, frame = cam_handler.read_frame()
                if not ret:
                    print("Failed to read frame.")
                    break
                cv2.imshow('Camera Test', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    except IOError as e:
        print(f"Error: {e}")
    finally:
        cv2.destroyAllWindows()
        print("--- Camera Handler Test Finished ---")