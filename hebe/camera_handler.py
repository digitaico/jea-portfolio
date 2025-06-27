# camera_handler.py
import cv2
import sys # For error output

class CameraHandler:
    def __init__(self, camera_index: int):
        """
        Initializes the CameraHandler for a physical webcam.

        Args:
            camera_index (int): The index of the physical camera to use (e.g., 0, 1, 2).
        """
        self.camera_index = camera_index
        self.cap = None  # OpenCV VideoCapture object
        self.width = 0   # Frame width
        self.height = 0  # Frame height
        self.fps = 0.0   # Frames per second

        print(f"Digital Makeup: CameraHandler: Initializing for camera index {self.camera_index}.")

    def __enter__(self):
        """
        Context manager entry point: Opens the camera.
        Raises an IOError if the camera cannot be opened.
        """
        print(f"Digital Makeup: CameraHandler: Attempting to open camera {self.camera_index}...")
        self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            # Release any potentially partially opened resources
            self.cap.release()
            raise IOError(f"Digital Makeup: CameraHandler Error: Could not open camera at index {self.camera_index}. "
                          "Please ensure the camera is connected and not in use by another application.")
        
        # Get actual camera properties
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        # Some cameras might report 0 FPS or very low FPS if not streaming yet
        if self.fps <= 1.0: # Set a default reasonable FPS if property is not available or too low
            self.fps = 30.0 

        print(f"Digital Makeup: CameraHandler: Opened camera {self.camera_index} at {self.width}x{self.height} @ {self.fps:.2f} FPS.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point: Releases the camera.
        """
        if self.cap and self.cap.isOpened():
            print(f"Digital Makeup: CameraHandler: Releasing camera {self.camera_index}.")
            self.cap.release()
        self.cap = None

    def read_frame(self) -> tuple[bool, cv2.Mat | None]:
        """
        Reads a single frame from the camera.

        Returns:
            tuple[bool, np.ndarray | None]: A tuple where the first element is True if a frame
                                          was successfully read, and the second element is the frame
                                          (numpy array) or None if reading failed.
        """
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                print("Digital Makeup: CameraHandler Warning: Failed to read frame.", file=sys.stderr)
            return ret, frame
        return False, None