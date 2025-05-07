import os
import cv2
import numpy as np

def detect_marionette_lines(image_path):
    # Load the image
    directory = os.path.dirname(__file__)
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # Face detection
    cv2.FaceDetectorYN_create('./face_detection_yunet_2023mar_int8bq.onnx', "", (300, 300), score_threshold=0.5)

    # Canny edge detection
    edges = cv2.Canny(gray, 50, 150)
    cv2.imshow("detected edges", edges)
    # Hough Line Transform
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=50, maxLineGap=50)

    # (Further filtering and processing as needed)

    # Draw lines on the image
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(image, (x1, y1), (x2, y2), (255, 0, 0), 2)  # Blue lines

    return image

# Example Usage:
image_path = "./foto_1.jpg"
detected_image = detect_marionette_lines(image_path)
#cv2.imshow("Marionette Lines Detection", detected_image)
cv2.waitKey(0)
cv2.destroyAllWindows()