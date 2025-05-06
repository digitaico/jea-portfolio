import cv2
import os

def detect_faces():
    """
    Captures video from webcam, detects faces and landmarks using MediaPipe
    """
    cap = cv2.VideoCapture(int(os.environ.get("WEBCAM_INDEX", 1)))
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    while cap.isOpened():
        ret, image = cap.read()
        if not ret:
            print("Ignoring empty camera frame.")
            continue

        image = cv2.flip(image, 1)
        cv2.imshow("Camera Raw", image)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            cap.release()
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_faces()











