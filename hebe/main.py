import cv2
import mediapipe as mp
import numpy as np 
import os
from Filters import Filters

def detect_faces_mediapipe_youthify():
    """
    Captures video from webcam, detects faces and landmarks using MediaPipe
    """
    # Landmark indices for left and right marionette lines (adjust as needed)
    LEFT_MARIONETTE_LANDMARKS_DEBUG = [129,203,205,216,212]
    RIGHT_MARIONETTE_LANDMARKS_DEBUG = [358,423,436,432]

    filters_to_apply = Filters()

    cap = cv2.VideoCapture(int(os.environ.get("WEBCAM_INDEX", 1)))
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    mp_face_detection = mp.solutions.face_detection
    mp_drawing = mp.solutions.drawing_utils
    mp_face_mesh = mp.solutions.face_mesh 

    with mp_face_detection.FaceDetection(
        model_selection=1, min_detection_confidence=0.5) as face_detection, \
         mp_face_mesh.FaceMesh(
            max_num_faces = 1,
            refine_landmarks = True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5) as face_mesh:

        while cap.isOpened():
            success, image_bgr = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            # flip image horizontally for later self view display
            image_bgr = cv2.flip(image_bgr, 1)
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            image_rgb.flags.writeable = False
            detection_results = face_detection.process(image_rgb)
            mesh_results = face_mesh.process(image_rgb)
            image_rgb.flags.writeable = True
            
            print(f"mesh results: {mesh_results}") 
            
            if mesh_results.multi_face_landmarks:
                print(f"Number of faces detected in mesh: {len(mesh_results.multi_face_landmarks)}")
                face_landmarks = mesh_results.multi_face_landmarks[0]
                print(f"Number of landmarks in first face: {len(face_landmarks.landmark)}")

                # Draw debug circles at marionette landmark positions
                ih, iw, _ = image_bgr.shape
                for index in LEFT_MARIONETTE_LANDMARKS_DEBUG:
                    try:
                        x = int(face_landmarks.landmark[index].x * iw)
                        y = int(face_landmarks.landmark[index].y * ih)
                        cv2.circle(image_bgr, (x, y), 5, (0, 0, 255), -1)
                    except IndexError:
                        print(f"IndexError: Landmark index {index} out of range (0-{len(face_landmarks.landmark)-1})")

                for index in RIGHT_MARIONETTE_LANDMARKS_DEBUG:
                    try:
                        x = int(face_landmarks.landmark[index].x * iw)
                        y = int(face_landmarks.landmark[index].y * ih)
                        cv2.circle(image_bgr, (x, y), 5, (0, 0, 255), -1)
                    except IndexError:
                        print(f"IndexError: Landmark index {index} out of range (0-{len(face_landmarks.landmark)-1})")

                mask = filters_to_apply.create_marionette_mask(image_bgr.shape, face_landmarks)
                cv2.imshow("Marionette Mask", mask)
                # Apply filters
                image_bgr = filters_to_apply.apply_skin_smoothing(image_bgr, detection_results)
                image_bgr = filters_to_apply.enlarge_eyes(image_bgr, face_landmarks)

                # Draw face mesh landmarks
                for face_landmark in mesh_results.multi_face_landmarks:
                    mp_drawing.draw_landmarks(
                        image=image_rgb,
                        landmark_list = face_landmark,
                        connections=mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=mp_drawing.DrawingSpec(color=(0,255,0), thickness=1, circle_radius=1),
                        connection_drawing_spec=mp_drawing.DrawingSpec(color=(255,0,0), thickness=1),
                    )

            # Display th BGR image convertes to BGR
            cv2.imshow("MediaPipe Youthification", cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))

            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_faces_mediapipe_youthify()











