from abc import ABC, abstractmethod
from typing import Dict
import numpy as np
from ..models.domain import KeyPoint


class PoseDetector(ABC):
    @abstractmethod
    def detect_pose(self, frame: np.ndarray) -> Dict[str, KeyPoint]:
        pass