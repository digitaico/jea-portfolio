from typing import List, Dict, Any
import numpy as np

from shared.models.domain import FramePose
from shared.utils.constants import MediaPipeLandmarks
from .base_calculator import BaseMetricsCalculator


class LeanAngleCalculator(BaseMetricsCalculator):
    """Calculator for average forward-lean angle (degrees)."""

    def calculate(self, pose_data: List[FramePose]) -> Dict[str, Any]:
        """Compute the average trunk angle relative to vertical over all frames."""
        if len(pose_data) < 10:
            return {"forward_lean": 0.0}

        angles = []
        vertical_vec = np.array([0.0, -1.0, 0.0])  # pointing up in image coordinates (y decreases upwards)

        for frame in pose_data:
            # need shoulder center and hip center
            if (MediaPipeLandmarks.LEFT_SHOULDER.value >= len(frame.landmarks) or
                MediaPipeLandmarks.RIGHT_SHOULDER.value >= len(frame.landmarks) or
                MediaPipeLandmarks.LEFT_HIP.value >= len(frame.landmarks) or
                MediaPipeLandmarks.RIGHT_HIP.value >= len(frame.landmarks)):
                continue

            # shoulder center
            left_sh = frame.landmarks[MediaPipeLandmarks.LEFT_SHOULDER.value]
            right_sh = frame.landmarks[MediaPipeLandmarks.RIGHT_SHOULDER.value]
            shoulder_center = np.array([(left_sh.x + right_sh.x) / 2.0,
                                         (left_sh.y + right_sh.y) / 2.0,
                                         (left_sh.z + right_sh.z) / 2.0])
            # hip center
            left_hip = frame.landmarks[MediaPipeLandmarks.LEFT_HIP.value]
            right_hip = frame.landmarks[MediaPipeLandmarks.RIGHT_HIP.value]
            hip_center = np.array([(left_hip.x + right_hip.x) / 2.0,
                                    (left_hip.y + right_hip.y) / 2.0,
                                    (left_hip.z + right_hip.z) / 2.0])

            trunk_vec = shoulder_center - hip_center  # vector from hip to shoulder
            norm = np.linalg.norm(trunk_vec)
            if norm == 0:
                continue
            trunk_vec_norm = trunk_vec / norm

            # Angle between trunk vector and vertical vector
            cos_theta = np.dot(trunk_vec_norm, vertical_vec)
            cos_theta = np.clip(cos_theta, -1.0, 1.0)
            angle_deg = np.degrees(np.arccos(cos_theta))
            angles.append(angle_deg)

        avg_angle = float(np.mean(angles)) if angles else 0.0
        return {"forward_lean": avg_angle} 