# drawing_utility.py (RENAMED and UPDATED)
import cv2
import numpy as np
from typing import Any # For MediaPipe results type hint if passed directly

def draw_points(image: cv2.Mat, points: list[tuple[int, int]], color: tuple[int, int, int] = (0, 255, 0), radius: int = 2, thickness: int = -1) -> cv2.Mat:
    """
    Draws a list of points (circles) on an image.
    Args: image, points, color, radius, thickness
    Returns: The image with points drawn.
    """
    for x, y in points:
        cv2.circle(image, (x, y), radius, color, thickness)
    return image

def draw_lines(image: cv2.Mat, lines: list[tuple[tuple[int, int], tuple[int, int]]], color: tuple[int, int, int] = (255, 255, 255), thickness: int = 1) -> cv2.Mat:
    """
    Draws a list of line segments on an image.
    Args: image, lines, color, thickness
    Returns: The image with lines drawn.
    """
    for (x1, y1), (x2, y2) in lines:
        cv2.line(image, (x1, y1), (x2, y2), color, thickness)
    return image

def draw_text(image: cv2.Mat, text: str, position: tuple[int, int], font_scale: float = 0.7, color: tuple[int, int, int] = (255, 255, 255), thickness: int = 2) -> cv2.Mat:
    """
    Draws text on an image.
    Args: image, text, position, font_scale, color, thickness
    Returns: The image with text drawn.
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(image, text, position, font, font_scale, color, thickness, cv2.LINE_AA)
    return image

def composite_images(base_image: cv2.Mat, overlay_image: cv2.Mat) -> cv2.Mat:
    """
    Composites two images by adding them together. Assumes both images are of the same size and type.
    Useful for overlaying prepared elements (like edges, mask) onto a base frame.
    Args: base_image, overlay_image
    Returns: The composited image.
    """
    return cv2.add(base_image, overlay_image)

def alpha_composite_images(base_image: cv2.Mat, overlay_image: cv2.Mat, alpha: float) -> cv2.Mat:
    """
    Composites an overlay image onto a base image with a specified alpha (transparency) value.
    Assumes both images are of the same size and type (BGR).

    Args:
        base_image (cv2.Mat): The background image.
        overlay_image (cv2.Mat): The image to overlay (e.g., a colored mask).
        alpha (float): The transparency value for the overlay image (0.0 to 1.0).

    Returns:
        cv2.Mat: The composited image with the overlay blended.
    """
    return cv2.addWeighted(base_image, 1 - alpha, overlay_image, alpha, 0)


# --- NEW FUNCTIONS FOR FACIAL VISUALIZATION ---

def draw_face_mesh_overlay(image: cv2.Mat, 
                           results: Any | None, 
                           all_faces_points: list[list[tuple[int, int]]], 
                           all_faces_lines: list[list[tuple[tuple[int, int], tuple[int, int]]]],
                           point_color: tuple[int, int, int] = (0, 255, 255), # Yellow
                           line_color: tuple[int, int, int] = (255, 0, 0),    # Blue
                           point_radius: int = 1,
                           line_thickness: int = 1) -> cv2.Mat:
    """
    Draws MediaPipe face mesh landmarks (points and lines) onto an image.

    Args:
        image (cv2.Mat): The image to draw on.
        results (Any | None): The MediaPipe results object.
        all_faces_points (list[list[tuple[int, int]]]): List of all face landmark points.
        all_faces_lines (list[list[tuple[tuple[int, int], tuple[int, int]]]]): List of all face mesh line segments.
        point_color (tuple[int, int, int]): BGR color for landmark points.
        line_color (tuple[int, int, int]): BGR color for mesh lines.
        point_radius (int): Radius for landmark points.
        line_thickness (int): Thickness for mesh lines.

    Returns:
        cv2.Mat: The image with face mesh drawn.
    """
    if results and results.multi_face_landmarks:
        for face_idx, face_points in enumerate(all_faces_points):
            draw_points(image, face_points, color=point_color, radius=point_radius, thickness=-1) 
            draw_lines(image, all_faces_lines[face_idx], color=line_color, thickness=line_thickness)
    return image

def draw_face_mask_overlay(image: cv2.Mat, 
                           face_mask_binary: cv2.Mat, 
                           mask_color: tuple[int, int, int] = (255, 0, 0), # Blue
                           alpha: float = 0.3) -> cv2.Mat:
    """
    Draws a semi-transparent face mask overlay on the image.

    Args:
        image (cv2.Mat): The base image.
        face_mask_binary (cv2.Mat): The binary mask (0 or 255 values).
        mask_color (tuple[int, int, int]): The BGR color for the mask overlay.
        alpha (float): Transparency for the mask overlay (0.0 to 1.0).

    Returns:
        cv2.Mat: The image with the mask overlay.
    """
    # Create a colored overlay layer based on the binary mask
    colored_mask_overlay = np.zeros_like(image)
    colored_mask_overlay[face_mask_binary == 255] = mask_color 
    
    # Alpha blend the colored mask overlay with the base image
    # This handles an all-black colored_mask_overlay gracefully if face_mask_binary is empty
    return alpha_composite_images(image, colored_mask_overlay, alpha)