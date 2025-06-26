# main_application.py
import cv2
import time # For time.sleep if needed, or just keep cv2.waitKey

# Assuming camera_handler.py and virtual_camera_emitter.py are in the same directory
from camera_handler import CameraHandler
from virtual_camera_emitter import VirtualCameraEmitter

# You'll import/define other classes here as we create them:
# from face_mesh_processor import FaceMeshProcessor
# from nasolabial_mask_generator import NasolabialMaskGenerator
# from image_effect_applier import ImageEffectApplier

class MainApplication:
    def __init__(self, camera_index: int = 1, virtual_camera_path: str = '/dev/video0'):
        """
        Initializes the main application with camera and virtual camera configurations.

        Args:
            camera_index (int): Index of the physical camera to use.
            virtual_camera_path (str): File path for the virtual camera device.
        """
        self.camera_index = camera_index
        self.virtual_camera_path = virtual_camera_path

        self.camera_handler = None
        self.virtual_camera_emitter = None

        # Placeholder for other processors (will be initialized later)
        # self.face_mesh_processor = None
        # self.nasolabial_mask_generator = None
        # self.image_effect_applier = None

        print("MainApplication: Initialized.")

    def run(self):
        """
        Runs the main video processing loop.
        """
        print("MainApplication: Starting...")
        
        try:
            # Use context managers for CameraHandler and VirtualCameraEmitter
            # This ensures they are properly initialized and released.
            with CameraHandler(camera_index=self.camera_index) as camera_handler:
                self.camera_handler = camera_handler # Store reference

                # Use camera_handler's properties to initialize virtual camera
                with VirtualCameraEmitter(width=self.camera_handler.width,
                                          height=self.camera_handler.height,
                                          fps=self.camera_handler.fps,
                                          device_path=self.virtual_camera_path) as virtual_camera_emitter:
                    self.virtual_camera_emitter = virtual_camera_emitter # Store reference

                    # --- Main processing loop ---
                    print("\nPress 'q' in the console to quit the application.")
                    while True:
                        ret, frame = self.camera_handler.read_frame()
                        if not ret:
                            print("MainApplication: Failed to read frame. Exiting.")
                            break

                        # --- Frame Processing Placeholder ---
                        # In later steps, we will add the MediaPipe processing,
                        # mask generation, and image effect application here.
                        processed_frame = frame.copy() # For now, just pass through the frame

                        # --- End Frame Processing Placeholder ---

                        # Send the (potentially processed) frame to the virtual camera
                        self.virtual_camera_emitter.send_frame(processed_frame)

                        # Check for quit key
                        # cv2.waitKey(1) requires an active OpenCV window,
                        # but it still processes keyboard events globally to an extent.
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            print("MainApplication: 'q' pressed. Quitting.")
                            break

        except IOError as e:
            print(f"MainApplication Error: {e}")
            print("Please ensure your physical camera is available and `v4l2loopback` is set up correctly.")
        except Exception as e:
            print(f"An unexpected error occurred in MainApplication: {e}")
        finally:
            # Resources are released automatically by 'with' statements,
            # but this block ensures graceful shutdown messages or cleanup if needed.
            print("MainApplication: Shutting down.")
            cv2.destroyAllWindows() # Clean up any OpenCV windows (even if not explicitly shown)

# This is the entry point of your application
if __name__ == "__main__":
    # --- Configuration ---
    # Adjust these parameters based on your system setup
    CAM_INDEX = 1             # Your physical camera index (usually 0)
    VIRTUAL_CAM_PATH = '/dev/video1' # The virtual device path created by v4l2loopback

    # Create an instance of the application and run it
    app = MainApplication(camera_index=CAM_INDEX, virtual_camera_path=VIRTUAL_CAM_PATH)
    app.run()