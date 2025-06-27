# main_application.py (UPDATED: Cleaned Nasolabial Mask Call)
import argparse
import sys
import numpy as np 

from camera_handler import CameraHandler 
from virtual_camera_emitter import VirtualCameraEmitter
from human_face_detector import HumanFaceDetector 
from edge_detector import EdgeDetector 
from mask_detector import MaskDetector 
from drawing_utility import (
    draw_face_mesh_overlay, 
    draw_face_mask_overlay, 
    composite_images, 
    draw_text 
)

class MainApplication:
    def __init__(self, camera_index: int, virtual_camera_path: str, max_num_faces: int = 1):
        """
        Initializes the main Digital Makeup application with configuration parameters.
        """
        self.camera_index = camera_index
        self.virtual_camera_path = virtual_camera_path
        self.max_num_faces = max_num_faces 

        self.camera_handler = None 
        self.virtual_camera_emitter = None
        self.human_face_detector = None 
        self.edge_detector = None 
        self.mask_detector = None 

        print(f"Digital Makeup: MainApplication: Initializing with physical camera index '{self.camera_index}', "
              f"virtual camera path '{self.virtual_camera_path}', and max faces '{self.max_num_faces}'.")

    def run(self):
        """
        Executes the main Digital Makeup application logic.
        This step focuses on creating and visualizing accurate nasolabial line masks.
        """
        print("\n--- Digital Makeup: MainApplication - Starting Step 6 (Cleaned Nasolabial Mask Call) ---")
        print("This test creates and displays a targeted mask specifically for nasolabial lines (Cyan overlay). "
              "Check your virtual camera to see your face with landmarks, green edges, a blue general mask, "
              "a red general edge ROI mask, AND a new Cyan nasolabial mask.")
        print("Press Ctrl+C in this terminal to quit.")

        try:
            with CameraHandler(camera_index=self.camera_index) as camera_handler, \
                 VirtualCameraEmitter(
                    width=camera_handler.width,
                    height=camera_handler.height,
                    fps=camera_handler.fps,
                    device_path=self.virtual_camera_path
                 ) as virtual_camera_emitter, \
                 HumanFaceDetector(max_num_faces=self.max_num_faces) as human_face_detector, \
                 EdgeDetector() as edge_detector, \
                 MaskDetector() as mask_detector: 

                self.camera_handler = camera_handler 
                self.virtual_camera_emitter = virtual_camera_emitter
                self.human_face_detector = human_face_detector 
                self.edge_detector = edge_detector
                self.mask_detector = mask_detector

                print("Digital Makeup: MainApplication: Streaming with refined mask generation started. Check your virtual camera app.")
                
                while True:
                    ret, frame = self.camera_handler.read_frame()
                    if not ret:
                        print("Digital Makeup: MainApplication: Failed to read frame, exiting loop.", file=sys.stderr)
                        break
                    
                    # 1. Process the frame for human face detection
                    results, processed_frame, all_faces_points, all_faces_lines = self.human_face_detector.process_frame(frame)

                    # 2. Extract and visualize general edges from face regions
                    face_edges_visual = self.edge_detector.extract_face_edges(processed_frame, all_faces_points, edge_color=(0, 255, 0)) # Green edges

                    # 3. Create the general binary face mask
                    face_mask_binary = self.mask_detector.create_face_mask(processed_frame.shape, all_faces_points)
                    
                    # 4. Create the binary mask for areas around ALL general edges (red overlay)
                    general_edge_roi_mask = self.mask_detector.create_edge_roi_mask(
                        processed_frame.shape, 
                        face_edges_visual, 
                        dilation_kernel_size=5, 
                        apply_general_face_mask=face_mask_binary 
                    )

                    # NEW CLEANED CALL: Create the binary mask specifically for nasolabial lines (cyan overlay)
                    # mask_detector.create_nasolabial_mask now handles multiple faces and returns a combined mask
                    nasolabial_mask = self.mask_detector.create_nasolabial_mask(
                        processed_frame.shape, 
                        all_faces_points, # Pass all face points directly
                        dilation_kernel_size=15, # Fine-tune this for thickness of the line
                        apply_general_face_mask=face_mask_binary # Use the general mask to clip
                    )


                    # --- No Digital Makeup Effects Applied in this Step ---
                    image_with_makeup = processed_frame # Simply use the original frame for now

                    # --- Visualization (drawn on image_with_makeup) ---
                    
                    final_frame = image_with_makeup
                    
                    # Draw face mesh (points and lines) on top
                    final_frame = draw_face_mesh_overlay(final_frame, results, all_faces_points, all_faces_lines)
                    
                    # Composite the detected general face edges onto the frame
                    final_frame = composite_images(final_frame, face_edges_visual)

                    # Draw the semi-transparent general face mask overlay (blue)
                    final_frame = draw_face_mask_overlay(final_frame, face_mask_binary, mask_color=(255, 0, 0), alpha=0.3)
                    
                    # Draw the semi-transparent general edge ROI mask overlay (red) - For general edge debugging
                    final_frame = draw_face_mask_overlay(final_frame, general_edge_roi_mask, mask_color=(0, 0, 255), alpha=0.5) 
                    
                    # NEW: Draw the semi-transparent NASOLABIAL mask overlay (CYAN)
                    final_frame = draw_face_mask_overlay(final_frame, nasolabial_mask, mask_color=(255, 255, 0), alpha=0.7) # Cyan BGR (more opaque to stand out)
                        
                    # Send the final processed frame to the virtual camera
                    self.virtual_camera_emitter.send_frame(final_frame)
                        
        except IOError as e:
            print(f"\n--- Digital Makeup: MainApplication - Step 6 Refinement FAILED (IOError) ---", file=sys.stderr)
            print(f"Camera or device error: {e}", file=sys.stderr)
            print("Please ensure your cameras are connected, v4l2loopback is loaded, and devices are correct.", file=sys.stderr)
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nDigital Makeup: MainApplication: Ctrl+C detected. Quitting.")
        except Exception as e:
            print(f"\n--- Digital Makeup: MainApplication - Step 6 Refinement FAILED (Unexpected Error) ---", file=sys.stderr)
            print(f"An unexpected error occurred: {e}", file=sys.stderr)
            sys.exit(1)

        finally:
            print("Digital Makeup: MainApplication: Exiting Step 6 refinement.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="The main orchestrator for the Digital Makeup application. "
                    "Handles command-line arguments and manages the workflow across modules.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--camera-index",
        type=int,
        default=0, 
        help="Index of the physical camera device to use (e.g., 0, 1, 2)."
    )

    parser.add_argument(
        "--virtual-camera-path",
        type=str,
        default='/dev/video0', 
        help="File path for the virtual camera device (e.g., /dev/video0, /dev/video1)."
    )

    parser.add_argument(
        "--max-num-faces",
        type=int,
        default=1,
        help="Maximum number of faces to detect for MediaPipe Face Mesh."
    )

    args = parser.parse_args()

    app = MainApplication(
        camera_index=args.camera_index, 
        virtual_camera_path=args.virtual_camera_path,
        max_num_faces=args.max_num_faces
    )
    app.run()