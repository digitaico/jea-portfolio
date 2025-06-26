import cv2

cap = cv2.VideoCapture(1) # Try 0, then 1, then 2 if 0 fails
if not cap.isOpened():
    print("Error: Could not open camera.")
else:
    print("Camera opened successfully!")
    ret, frame = cap.read()
    if ret:
        cv2.imshow("Test Cam", frame)
        cv2.waitKey(0)
    cap.release()
    cv2.destroyAllWindows()
