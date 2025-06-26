# virtual_camera_emitter.py
import pyvirtualcam
import numpy as np
import subprocess # For running shell commands like v4l2-ctl
import re         # For regular expressions to parse command output

class VirtualCameraEmitter:
    def __init__(self, width: int, height: int, fps: float, device_path: str = None):
        """
        Initializes the VirtualCameraEmitter to send frames to a virtual webcam.

        Args:
            width (int): The width of the frames to send.
            height (int): The height of the frames to send.
            fps (float): The frames per second for the virtual camera.
            device_path (str, optional): The specific device path for the virtual camera (e.g., '/dev/video1').
                                         Defaults to None, letting pyvirtualcam choose.
                                         IMPORTANT: Ensure this device is created by v4l2loopback!
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.device_path = device_path
        self.cam = None

    def _check_v4l2loopback_device_status(self) -> bool:
        """
        Checks if the specified virtual camera device exists and is likely from v4l2loopback.
        Provides user guidance if issues are found.
        """
        if not self.device_path:
            print("VirtualCameraEmitter: Warning: No specific virtual device path provided. Cannot perform pre-check.")
            return True # Allow pyvirtualcam to attempt opening a default device

        print(f"VirtualCameraEmitter: Checking status of virtual device {self.device_path}...")
        try:
            # Use v4l2-ctl to list devices and check if our device path is there
            result = subprocess.run(['v4l2-ctl', '--list-devices'], capture_output=True, text=True, check=True)
            output = result.stdout

            # Find the section in the output that corresponds to our device_path
            # We look for the path and then for "v4l2loopback" in its associated description
            # This regex is more robust to whitespace and captures the device name.
            device_section_pattern = r"(?P<device_name>[^\n]+?)\s+\(.+?platform:v4l2loopback.+?\)\s*(\n\s*" + re.escape(self.device_path) + r")"
            match = re.search(device_section_pattern, output)

            if match:
                device_name = match.group('device_name').strip()
                print(f"VirtualCameraEmitter: Confirmed '{device_name}' ({self.device_path}) is a v4l2loopback device.")
                return True
            else:
                print(f"VirtualCameraEmitter: Error: Virtual device {self.device_path} not found or not recognized as a v4l2loopback device by 'v4l2-ctl'.")
                return False

        except FileNotFoundError:
            print("VirtualCameraEmitter: Error: 'v4l2-ctl' command not found. Please install v4l-utils (e.g., `sudo apt install v4l-utils`).")
            return False
        except subprocess.CalledProcessError as e:
            print(f"VirtualCameraEmitter: Error running 'v4l2-ctl': {e.stderr}")
            return False
        except Exception as e:
            print(f"VirtualCameraEmitter: An unexpected error occurred during device pre-check: {e}")
            return False

    def __enter__(self):
        """
        Context manager entry point. Initializes the pyvirtualcam.Camera.
        """
        if not self._check_v4l2loopback_device_status():
            raise IOError(
                f"\n--- Virtual Camera Setup Required ---\n"
                f"Virtual device '{self.device_path}' is not properly set up for this application.\n"
                f"Please ensure `v4l2loopback` is loaded correctly.\n"
                f"Run in your terminal (and provide password if prompted):\n"
                f"  `sudo modprobe v4l2loopback devices=1 exclusive_caps=1 card_label=\"MySmoothedCam\"`\n"
                f"After running this, verify the device path using `v4l2-ctl --list-devices`.\n"
                f"Then, re-run this application with the correct `--virtual-camera-path`.\n"
                f"-------------------------------------\n"
            )
        try:
            # `device` parameter explicitly specifies the virtual device path
            # `fmt=pyvirtualcam.PixelFormat.BGR` is critical as our frames from OpenCV are BGR
            self.cam = pyvirtualcam.Camera(width=self.width, height=self.height, fps=self.fps,
                                           fmt=pyvirtualcam.PixelFormat.BGR, device=self.device_path)
            print(f"VirtualCameraEmitter: Virtual camera started on {self.cam.device} at {self.width}x{self.height} @ {self.fps:.2f} FPS.")
            return self
        except Exception as e:
            # Provide more specific guidance on common errors if pyvirtualcam fails despite pre-check
            error_msg = f"Error: Could not initialize virtual camera on {self.device_path or 'default device'}. "
            if "No such file or directory" in str(e) or "V4L2_ERROR: Failed to open V4L2 device" in str(e):
                error_msg += "This usually means the device path is incorrect or it's not ready. "
            elif "Permission denied" in str(e):
                error_msg += "Permission denied. Ensure your user is in the 'video' group (`sudo usermod -a -G video $USER`) and logged back in."
            elif "Failed to open V4L2 device" in str(e):
                error_msg += "This might indicate a capabilities mismatch (e.g., `exclusive_caps=1` missing) or the device being in use by another app."
            raise IOError(f"{error_msg}\n  Original error: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point. Automatically releases the virtual camera.
        """
        if self.cam:
            self.cam.close() # pyvirtualcam.Camera uses .close()
            print(f"VirtualCameraEmitter: Virtual camera on {self.cam.device} released.")

    def send_frame(self, frame: np.ndarray):
        """
        Sends a single frame to the virtual camera.

        Args:
            frame (np.ndarray): The BGR frame to send.
        """
        if self.cam:
            self.cam.send(frame)
            self.cam.sleep_until_next_frame()
        else:
            print("VirtualCameraEmitter: Warning - Virtual camera not initialized. Frame not sent.")

# Example of how to use it (for testing purposes)
if __name__ == "__main__":
    # This block is for testing this module independently.
    # It attempts to open a camera and stream to a virtual one.
    print("--- Virtual Camera Emitter Test ---")
    print("Opening physical webcam and streaming to a virtual device.")
    print("You might need to run `sudo modprobe v4l2loopback devices=1 exclusive_caps=1 card_label=\"MySmoothedCam\"` first.")
    
    # Use your physical camera index, e.g., 0 or 1
    # Use your virtual camera path, e.g., '/dev/video0'
    PHYSICAL_CAM_INDEX = 0
    VIRTUAL_CAM_TEST_PATH = '/dev/video1' # Default for many systems

    cap = cv2.VideoCapture(PHYSICAL_CAM_INDEX)
    if not cap.isOpened():
        print(f"Error: Could not open physical webcam at index {PHYSICAL_CAM_INDEX}. Exiting test.")
        exit()

    # Get properties from physical camera
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: fps = 30 # Default to 30 if not reported

    try:
        with VirtualCameraEmitter(width=width, height=height, fps=fps, device_path=VIRTUAL_CAM_TEST_PATH) as emitter:
            print("Streaming to virtual camera. Check Cheese or Google Meet.")
            print("Press 'q' in this terminal to quit.")
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to grab frame from physical camera.")
                    break
                emitter.send_frame(frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    except IOError as e:
        print(f"Test failed due to IOError: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during the test: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("--- Virtual Camera Emitter Test Finished ---")