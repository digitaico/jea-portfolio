from typing import List, Dict, Any
import numpy as np

from shared.models.domain import FramePose
from shared.utils.constants import MediaPipeLandmarks
from .base_calculator import BaseMetricsCalculator


class VerticalOscillationCalculator(BaseMetricsCalculator):
    """Calculator for vertical oscillation of the runner's center (meters)"""

    def calculate(self, pose_data: List[FramePose]) -> Dict[str, Any]:
        """Compute standard deviation of hip-center Y positions as vertical oscillation."""
        if len(pose_data) < 10:
            return {"vertical_oscillation": 0.0}

        # Get hip centers (average of left and right hip landmarks)
        left_hip = self.get_landmark_positions(pose_data, MediaPipeLandmarks.LEFT_HIP.value)
        right_hip = self.get_landmark_positions(pose_data, MediaPipeLandmarks.RIGHT_HIP.value)
        hip_center = (left_hip + right_hip) / 2.0  # shape (N,3)

        # Smooth Y coordinate to reduce noise
        y_smooth = self.smooth_signal(hip_center[:, 1])

        # Pixel → meters conversion (same logic as SpeedCalculator)
        pixel_to_meter_ratio = self.height_m / np.mean([
            np.abs(left_hip[:, 1].max() - left_hip[:, 1].min()),
            np.abs(right_hip[:, 1].max() - right_hip[:, 1].min())
        ])

        vertical_osc_m = np.std(y_smooth) * pixel_to_meter_ratio

        return {
            "vertical_oscillation": vertical_osc_m
        } 