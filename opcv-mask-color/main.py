import cv2
import matplotlib.pyplot as plt
import numpy as np
#%matplotlib inline

print(cv2.__version__)
QT_DEBUG_PLUGINS=1
#export QT_QPA_PLATFORM=xcb

imagePath = '1.png'
image = cv2.imread(imagePath)
imageGray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

plt.imshow(imageGray)


