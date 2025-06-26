# camera_handler.py
import cv2

class CameraHandler:
    def __init__(self, camera_index=0):
        """
        Initializes the CameraHandler to open a webcam.

        Args:
            camera_index (int): The index of the camera to open (default is 0).
        """
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            raise IOError(f"Error: Could not open camera at index {self.camera_index}. "
                          "It might be in use, or the index is incorrect.")

        self._width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self._fps == 0: # Fallback if FPS is not properly reported
            self._fps = 30.0 # Default to 30 FPS

        print(f"CameraHandler: Opened camera {self.camera_index} at {self.width}x{self.height} @ {self.fps:.2f} FPS")

    @property
    def width(self):
        """Returns the width of the camera frame."""
        return self._width

    @property
    def height(self):
        """Returns the height of the camera frame."""
        return self._height

    @property
    def fps(self):
        """Returns the frames per second (FPS) of the camera."""
        return self._fps

    def read_frame(self):
        """
        Reads a single frame from the camera.

        Returns:
            tuple: A tuple (ret, frame) where ret is True if the frame was read successfully,
                   and frame is the captured frame (or None if read failed).
        """
        ret, frame = self.cap.read()
        if not ret:
            print(f"CameraHandler: Warning - Could not read frame from camera {self.camera_index}.")
        return ret, frame

    def release(self):
        """
        Releases the camera resource.
        """
        if self.cap.isOpened():
            self.cap.release()
            print(f"CameraHandler: Camera {self.camera_index} released.")

    # Using context manager for safe handling (optional but good practice)
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

# Example of how to use it (for testing purposes, not part of the main app yet)
if __name__ == "__main__":
    try:
        with CameraHandler(camera_index=0) as cam: # Use 'with' for auto-release
            print(f"Camera properties: {cam.width}x{cam.height} @ {cam.fps} FPS")
            
            # Simple loop to display frames
            while True:
                ret, frame = cam.read_frame()
                if not ret:
                    break
                
                cv2.imshow("Camera Test - Press 'q' to quit", frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            cv2.destroyAllWindows()

    except IOError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")