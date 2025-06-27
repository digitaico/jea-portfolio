# virtual_camera_emitter.py
import pyvirtualcam
import numpy as np
import subprocess
import re
import os
import time # For diagnostic sleep

class VirtualCameraEmitter:
    def __init__(self, width: int, height: int, fps: float, device_path: str = '/dev/video0'):
        """
        Initializes the VirtualCameraEmitter for the Digital Makeup application.

        Args:
            width (int): The width of frames to be sent to the virtual camera.
            height (int): The height of frames to be sent to the virtual camera.
            fps (float): The frames per second to be reported by the virtual camera.
            device_path (str): The file path of the v4l2loopback virtual device (e.g., /dev/video0).
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.device_path = device_path
        self.cam = None # pyvirtualcam.Camera instance

        print(f"Digital Makeup: VirtualCameraEmitter: Initializing for device '{self.device_path}' "
              f"at {self.width}x{self.height} @ {self.fps:.2f} FPS.")
        self._check_v4l2loopback_device()

    def _check_v4l2loopback_device(self):
        """
        Verifies if the specified device path corresponds to a v4l2loopback device.
        This provides a more informative error if the device isn't set up correctly.
        """
        try:
            # Use v4l2-ctl to list devices and their properties
            result = subprocess.run(
                ['v4l2-ctl', '--list-devices'],
                capture_output=True, text=True, check=True
            )
            v4l2_output = result.stdout

            # Debug: Print raw v4l2-ctl output received
            print(f"Digital Makeup: VirtualCameraEmitter: DEBUG: Raw v4l2-ctl output received (using repr()):\n{repr(v4l2_output)}")

            # Regex to find the device and its card label
            # This regex needs to be robust for various v4l2-ctl outputs
            # It looks for lines starting with "Card Name (platform:...)" followed by lines with "/dev/videoX"
            pattern = re.compile(r'^(.*?)\(platform:v4l2loopback-.*?\):\n\t(/dev/video\d+)', re.MULTILINE)
            matches = pattern.findall(v4l2_output)

            found_device = False
            card_label = "Unknown"

            for label, device_path in matches:
                # Strip leading/trailing whitespace and non-printable chars from label
                label = label.strip()
                if device_path == self.device_path:
                    found_device = True
                    card_label = label
                    break
            
            if not found_device:
                raise RuntimeError(
                    f"Digital Makeup: VirtualCameraEmitter Error: Device '{self.device_path}' "
                    f"not found or not identified as a v4l2loopback device by v4l2-ctl."
                )
            
            print(f"Digital Makeup: VirtualCameraEmitter: Confirmed '{card_label}' ({self.device_path}) is a v4l2loopback device.")

        except FileNotFoundError:
            raise RuntimeError(
                "Digital Makeup: VirtualCameraEmitter Error: 'v4l2-ctl' command not found. "
                "Please install v4l2-utils package (e.g., `sudo apt install v4l2-utils`)."
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Digital Makeup: VirtualCameraEmitter Error: 'v4l2-ctl' command failed: {e.stderr}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Digital Makeup: VirtualCameraEmitter Error: Failed to check v4l2loopback device status: {e}"
            )

    def __enter__(self):
        """
        Context manager entry point: Opens the virtual camera.
        Raises an IOError if the virtual camera cannot be initialized.
        """
        print(f"Digital Makeup: VirtualCameraEmitter: Attempting to initialize virtual camera on '{self.device_path}'...")
        
        # --- Diagnostic Sleep ---
        # Based on previous debugging, a short delay before initializing pyvirtualcam
        # sometimes resolves "not a video output device" errors, especially in
        # scenarios with subtle timing or resource contention issues.
        # This can be removed if found unnecessary after full integration.
        time.sleep(1) 
        # --- End Diagnostic Sleep ---

        try:
            self.cam = pyvirtualcam.Camera(
                width=self.width,
                height=self.height,
                fps=self.fps,
                fmt=pyvirtualcam.PixelFormat.BGR, # Assuming OpenCV frames are BGR
                device=self.device_path
            )
            print(f"Digital Makeup: VirtualCameraEmitter: Virtual camera started successfully on {self.cam.device}.")
            return self
        except Exception as e:
            # Provide more context for common pyvirtualcam errors
            error_message = (
                f"Digital Makeup: VirtualCameraEmitter Error: Could not initialize virtual camera on {self.device_path}. "
                f"Original error: '{e}'.\n"
                f"Common causes: v4l2loopback module not loaded, incorrect device path, "
                f"or device not configured as a video output."
            )
            raise IOError(error_message) from e

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point: Releases the virtual camera.
        """
        if self.cam:
            print("Digital Makeup: VirtualCameraEmitter: Releasing virtual camera.")
            self.cam.close()
        self.cam = None

    def send_frame(self, frame: np.ndarray):
        """
        Sends a NumPy array frame to the virtual camera.

        Args:
            frame (np.ndarray): The frame to send. Must be a BGR NumPy array.
        """
        if self.cam:
            # pyvirtualcam expects C-contiguous arrays. Ensure this for safety.
            if not frame.flags['C_CONTIGUOUS']:
                frame = np.ascontiguousarray(frame)
            self.cam.send(frame)
            # Sleep until the next frame is due to maintain consistent FPS
            self.cam.sleep_until_next_frame()