import cv2
import mediapipe as mp
import numpy as np
from skimage.feature import hessian_matrix, hessian_matrix_eigvals
import pyvirtualcam
import time

def smooth_nasolabial_lines_virtual_cam():
    mp_face_mesh = mp.solutions.face_mesh
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False,
                                      max_num_faces=1,
                                      refine_landmarks=True,
                                      min_detection_confidence=0.5,
                                      min_tracking_confidence=0.5)

    # Open the PHYSICAL camera (input)
    cap = cv2.VideoCapture(1) # Assuming your physical camera is still /dev/video0

    if not cap.isOpened():
        print("Error: Could not open physical camera. It might be in use or have a different index.")
        print("Try changing cv2.VideoCapture(0) to (1), (2) etc. or ensure no other app uses it.")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 30.0

    print("Press 'q' to quit.")
    print(f"Physical camera opened. Setting up virtual camera for output.")
    print(f"Virtual camera resolution: {width}x{height} at {fps} FPS.")
    print("Look for the virtual webcam device (likely named 'MySmoothedCam') in your video conferencing software.")


    # Initialize the virtual camera, explicitly specifying its output path
    # >>> IMPORTANT: Check `ls /dev/video*` to confirm what your new virtual device is
    # >>> If your physical camera is /dev/video0, the new virtual one created by modprobe will likely be /dev/video1
    virtual_cam_path = '/dev/video0' # <--- ADJUST THIS IF YOUR VIRTUAL CAM IS A DIFFERENT INDEX
    
    try:
        with pyvirtualcam.Camera(width=width, height=height, fps=fps, fmt=pyvirtualcam.PixelFormat.BGR, device=virtual_cam_path) as cam:
            print(f"Virtual camera started successfully on {cam.device}. Ready for connection.")
            print(f"Adjusting original frame to {cam.width}x{cam.height} for virtual cam.")

            target_width = cam.width
            target_height = cam.height

            drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)

            def process_roi_and_mask(region_name, roi_points, sigma_val, draw_color, padding=1, min_contour_area=15):
                nonlocal gray_frame, img_w, img_h

                if len(roi_points) < 3:
                    return np.zeros_like(gray_frame, dtype=np.uint8) 

                (x_base, y_base, w_base, h_base) = cv2.boundingRect(roi_points)
                x_base = max(0, x_base)
                y_base = max(0, y_base)
                w_base = min(img_w - x_base, w_base)
                h_base = min(img_h - y_base, h_base)

                x1 = max(0, x_base - padding)
                y1 = max(0, y_base - padding)
                x2 = min(img_w, x_base + w_base + padding)
                y2 = min(img_h, h_base + y_base + padding) 

                w_final = x2 - x1
                h_final = y2 - y1

                if w_final <= 0 or h_final <= 0:
                    return np.zeros_like(gray_frame, dtype=np.uint8)
                
                mask_poly = np.zeros_like(gray_frame, dtype=np.uint8)
                cv2.fillPoly(mask_poly, [roi_points], 255) 
                masked_region = cv2.bitwise_and(gray_frame, gray_frame, mask=mask_poly)
                roi_cropped = masked_region[y1:y2, x1:x2]
                
                if roi_cropped.shape[0] == 0 or roi_cropped.shape[1] == 0:
                    return np.zeros_like(gray_frame, dtype=np.uint8)

                H_elems = hessian_matrix(roi_cropped, sigma=sigma_val)
                _, eigenvalues = hessian_matrix_eigvals(H_elems)
                wrinkles_mask_region = (eigenvalues < 0).astype(np.uint8) * 255 

                current_region_mask = np.zeros_like(gray_frame, dtype=np.uint8)

                contours, _ = cv2.findContours(wrinkles_mask_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for contour in contours:
                    if cv2.contourArea(contour) > min_contour_area:
                        contour_offset = contour + (x1, y1)
                        cv2.drawContours(current_region_mask, [contour_offset], -1, 255, -1) 

                kernel = np.ones((7,7), np.uint8) 
                current_region_mask = cv2.morphologyEx(current_region_mask, cv2.MORPH_CLOSE, kernel, iterations=3) 

                return current_region_mask


            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read frame from physical camera.")
                    break

                frame = cv2.resize(frame, (target_width, target_height))
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                rgb_frame.flags.writeable = False 
                results = face_mesh.process(rgb_frame)
                rgb_frame.flags.writeable = True 

                original_frame_for_blend = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR).copy() 
                frame_bgr = original_frame_for_blend.copy() 
                gray_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

                img_h, img_w, _ = frame_bgr.shape 

                nasolabial_lines_mask = np.zeros((img_h, img_w), dtype=np.uint8)
                
                if results.multi_face_landmarks:
                    for face_landmarks in results.multi_face_landmarks:
                        if len(face_landmarks.landmark) < 468:
                            continue 

                        landmarks_px = []
                        for lm in face_landmarks.landmark:
                            x, y = int(lm.x * img_w), int(lm.y * img_h)
                            landmarks_px.append((x, y))
                        landmarks_px = np.array(landmarks_px)

                        right_nasolabial_indices = sorted(list(set([64, 49, 131, 36, 203, 206, 205, 207, 212, 216])))
                        right_nasolabial_pts = np.array([landmarks_px[i] for i in right_nasolabial_indices if i < len(landmarks_px)], dtype=np.int32)
                        
                        current_mask = process_roi_and_mask("Right Nasolabial", right_nasolabial_pts, sigma_val=1.5, draw_color=(255, 0, 255), padding=1, min_contour_area=15) 
                        if current_mask is not None:
                            nasolabial_lines_mask = cv2.bitwise_or(nasolabial_lines_mask, current_mask)


                        left_nasolabial_indices = sorted(list(set([371, 279, 266, 423, 425, 426, 427, 436, 432]))) 
                        left_nasolabial_pts = np.array([landmarks_px[i] for i in left_nasolabial_indices if i < len(landmarks_px)], dtype=np.int32)
                        
                        current_mask = process_roi_and_mask("Left Nasolabial", left_nasolabial_pts, sigma_val=1.5, draw_color=(255, 0, 255), padding=1, min_contour_area=15) 
                        if current_mask is not None:
                            nasolabial_lines_mask = cv2.bitwise_or(nasolabial_lines_mask, current_mask)

                        frame_to_blur = original_frame_for_blend.copy(order='C') 
                        
                        kernel_size = (11, 11) 
                        sigmaX = 10 
                        blurred_frame_copy = cv2.GaussianBlur(frame_to_blur, kernel_size, sigmaX) 
                        
                        if np.any(nasolabial_lines_mask > 0): 
                            mask_3_channel = cv2.cvtColor(nasolabial_lines_mask, cv2.COLOR_GRAY2BGR)
                            alpha = mask_3_channel.astype(float) / 255.0
                            
                            frame_bgr = (alpha * blurred_frame_copy.astype(float) + \
                                         (1 - alpha) * original_frame_for_blend.astype(float)).astype(np.uint8)
                
                cam.send(frame_bgr)
                cam.sleep_until_next_frame()

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    except Exception as e:
        print(f"An error occurred with pyvirtualcam: {e}")
        print("Please ensure `v4l2loopback` is properly loaded to create virtual devices.")
        print("Also check if your specified 'virtual_cam_path' exists and is available.")

    face_mesh.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    smooth_nasolabial_lines_virtual_cam()