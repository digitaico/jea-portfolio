import cv2
import numpy as np

EYE_RESIZE_FACTOR = 1.15
EYES_ROI_RESIZE_FACTOR = 1.5
FOREHEAD_KERNEL_SIZE = 11
FACE_KERNEL_SIZE = 9

LEFT_MARIONETTE_LANDMARKS = [95,96,178,179]
RIGHT_MARIONETTE_LANDMARKS = [325, 326, 406, 407]

class Filters:
    def __init__(self):
        pass

    def apply_skin_smoothing(self, image_bgr, face_detection_results):
        """Applies skin smoothing to detected face regions."""
        if face_detection_results.detections:
            for detection in face_detection_results.detections:
                bboxC = detection.location_data.relative_bounding_box
                ih, iw, ic = image_bgr.shape
                bbox =  int(bboxC.xmin * iw), int(bboxC.ymin * ih), \
                        int(bboxC.width * iw), int(bboxC.height * ih)
                x, y, w, h = bbox

                if w > 0 and h > 0:
                    face_roi = image_bgr[y:y+h, x:x+w].copy()
                    # Apply Gaussian Blur for smoothing
                    blurred_face = cv2.GaussianBlur(face_roi, (11,11), 0)
                    # Replace original face region with blurred one.
                    image_bgr[y:y+h, x:x +w] = blurred_face
        return image_bgr

    def enlarge_eyes(self, image_bgr, face_landmarks):
        """ enlarges eyes based on detected landmarks """
        if face_landmarks and face_landmarks.landmark:
            left_eye = (int(face_landmarks.landmark[133].x * image_bgr.shape[1]),
                        int(face_landmarks.landmark[133].y * image_bgr.shape[0]))
            right_eye = (int(face_landmarks.landmark[362].x * image_bgr.shape[1]),
                        int(face_landmarks.landmark[362].y * image_bgr.shape[0]))

            def get_roi (center, size_factor=EYES_ROI_RESIZE_FACTOR):
                size = int(size_factor * 20)
                x = max(0, center[0] - size // 2)
                y = max(0, center[1] - size // 2)
                return x, y, size, size

            lx, ly, lw, lh = get_roi(left_eye)
            rx, ry, rw, rh = get_roi(right_eye)

            if lw > 0 and lh > 0 and rx + rw < image_bgr.shape[1] and ry + rh < image_bgr.shape[0]:
                left_eye_roi = image_bgr[ly:ly + lh, lx:lx + lw].copy()
                resized_left_eye = cv2.resize(left_eye_roi, None, fx=EYE_RESIZE_FACTOR, fy=EYE_RESIZE_FACTOR, interpolation=cv2.INTER_LINEAR) # slight enlargement
                new_lh, new_lw, _ = resized_left_eye.shape
                offset_ly = ly - (new_lh - lh) // 2
                offset_lx = lx - (new_lw - lw) // 2
                if 0 <= offset_ly < image_bgr.shape[0] - new_lh and 0 <= offset_lx < image_bgr.shape[1] - new_lw:
                    image_bgr[offset_ly:offset_ly + new_lh, offset_lx:offset_lx +new_lw] = resized_left_eye

            if rw > 0 and rh > 0 and rx + rw < image_bgr.shape[1] and ry + rh < image_bgr.shape[0]:
                right_eye_roi = image_bgr[ry:ry + rh, rx:rx + rw].copy()
                resized_right_eye = cv2.resize(right_eye_roi, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_LINEAR) # slight enlargement
                new_rh, new_rw, _ = resized_right_eye.shape
                offset_ry = ry - (new_rh - rh) // 2
                offset_rx = rx - (new_rw - rw) // 2
                if 0 <= offset_ry < image_bgr.shape[0] - new_rh and 0 <= offset_rx < image_bgr.shape[1] - new_rw:
                    image_bgr[offset_ry:offset_ry + new_rh, offset_rx:offset_rx +new_rw] = resized_right_eye

        return image_bgr

    def smooth_forehead(self, image_bgr, face_detection_results, face_landmarks):
        """ Applies smoothing to an estimated forehead ROI  based on eye landmarks."""
        if face_detection_results.detections and face_landmarks and face_landmarks.landmark:
            bboxC = face_detection_results.detections[0].location_data.relative_bounding_box
            ih, iw, ic = image_bgr.shape
            bbox =  int(bboxC.xmin * iw), int(bboxC.ymin * ih), \
                    int(bboxC.width * iw), int(bboxC.height * ih)
            x, y, w, h = bbox

            left_eye_y = int(face_landmarks.landmark[0].y * ih)
            right_eye_y = int(face_landmarks.landmark[1].y * ih)
            eyes_y = min(left_eye_y, right_eye_y)

            # forehead ROI estimation
            forehead_top = int(y - 0.15 * h)
            forehead_bottom = int(eyes_y * 0.9) # extend down to 80% of the ey level
            forehead_left = int(x + 0.1 * w)
            forehead_right = int(x + 0.9 * w)

            #print(f"Forehead ROI: top={forehead_top}, bottom={forehead_bottom}, left={forehead_left}, right={forehead_right}, image height={ih}, image width={iw}")

            # draw forehead boundaries for visualization
            #cv2.rectangle(image_bgr, (forehead_left, forehead_top), (forehead_right, forehead_bottom), (0,255,0), 1)

            if 0 <= forehead_top < forehead_bottom < ih and 0 <= forehead_left < forehead_right < iw:
                forehead_roi = image_bgr[forehead_top:forehead_bottom, forehead_left:forehead_right].copy()
                blurred_forehead = cv2.GaussianBlur(forehead_roi, (FOREHEAD_KERNEL_SIZE, FOREHEAD_KERNEL_SIZE), 0)
                image_bgr[forehead_top:forehead_bottom, forehead_left: forehead_right] = blurred_forehead
                print("forehead blur applied")

        return image_bgr


    def create_marionette_mask(self, image_shape, face_landmarks):
        """ Creates a mask for the marionette lines based on face landmarks """
        mask = np.zeros(image_shape[:2], dtype=np.uint8)
        if face_landmarks and len(face_landmarks.landmark) == 468:
            points_left = np.array([(int(face_landmarks.landmark[i].x * image_shape[1]),
                                    int(face_landmarks.landmark[i].y * image_shape[0]))
                                    for i in LEFT_MARIONETTE_LANDMARKS], np.int32)
            points_right = np.array([(int(face_landmarks.landmark[i].x * image_shape[1]),
                                    int(face_landmarks.landmark[i].y * image_shape[0]))
                                    for i in RIGHT_MARIONETTE_LANDMARKS], np.int32)

            # Draw lines and thicken them to create the mask
            cv2.polylines(mask, [points_left], isClosed=False, color=255, thickness=5)
            cv2.polylines(mask, [points_right], isClosed=False, color=255, thickness=5)

        return mask

    def create_marionette_lines_inpainting(self, image_bgr, mask):
        """ Applies Inpainting to reduce marionette lines."""
        if mask is not None:
            inpainting_image = cv2.inpaint(image_bgr, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA )
            return inpainted_image

        return image_bgr

