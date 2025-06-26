# virtual_camera_emitter.py
import pyvirtualcam
import numpy as np # Used for type hinting 'frame: np.ndarray'

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

    def __enter__(self):
        """
        Context manager entry point. Initializes the pyvirtualcam.Camera.
        """
        try:
            # `device` parameter explicitly specifies the virtual device path
            # `fmt=pyvirtualcam.PixelFormat.BGR` is critical as our frames from OpenCV are BGR
            self.cam = pyvirtualcam.Camera(width=self.width, height=self.height, fps=self.fps,
                                           fmt=pyvirtualcam.PixelFormat.BGR, device=self.device_path)
            print(f"VirtualCameraEmitter: Virtual camera started on {self.cam.device} at {self.width}x{self.height} @ {self.fps:.2f} FPS.")
            return self
        except Exception as e:
            # Provide more specific guidance on common errors
            error_msg = f"Error: Could not initialize virtual camera on {self.device_path or 'default device'}. "
            if "No such file or directory" in str(e) or "V4L2_ERROR: Failed to open V4L2 device" in str(e):
                error_msg += "This usually means the specified device path does not exist or `v4l2loopback` is not loaded/configured correctly."
                error_msg += "\n  Ensure you've run: `sudo modprobe v4l2loopback devices=1 exclusive_caps=1 card_label=\"MySmoothedCam\"`"
                error_msg += "\n  And checked `ls /dev/video*` to confirm the device path (e.g., /dev/video1)."
            elif "Permission denied" in str(e):
                error_msg += "Permission denied. Ensure your user is in the 'video' group (sudo usermod -a -G video $USER) and logged back in."
            raise IOError(f"{error_msg}\n  Original error: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point. Automatically releases the virtual camera.
        """
        if self.cam:
            self.cam.close() # pyvirtualcam.Camera uses .close() for cleanup
            print(f"VirtualCameraEmitter: Virtual camera on {self.cam.device} released.")

    def send_frame(self, frame: np.ndarray):
        """
        Sends a single frame to the virtual camera.

        Args:
            frame (np.ndarray): The BGR frame to send.
        """
        if self.cam:
            # pyvirtualcam was initialized with fmt=BGR, so it expects BGR frames
            # and handles any internal conversions needed for the virtual device.
            self.cam.send(frame)
            self.cam.sleep_until_next_frame()
        else:
            print("VirtualCameraEmitter: Warning - Virtual camera not initialized. Frame not sent.")

# Example of how to use it (for testing purposes)
if __name__ == "__main__":
    # This example requires:
    # 1. A physical webcam at index 0 (adjust `physical_camera_index` if different).
    # 2. `v4l2loopback` loaded to create a virtual device (e.g., at /dev/video1).
    #    Run in your terminal: `sudo modprobe v4l2loopback devices=1 exclusive_caps=1 card_label="MySmoothedCam"`
    #    And verify path: `ls /dev/video*`
    # It will simply pass through the physical webcam feed to the virtual cam.

    import cv2
    from camera_handler import CameraHandler # Assuming CameraHandler is in camera_handler.py

    physical_camera_index = 0
    virtual_camera_path = '/dev/video1' # <--- ADJUST THIS IF YOUR VIRTUAL CAM IS A DIFFERENT INDEX

    print("--- Virtual Camera Emitter Test ---")
    print(f"Attempting to open physical camera at index: {physical_camera_index}")
    print(f"Attempting to stream to virtual camera at path: {virtual_camera_path}")
    print("---------------------------------")

    try:
        with CameraHandler(camera_index=physical_camera_index) as cam_input:
            with VirtualCameraEmitter(width=cam_input.width, height=cam_input.height,
                                      fps=cam_input.fps, device_path=virtual_camera_path) as cam_output:
                print("\nStreaming physical camera to virtual camera. Check your video conferencing app (e.g., Cheese, Google Meet) and select 'MySmoothedCam' or similar.")
                print("Press 'q' in console to quit.")
                
                while True:
                    ret, frame = cam_input.read_frame()
                    if not ret:
                        print("Failed to read frame from physical camera, exiting.")
                        break

                    # Resize frame if dimensions don't match exactly (though they should based on init)
                    # This step is mostly a safeguard, as width/height are derived from input cam.
                    if frame.shape[1] != cam_output.width or frame.shape[0] != cam_output.height:
                        frame = cv2.resize(frame, (cam_output.width, cam_output.height))

                    cam_output.send_frame(frame)

                    # For console quit check (requires an active window for cv2.waitKey to work well)
                    # If you just want to quit from console input, you might need a different mechanism
                    # if no cv2.imshow window is active.
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("Quit requested, exiting loop.")
                        break

    except IOError as e:
        print(f"Setup or Camera Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during streaming: {e}")

    cv2.destroyAllWindows() # Ensures any hidden OpenCV windows are closed if any were used internally
    print("--- Test Finished ---")