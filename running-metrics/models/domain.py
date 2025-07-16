from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class RunnerProfile:
    gender: str  # "male" or "female"
    height_cm: float
    email: str
    
    
@dataclass
class KeyPoint:
    x: float
    y: float
    visibility: float
    
    
@dataclass
class Frame:
    timestamp: float
    keypoints: Dict[str, KeyPoint]
    frame_number: int
    

@dataclass
class GaitMetrics:
    cadence: Optional[float] = None
    stride_length: Optional[float] = None
    ground_contact_time: Optional[float] = None
    flight_time: Optional[float] = None
    vertical_oscillation: Optional[float] = None
    forward_lean: Optional[float] = None
    left_right_symmetry: Optional[float] = None
    speed: Optional[float] = None