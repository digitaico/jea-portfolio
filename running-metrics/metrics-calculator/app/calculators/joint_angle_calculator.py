from typing import List, Dict, Any
import numpy as np

from shared.models.domain import FramePose
from shared.utils.constants import MediaPipeLandmarks
from .base_calculator import BaseMetricsCalculator

_JOINTS = {
    "left_knee": [MediaPipeLandmarks.LEFT_HIP.value, MediaPipeLandmarks.LEFT_KNEE.value, MediaPipeLandmarks.LEFT_ANKLE.value],
    "right_knee": [MediaPipeLandmarks.RIGHT_HIP.value, MediaPipeLandmarks.RIGHT_KNEE.value, MediaPipeLandmarks.RIGHT_ANKLE.value],
    "left_elbow": [MediaPipeLandmarks.LEFT_SHOULDER.value, MediaPipeLandmarks.LEFT_ELBOW.value, MediaPipeLandmarks.LEFT_WRIST.value],
    "right_elbow": [MediaPipeLandmarks.RIGHT_SHOULDER.value, MediaPipeLandmarks.RIGHT_ELBOW.value, MediaPipeLandmarks.RIGHT_WRIST.value],
}


class JointAngleCalculator(BaseMetricsCalculator):
    """Calculator for joint angles across gait cycle."""

    def calculate(self, pose_data: List[FramePose]) -> Dict[str, Any]:
        if not pose_data:
            return {"joint_angles": {}}

        angle_series: Dict[str, List[float]] = {name: [] for name in _JOINTS.keys()}

        for frame in pose_data:
            for name, (i1, i2, i3) in _JOINTS.items():
                if max(i1, i2, i3) >= len(frame.landmarks):
                    continue
                p1 = np.array([frame.landmarks[i1].x, frame.landmarks[i1].y, frame.landmarks[i1].z])
                p2 = np.array([frame.landmarks[i2].x, frame.landmarks[i2].y, frame.landmarks[i2].z])
                p3 = np.array([frame.landmarks[i3].x, frame.landmarks[i3].y, frame.landmarks[i3].z])

                angle = self.calculate_angle(p1, p2, p3)
                angle_series[name].append(angle)

        # Reduce to average angle per joint
        joint_angles_avg = {name: float(np.mean(angles)) if angles else 0.0 for name, angles in angle_series.items()}

        return {"joint_angles": joint_angles_avg} 