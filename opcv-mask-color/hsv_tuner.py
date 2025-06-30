import cv2
import numpy as np
import os

def nothing(x):
    pass

def run_hsv_tuner(image_path='apron-1.jpg'):
    display_witdth = 600
    display_height  = 600

    img = cv2.imread(image_path)
    if img is None:
        print("Error: Image not found!")
        return
    print(f"Image '{image_path}' loaded successfully")

    # Calculate resized image dimensions
    height, width = img.shape[:2]
    aspect_ratio = width / height   
    if aspect_ratio > 1:
        new_width = display_witdth
        new_height = int(new_width / aspect_ratio)
    else:
        new_height = display_height
        new_width = int(new_height * aspect_ratio)      

    # Resize image
    img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
    print(f"Original image dimensions: {width}x{height}")
    print(f"Resized image dimensions: {new_width}x{new_height}")

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # window for trackbars
    cv2.namedWindow("01 Original Image", cv2.WINDOW_NORMAL)
    cv2.namedWindow("02 HSV Mask", cv2.WINDOW_NORMAL)
    cv2.namedWindow("03 Result Masked Image", cv2.WINDOW_NORMAL    )
    cv2.namedWindow("04 HSV Tuner Trackbars", cv2.WINDOW_NORMAL)

    cv2.resizeWindow("01 Original Image", new_width, new_height)
    cv2.resizeWindow("02 HSV Mask", new_width, new_height)
    cv2.resizeWindow("03 Result Masked Image", new_width, new_height)
    cv2.resizeWindow("04 HSV Tuner Trackbars", 600,350)

    # Position windows for 1920x1080 screen
    # row 1 Original | mask | result
    # row 2 Trackbars 
    cv2.moveWindow("01 Original Image", 0, 0)
    cv2.moveWindow("02 HSV Mask", new_width, 0)
    cv2.moveWindow("03 Result Masked Image", 2 * new_width, 0)
    cv2.moveWindow("04 HSV Tuner Trackbars", 0, new_height + 30)


    # Create trackbars for HSV min/max values
    cv2.createTrackbar("H Min", "04 HSV Tuner Trackbars", 0, 179, nothing)
    cv2.createTrackbar("S Min", "04 HSV Tuner Trackbars", 0, 255, nothing)
    cv2.createTrackbar("V Min", "04 HSV Tuner Trackbars", 0, 255, nothing)
    cv2.createTrackbar("H Max", "04 HSV Tuner Trackbars", 179,179, nothing)
    cv2.createTrackbar("S Max", "04 HSV Tuner Trackbars", 255, 255, nothing)
    cv2.createTrackbar("V Max", "04 HSV Tuner Trackbars", 255, 255, nothing)

    cv2.waitKey(1)

    print("\n--- HSV Tuner Ready ---")
    print("Adjust trackbars to select desired color range.")
    print("Window '02. HSV Mask' shows detected regio, white pixels.")
    print("Window '03. Result Masked Image' shows detected region in the original image.")
    print("Press 'q' to exit the tuner.\n")

    while True:
        # Get current positions of trackbars
        h_min = cv2.getTrackbarPos("H Min", "04 HSV Tuner Trackbars")
        s_min = cv2.getTrackbarPos("S Min", "04 HSV Tuner Trackbars")
        v_min = cv2.getTrackbarPos("V Min", "04 HSV Tuner Trackbars")

        h_max = cv2.getTrackbarPos("H Max", "04 HSV Tuner Trackbars")
        s_max = cv2.getTrackbarPos("S Max", "04 HSV Tuner Trackbars")
        v_max = cv2.getTrackbarPos("V Max", "04 HSV Tuner Trackbars")

        # Ensure that min values are less than max values
        h_min = min(h_min, h_max)
        s_min = min(s_min, s_max)
        v_min = min(v_min, v_max)

        # Set HSV lower and upper bounds
        lower_bound = np.array([h_min, s_min, v_min])
        upper_bound = np.array([h_max, s_max, v_max])

        # Create the mask
        mask = cv2.inRange(hsv, lower_bound, upper_bound)

        # apply the mask to original Image for viaulization
        res = cv2.bitwise_and(img, img, mask=mask)

        cv2.imshow("01 Original Image", img)
        cv2.imshow("02 HSV Mask", mask)
        cv2.imshow("03 Result Masked Image", res)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cv2.destroyAllWindows()
    print("\nHSV Tuner closed")
    print("Recuerda guardar los valores encontrados.")

if __name__ == "__main__":
    run_hsv_tuner(image_path = 'apron-1.jpg')


