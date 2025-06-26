import cv2
import mediapipe as mp
import numpy as np
from skimage.feature import hessian_matrix, hessian_matrix_eigvals

def identify_nasolabial_landmarks_all_numbers(): # New function name for all numbers
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
    print("DISPLAYING ALL LANDMARK NUMBERS.")
    print("Have your grandfather SMILE naturally.")
    print("Identify the landmark numbers that best trace his nasolabial folds when smiling.")

    # --- Create a resizable window for the visualization ---
    detection_window_name = "Nasolabial Line Detections (Raw) - ALL NUMBERS"
    cv2.namedWindow(detection_window_name, cv2.WINDOW_NORMAL)
    target_width = 1920
    target_height = 1080
    cv2.resizeWindow(detection_window_name, target_width, target_height)

    # --- Drawing spec for full facemesh visualization (small points) ---
    drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)

    # --- Helper function for ROI processing (for visualization of contours only) ---
    def process_roi(region_name, roi_points, sigma_val, draw_color, padding=10, min_contour_area=15):
        if len(roi_points) < 3:
            return None 

        (x_base, y_base, w_base, h_base) = cv2.boundingRect(roi_points)
        x_base = max(0, x_base)
        y_base = max(0, y_base)
        w_base = min(img_w - x_base, w_base)
        h_base = min(img_h - y_base, h_base)

        x1 = max(0, x_base - padding)
        y1 = max(0, y_base - padding)
        x2 = min(img_w, x_base + w_base + padding)
        y2 = min(img_h, y_base + h_base + padding)

        w_final = x2 - x1
        h_final = y2 - y1

        if w_final <= 0 or h_final <= 0:
            return None

        cv2.polylines(frame_bgr, [roi_points], True, draw_color, 3) # Magenta outline for ROI
        if roi_points.size > 0:
            text_x, text_y = x_base, y_base 
            cv2.putText(frame_bgr, region_name, (text_x, text_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, draw_color, 2)

        mask_poly = np.zeros_like(gray_frame, dtype=np.uint8)
        cv2.fillPoly(mask_poly, [roi_points], 255) 
        masked_region = cv2.bitwise_and(gray_frame, gray_frame, mask=mask_poly)
        roi_cropped = masked_region[y1:y2, x1:x2]
        
        if roi_cropped.shape[0] == 0 or roi_cropped.shape[1] == 0:
            return None

        H_elems = hessian_matrix(roi_cropped, sigma=sigma_val)
        _, eigenvalues = hessian_matrix_eigvals(H_elems)
        wrinkles_mask_region = (eigenvalues < 0).astype(np.uint8) * 255 

        contours, _ = cv2.findContours(wrinkles_mask_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            if cv2.contourArea(contour) > min_contour_area:
                contour_offset = contour + (x1, y1)
                cv2.drawContours(frame_bgr, [contour_offset], -1, draw_color, 1) # DRAW DETECTED CONTOURS

        return None # No mask returned for this visualization step


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

        frame_bgr = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR) # Frame to draw on
        gray_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        img_h, img_w, _ = frame_bgr.shape # Update img_h, img_w after resizing

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                if len(face_landmarks.landmark) < 468:
                    continue 

                landmarks_px = []
                for lm in face_landmarks.landmark:
                    x, y = int(lm.x * img_w), int(lm.y * img_h)
                    landmarks_px.append((x, y))
                landmarks_px = np.array(landmarks_px)

                # --- DRAW THE FULL FACE MESH WITH ALL NUMBERS ---
                mp_drawing.draw_landmarks(
                    image=frame_bgr,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION, 
                    landmark_drawing_spec=drawing_spec,
                    connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style())
                
                # Draw ALL landmark numbers (can be very dense!)
                for i, (x, y) in enumerate(landmarks_px):
                    cv2.putText(frame_bgr, str(i), (x + 3, y + 3), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1, cv2.LINE_AA) # Smaller font for all numbers


                # --- Nasolabial Folds (Right Side) - Using YOUR LAST PROVIDED INDICES (for context) ---
                # You'll provide NEW indices based on the "all numbers" view while smiling
                right_nasolabial_indices = [49, 202, 206] 
                right_nasolabial_pts = np.array([landmarks_px[i] for i in right_nasolabial_indices if i < len(landmarks_px)], dtype=np.int32)
                # Drawing with a distinctive color (e.g., Yellow) so it doesn't conflict too much with the numbers
                #process_roi("Right Nasolabial (Current)", right_nasolabial_pts, sigma_val=1.2, draw_color=(0, 255, 255), padding=10, min_contour_area=15) # Yellow


                # --- Nasolabial Folds (Left Side) - Using YOUR LAST PROVIDED INDICES (for context) ---
                # You'll provide NEW indices based on the "all numbers" view while smiling
                left_nasolabial_indices = [279, 423, 422]
                left_nasolabial_pts = np.array([landmarks_px[i] for i in left_nasolabial_indices if i < len(landmarks_px)], dtype=np.int32)
                # Drawing with a distinctive color (e.g., Yellow)
                #process_roi("Left Nasolabial (Current)", left_nasolabial_pts, sigma_val=1.2, draw_color=(0, 255, 255), padding=10, min_contour_area=15) # Yellow


        cv2.imshow(detection_window_name, frame_bgr) 

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    face_mesh.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    identify_nasolabial_landmarks_all_numbers()