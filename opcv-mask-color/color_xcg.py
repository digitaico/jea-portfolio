import cv2
import numpy as np
import os

def change_figure_colors(image_path, output_path ):
    # Load the image
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Image '{image_path}' not found!")
        return  
