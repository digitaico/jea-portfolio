from typing import List, Dict, Any
import numpy as np

from shared.models.domain import FramePose
from shared.utils.constants import MediaPipeLandmarks
from .base_calculator import BaseMetricsCalculator

# Using a simple average of selected key landmarks as center of gravity.
_KEY_LANDMARKS = [
    MediaPipeLandmarks.LEFT_HIP.value,
    MediaPipeLandmarks.RIGHT_HIP.value,
    MediaPipeLandmarks.LEFT_SHOULDER.value,
    MediaPipeLandmarks.RIGHT_SHOULDER.value,
    MediaPipeLandmarks.LEFT_KNEE.value,
    MediaPipeLandmarks.RIGHT_KNEE.value,
]


class CenterOfGravityCalculator(BaseMetricsCalculator):
    """Calculator for center-of-gravity position (normalized coords)."""

    def calculate(self, pose_data: List[FramePose]) -> Dict[str, Any]:
        if not pose_data:
            return {"center_of_gravity": {"x": 0.0, "y": 0.0, "z": 0.0}}

        xs, ys, zs = [], [], []
        for frame in pose_data:
            coords = []
            for idx in _KEY_LANDMARKS:
                if idx < len(frame.landmarks):
                    lm = frame.landmarks[idx]
                    coords.append([lm.x, lm.y, lm.z])
            if coords:
                coords_np = np.array(coords)
                cog = coords_np.mean(axis=0)
                xs.append(cog[0])
                ys.append(cog[1])
                zs.append(cog[2])

        center = {
            "x": float(np.mean(xs)) if xs else 0.0,
            "y": float(np.mean(ys)) if ys else 0.0,
            "z": float(np.mean(zs)) if zs else 0.0,
        }

        return {"center_of_gravity": center} 