import cv2
import numpy as np
from matplotlib import pyplot as plt

image_path = 'apron-1-2.jpg'

def generate_outline(image_path):
    
    img = cv2.imread(image_path, -1)
    assert img is not None, f"Could not load image: '{image_path}'"
    img = cv2.medianBlur(img, 7)
    print(f"Image '{image_path}' loaded successfully.")

    img_copy = img.copy()

    imgGray = cv2.cvtColor(img_copy, cv2.COLOR_BGR2GRAY)
    imgHsv = cv2.cvtColor(img_copy, cv2.COLOR_BGR2HSV)
    print(f"Image '{image_path}' transformed successfully to grayscale, hsv.")

    thmi = cv2.adaptiveThreshold(imgGray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11,2)
    thai = cv2.adaptiveThreshold(imgGray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11,2)

    print(f"Adaptive thresholds applied to Image '{image_path}'.") 

    #cv2.imshow('Grey', thai)
    #cv2.imshow('Grey', thai)
    
    cv2.imwrite(f"adaptive_mean_{image_path}.jpg", thmi)
    cv2.imwrite(f"adaptive_gaussian_{image_path}.jpg", thai)

    titles = ['Original', 'MedianBlurred', 'Gray', 'HSV', 'Adaptive Mean Threshold', 'Adaptive Mean Threshold']
    images = [image_path, img, imgGray, imgHsv, thmi, thai]

    for i in range(len(images)):
        plt.subplot(2,2,i+1),plt.imshow(images[i], 'gray')
        plt.title(titles[i])
        plt.xticks([]), plt.yticks([])
    plt.show()

    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    generate_outline(image_path)
