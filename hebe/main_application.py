# main_application.py
import cv2
import argparse
import time
import traceback # For printing full tracebacks on unexpected errors

from camera_handler import CameraHandler
from virtual_camera_emitter import VirtualCameraEmitter
from face_mesh_processor import FaceMeshProcessor
from nasolabial_mask_generator import NasolabialMaskGenerator
from image_effect_applier import ImageEffectApplier

class MainApplication:
    def __init__(self, camera_index: int, virtual_camera_path: str):
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

        # Initialize Face Mesh and Smoothing Components
        self.face_mesh_processor = FaceMeshProcessor()
        self.nasolabial_mask_generator = NasolabialMaskGenerator()
        self.image_effect_applier = ImageEffectApplier()

        print(f"MainApplication: Initialized with physical camera {self.camera_index} and virtual camera path {self.virtual_camera_path}.")

    def run(self):
        """
        Runs the main video processing loop.
        """
        print("MainApplication: Starting...")

        try:
            with CameraHandler(camera_index=self.camera_index) as camera_handler:
                self.camera_handler = camera_handler

                with VirtualCameraEmitter(width=self.camera_handler.width,
                                          height=self.camera_handler.height,
                                          fps=self.camera_handler.fps,
                                          device_path=self.virtual_camera_path) as virtual_camera_emitter:
                    self.virtual_camera_emitter = virtual_camera_emitter

                    print("\nPress 'q' in the console to quit the application.")
                    print("Also, check your video conferencing app (e.g., Cheese, Google Meet) and select the virtual camera 'VirtualAICam'.") # Updated name

                    while True:
                        ret, frame = self.camera_handler.read_frame()
                        if not ret:
                            print("MainApplication: Failed to read frame from physical camera. Exiting.")
                            break

                        # --- Frame Processing Logic ---
                        # Start with a copy of the original frame for MediaPipe processing
                        # MediaPipe might draw landmarks on this copy if enabled in FaceMeshProcessor
                        processed_for_facemesh = frame.copy() 

                        # Step 1: Process frame to detect facial landmarks
                        # This returns the image (potentially with drawn landmarks) and the MediaPipe results
                        _, results = self.face_mesh_processor.process_frame(processed_for_facemesh) # Don't need the image with drawn landmarks here, just the results

                        # Initialize processed_frame to be the original frame by default
                        final_output_frame = frame.copy()

                        # Check if face landmarks were detected
                        if results.multi_face_landmarks:
                            # Take the landmarks of the first detected face for smoothing
                            landmarks = results.multi_face_landmarks[0]

                            # Step 2: Generate the nasolabial mask based on landmarks AND the current frame data
                            # IMPORTANT CHANGE: Pass the actual 'frame' (BGR image) to generate_mask
                            mask = self.nasolabial_mask_generator.generate_mask(frame, landmarks)

                            # Step 3: Apply the smoothing effect to the original frame using the generated mask
                            # The result is the final_output_frame that will be sent out
                            final_output_frame = self.image_effect_applier.apply_gaussian_blur(frame, mask, kernel_size=(45, 45), sigmaX=0)
                        
                        # Send the final processed frame (either smoothed or original) to the virtual camera
                        self.virtual_camera_emitter.send_frame(final_output_frame)

                        # --- Debug/Visualization (Optional) ---
                        # Uncomment these lines to see the processed_frame on your local desktop
                        # This might impact performance slightly and is not part of the virtual camera stream.
                        # cv2.imshow('Smoothed Output (Local Debug)', final_output_frame)
                        # # You could also show the mask for debugging
                        # # if results.multi_face_landmarks:
                        # #     cv2.imshow('Mask (Local Debug)', mask)
                        # # else:
                        # #     cv2.imshow('Mask (Local Debug)', np.zeros_like(mask)) # Show black if no mask

                        # Check for quit keypress
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            print("MainApplication: 'q' pressed. Quitting.")
                            break

        except IOError as e:
            print(f"\nMainApplication Error (IOError): {e}")
            print("\n--- Troubleshooting Tips ---")
            print(f"  1. Ensure your physical camera (index: {self.camera_index}) is not in use by another application.")
            print(f"  2. Verify the `v4l2loopback` module is loaded correctly as prompted by VirtualCameraEmitter.")
            print(f"  3. Check permissions: Your user might need to be in the 'video' group. Run `sudo usermod -a -G video $USER` then log out/in.")
            print(f"  4. Confirm virtual device path: Check `v4l2-ctl --list-devices` to ensure `{self.virtual_camera_path}` is available.")
            print("----------------------------\n")
        except Exception as e:
            print(f"\nAn unexpected error occurred in MainApplication: {e}")
            traceback.print_exc() # Print full traceback for deeper debugging
        finally:
            print("MainApplication: Shutting down.")
            cv2.destroyAllWindows() # Close any OpenCV display windows

# This is the entry point of your application when run directly
if __name__ == "__main__":
    # --- Command-line Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Run the Nasolabial Smoother application. Streams from a physical camera to a virtual camera.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter # Shows default values in help message
    )

    parser.add_argument(
        "--camera-index",
        type=int,
        default=0, # Default physical camera index (often 0, but can be 1, 2, etc.)
        help="Index of the physical camera to use (e.g., 0, 1, 2). Use 'v4l2-ctl --list-devices' to identify."
    )

    parser.add_argument(
        "--virtual-camera-path",
        type=str,
        default='/dev/video1', # Default virtual camera path (often /dev/video0 or /dev/video1)
        help="Path to the virtual camera device (e.g., /dev/video0, /dev/video1). Use 'v4l2-ctl --list-devices' to identify your v4l2loopback device."
    )

    args = parser.parse_args() # Parse arguments from the command line

    # Create an instance of the main application and run it
    # Pass the parsed arguments to the MainApplication constructor
    app = MainApplication(camera_index=args.camera_index, virtual_camera_path=args.virtual_camera_path)
    app.run()