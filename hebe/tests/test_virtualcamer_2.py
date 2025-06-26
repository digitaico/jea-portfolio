import cv2

camera_index = 1 # Try 1 first, if not, try 2
cap = cv2.VideoCapture(camera_index)

if not cap.isOpened():
    print(f"Error: Could not open camera at index {camera_index}. Trying next index if available.")
    # If 1 didn't work, try 2 (only if you have a /dev/video2 listed)
    if camera_index == 1:
        camera_index = 2
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            print(f"Error: Could not open camera at index {camera_index} either. Check your devices.")
            exit()
        else:
            print(f"Successfully opened camera at index {camera_index}.")
else:
    print(f"Successfully opened camera at index {camera_index}.")

print("Displaying camera feed. Press 'q' to quit.")
while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        break

    cv2.imshow("Physical Camera Test", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()