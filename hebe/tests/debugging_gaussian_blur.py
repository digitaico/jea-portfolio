import cv2
import mediapipe as mp
import numpy as np
from skimage.feature import hessian_matrix, hessian_matrix_eigvals

def smooth_nasolabial_lines_alpha_blend_test(): # The latest version with alpha blending
    mp_face_mesh = mp.solutions.face_mesh
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False,
                                      max_num_faces=1,
                                      refine_landmarks=True,
                                      min_detection_confidence=0.5,
                                      min_tracking_confidence=0.5)

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return

    print("Press 'q' to quit.")
    print("ALPHA BLENDING TEST: Blending blurred region with original for smoother look.")
    print(">>>> IMPORTANT: Ensure consistent face detection for the effect to apply.")
    print(">>>> Focus on lighting, face position, and distance for stable detection.")

    output_window_name = "Nasolabial Lines Smoothing (Final Output - Alpha Blend)"
    cv2.namedWindow(output_window_name, cv2.WINDOW_NORMAL)
    target_width = 1920
    target_height = 1080
    cv2.resizeWindow(output_window_name, target_width, target_height)

    detection_debug_window_name = "Nasolabial Detections (Debug)"
    cv2.namedWindow(detection_debug_window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(detection_debug_window_name, target_width // 2, target_height // 2)

    mask_debug_window_name = "Nasolabial Mask (Debug)"
    cv2.namedWindow(mask_debug_window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(mask_debug_window_name, target_width // 2, target_height // 2)

    blurred_debug_window_name = "Debug: Blurred Frame (Should be EXTREMELY Blurred!)"
    cv2.namedWindow(blurred_debug_window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(blurred_debug_window_name, target_width // 2, target_height // 2)

    overlay_debug_window_name = "DEBUG: Mask Overlay on Final Frame (Should be GREEN)"
    cv2.namedWindow(overlay_debug_window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(overlay_debug_window_name, target_width // 2, target_height // 2)

    drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)

    def process_roi_and_mask(region_name, roi_points, sigma_val, draw_color, padding=1, min_contour_area=15):
        # Local variables to be accessed from the main loop's scope
        nonlocal gray_frame, debug_detection_frame, img_w, img_h

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

        cv2.polylines(debug_detection_frame, [roi_points], True, draw_color, 3) 
        if roi_points.size > 0:
            text_x, text_y = x_base, y_base 
            cv2.putText(debug_detection_frame, region_name, (text_x, text_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, draw_color, 2)

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
                cv2.drawContours(debug_detection_frame, [contour_offset], -1, draw_color, 1) 
                cv2.drawContours(current_region_mask, [contour_offset], -1, 255, -1) 

        kernel = np.ones((7,7), np.uint8) 
        current_region_mask = cv2.morphologyEx(current_region_mask, cv2.MORPH_CLOSE, kernel, iterations=3) 

        return current_region_mask


    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        aspect_ratio = frame.shape[1] / frame.shape[0] 
        if aspect_ratio > target_width / target_height: 
            new_width = target_width
            new_height = int(target_width / aspect_ratio)
        else: 
            new_height = target_height
            new_width = int(target_height * aspect_ratio)
            
        frame = cv2.resize(frame, (new_width, new_height))
        
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        rgb_frame.flags.writeable = False 
        results = face_mesh.process(rgb_frame)
        rgb_frame.flags.writeable = True 

        original_frame_for_blend = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR).copy() 
        frame_bgr = original_frame_for_blend.copy() 
        debug_detection_frame = frame_bgr.copy() 
        gray_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        img_h, img_w, _ = frame_bgr.shape 

        nasolabial_lines_mask = np.zeros((img_h, img_w), dtype=np.uint8)
        
        if results.multi_face_landmarks: # This is the crucial condition!
            for face_landmarks in results.multi_face_landmarks:
                if len(face_landmarks.landmark) < 468:
                    continue 

                landmarks_px = []
                for lm in face_landmarks.landmark:
                    x, y = int(lm.x * img_w), int(lm.y * img_h)
                    landmarks_px.append((x, y))
                landmarks_px = np.array(landmarks_px)

                mp_drawing.draw_landmarks(
                    image=debug_detection_frame, 
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION, 
                    landmark_drawing_spec=drawing_spec,
                    connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style())

                right_nasolabial_indices = sorted(list(set([64, 49, 131, 36, 203, 206, 205, 207, 216])))
                right_nasolabial_pts = np.array([landmarks_px[i] for i in right_nasolabial_indices if i < len(landmarks_px)], dtype=np.int32)
                
                current_mask = process_roi_and_mask("Right Nasolabial", right_nasolabial_pts, sigma_val=1.5, draw_color=(255, 0, 255), padding=1, min_contour_area=15) 
                if current_mask is not None:
                    nasolabial_lines_mask = cv2.bitwise_or(nasolabial_lines_mask, current_mask)


                left_nasolabial_indices = sorted(list(set([371, 279, 266, 423, 425, 426, 427, 436, 432]))) 
                left_nasolabial_pts = np.array([landmarks_px[i] for i in left_nasolabial_indices if i < len(landmarks_px)], dtype=np.int32)
                
                current_mask = process_roi_and_mask("Left Nasolabial", left_nasolabial_pts, sigma_val=1.5, draw_color=(255, 0, 255), padding=1, min_contour_area=15) 
                if current_mask is not None:
                    nasolabial_lines_mask = cv2.bitwise_or(nasolabial_lines_mask, current_mask)

                cv2.imshow(mask_debug_window_name, nasolabial_lines_mask)

                frame_to_blur = original_frame_for_blend.copy(order='C') 
                
                print(f"\nBefore GaussianBlur: frame_to_blur shape={frame_to_blur.shape}, dtype={frame_to_blur.dtype}")
                kernel_size = (51, 51) 
                blurred_frame_copy = cv2.GaussianBlur(frame_to_blur, kernel_size, 0) 
                print(f"After GaussianBlur: blurred_frame_copy shape={blurred_frame_copy.shape}, dtype={blurred_frame_copy.dtype}")
                
                cv2.imshow(blurred_debug_window_name, blurred_frame_copy)

                if np.array_equal(frame_to_blur, blurred_frame_copy):
                    print("CRITICAL: frame_to_blur and blurred_frame_copy are IDENTICAL. GaussianBlur is STILL not working on live frame data.")
                else:
                    print("SUCCESS: blurred_frame_copy is different from original. GaussianBlur is working on live frame.")
                    
                    if np.any(nasolabial_lines_mask > 0):
                        mask_3_channel = cv2.cvtColor(nasolabial_lines_mask, cv2.COLOR_GRAY2BGR)
                        alpha = mask_3_channel.astype(float) / 255.0
                        
                        frame_bgr = (alpha * blurred_frame_copy.astype(float) + \
                                     (1 - alpha) * original_frame_for_blend.astype(float)).astype(np.uint8)

                        print(f"Applying Alpha Blending with alpha based on mask.")

                        mask_coords_rows, mask_coords_cols = np.where(nasolabial_lines_mask == 255)
                        if len(mask_coords_rows) > 0:
                            temp_overlay_color = [0, 255, 0] # Green
                            frame_bgr_with_overlay = original_frame_for_blend.copy() 
                            frame_bgr_with_overlay[mask_coords_rows, mask_coords_cols] = temp_overlay_color
                            cv2.imshow(overlay_debug_window_name, frame_bgr_with_overlay)
                            cv2.waitKey(1) 

                            sample_idx = np.random.randint(0, len(mask_coords_rows))
                            sample_row = mask_coords_rows[sample_idx]
                            sample_col = mask_coords_cols[sample_idx]

                            original_pixel_value = original_frame_for_blend[sample_row, sample_col]
                            blurred_pixel_value = blurred_frame_copy[sample_row, sample_col]
                            blended_pixel_value = frame_bgr[sample_row, sample_col]

                            print(f"Sample pixel ({sample_row}, {sample_col}):")
                            print(f"  Original (from original_frame_for_blend): {original_pixel_value}")
                            print(f"  Blurred (from blurred_frame_copy): {blurred_pixel_value}")
                            print(f"  Blended (in final frame_bgr): {blended_pixel_value} (should be blend of original & blurred)")
                            
                            if np.array_equal(blended_pixel_value, original_pixel_value) and \
                               not np.array_equal(blended_pixel_value, blurred_pixel_value):
                                print(f"DEBUG: Pixel at ({sample_row}, {sample_col}) in final frame_bgr is a blend.")
                            elif np.array_equal(blended_pixel_value, blurred_pixel_value):
                                print(f"DEBUG: Pixel at ({sample_row}, {sample_col}) in final frame_bgr is fully blurred (alpha=1).")
                            else:
                                print(f"CRITICAL: Blending issue at ({sample_row}, {sample_col}).")

                        else:
                            print("Mask coordinates found, but list is empty. No pixel assignment (mask might be too small).")
                    else:
                        print("Warning: Nasolabial lines mask is entirely black, no blur applied to output.")
        else:
            print("No face landmarks detected. No processing for this frame.")


        cv2.imshow(detection_debug_window_name, debug_detection_frame) 
        cv2.imshow(output_window_name, frame_bgr) 

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    face_mesh.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    smooth_nasolabial_lines_alpha_blend_test()