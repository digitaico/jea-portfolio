from typing import List, Dict, Any
import numpy as np
from scipy.signal import find_peaks

from shared.models.domain import FramePose
from shared.utils.constants import MediaPipeLandmarks
from .base_calculator import BaseMetricsCalculator


class SymmetryCalculator(BaseMetricsCalculator):
    """Calculator for left–right symmetry score (0–1)."""

    def calculate(self, pose_data: List[FramePose]) -> Dict[str, Any]:
        if len(pose_data) < 20:
            return {"left_right_symmetry": 0.0}

        # Get ankle Y arrays
        left_foot = self.get_landmark_positions(pose_data, MediaPipeLandmarks.LEFT_ANKLE.value)
        right_foot = self.get_landmark_positions(pose_data, MediaPipeLandmarks.RIGHT_ANKLE.value)

        left_y = self.smooth_signal(left_foot[:, 1])
        right_y = self.smooth_signal(right_foot[:, 1])

        # Find ground-contact peaks
        left_peaks, _ = find_peaks(-left_y, height=0.01, distance=5)
        right_peaks, _ = find_peaks(-right_y, height=0.01, distance=5)

        total_steps = len(left_peaks) + len(right_peaks)
        if total_steps == 0:
            return {"left_right_symmetry": 0.0}

        symmetry_score = 1.0 - abs(len(left_peaks) - len(right_peaks)) / total_steps
        symmetry_score = max(0.0, symmetry_score)  # clamp

        return {
            "left_right_symmetry": symmetry_score,
            "left_steps": len(left_peaks),
            "right_steps": len(right_peaks)
        } 