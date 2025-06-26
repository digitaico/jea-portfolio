import cv2
import numpy as np

print("Testing cv2.GaussianBlur on a generated image.")

# Create a simple test image (a checkerboard pattern)
img_size = 300
img = np.zeros((img_size, img_size, 3), dtype=np.uint8)
# Draw some clear lines to make blur visible
cv2.line(img, (0, img_size // 2), (img_size, img_size // 2), (0, 0, 255), 5) # Red line
cv2.line(img, (img_size // 2, 0), (img_size // 2, img_size), (0, 255, 0), 5) # Green line
cv2.rectangle(img, (50, 50), (250, 250), (255, 0, 0), -1) # Blue rectangle

cv2.putText(img, "Original", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

cv2.imshow("Original Test Image", img)

# Apply Gaussian Blur with a large kernel
blurred_img_1 = cv2.GaussianBlur(img, (25, 25), 0) # Very large kernel for unmistakable blur
cv2.putText(blurred_img_1, "Blurred (25x25)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
cv2.imshow("Blurred Test Image (25x25)", blurred_img_1)

# Apply Gaussian Blur with a smaller kernel
blurred_img_2 = cv2.GaussianBlur(img, (5, 5), 0) # Smaller kernel
cv2.putText(blurred_img_2, "Blurred (5x5)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
cv2.imshow("Blurred Test Image (5x5)", blurred_img_2)

print("Press any key to exit all test image windows.")
cv2.waitKey(0)
cv2.destroyAllWindows()