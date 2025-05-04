import cv2
import os
import face_alignment
import torch
from ultralytics import YOLO

def detect_faces_and_landmarks_yolo():
    """captures video from webcam, detects faces using YOLOv5 and facial landmarks and displays result"""
    video_capture = cv2.VideoCapture(int(os.environ.get("WEBCAM_INDEX", 1)))

    if not video_capture.isOpened():
        print("Error: Could not open webcam")
        return

    # Set frame width and height
    frame_width = 320
    frame_height = 240
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

    # Load YOLOv5 face detector
    try:
        face_model = YOLO('yolov5su.pt') # download this model
        face_model.to('cuda' if torch.cuda.is_available() else 'cpu')
    except Exception as e:
        print(f"Error loading YOLOv5 face detection model: {e}")
        return

    # Initialize the face aligment model using a lightweight 2D model.
    try:
        fa = face_alignment.FaceAlignment(face_alignment.LandmarksType.TWO_D, device='cuda' if torch.cuda.is_available() else 
                                          'cpu', flip_input=True)
    except Exception as e:
        print(f"Error initializing face alignment model: {e}")
        return

    while True:
        ret, frame = video_capture.read()

        if not ret:
            print("Error: Could not read frame.")
            break
            
        # Detect faces with YOLOv5
        results = face_model(frame)

        # get bounding boxes of detected faces
        faces = []
        for result in results:
            if result.boxes is not None and len(result.boxes.xyxy) > 0:
                faces = result.boxes.xyxy.cpu().numpy().astype(int) # x1, y1, x2, y2 format
                break
        
        # Detect landmarks for each detected face
        if faces is not None and len(faces) > 0:
            for (x1, y1, x2, y2) in faces:
                face_image = frame[y1:y2, x1:x2]
                try:
                    preds = fa.get_landmarks(face_image)
                    if preds is not None:
                        for landmark in preds[0]:
                            cv2.circle(frame, (int(landmark[0]) + x1, int(landmark[1]) + y1), 1, (0, 0, 255), -1)
                except Exception as e:
                    print(f"Error detecting landmarks: {e}")
                # draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)

        cv2.imshow("Face and landmarks YOLO", frame)
        # press q to exit the loop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_faces_and_landmarks_yolo()

