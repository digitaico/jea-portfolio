import cv2
import matplotlib.pyplot as plt
import numpy as np
#import matplotlib 

print(cv2.__version__)

imagePath = '1.png'
image = cv2.imread(imagePath)
imageGray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

#plt.imshow(imageGray)

ret, thresh = cv2.threshold(imageGray, 200, 255, cv2.THRESH_BINARY_INV)

contours, hierarchy = cv2.findContours(image, mode, method[, contours[, 
                                                                      hierarchy[, 
                                                                                offset]]])


