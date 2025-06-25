import numpy as np
import cv2 

img = cv2.imread('pics/jea-1.jpg')
# to create mask
img_mask = img.copy()
# black copy of original image, as mask
inpaintMask = np.zeros(img.shape[:2], np.uint8)
# Create a sketch
cv2.imshow('mask', inpaintMask)

while True:
    ch = cv2.waitKey()
    if ch == 27:
        break
    if ch == ord('t'):
        res = cv2.inpaint(src=img_mask, inpaintMask=inpaintMask, 
                          inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        cv2.imshow('Inpaint Result using FMM', res)

cv2.destroyAllWindows()
