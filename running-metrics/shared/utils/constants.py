from enum import Enum


class MediaPipeLandmarks(Enum):
    """MediaPipe pose landmark indices"""
    NOSE = 0
    LEFT_EYE_INNER = 1
    LEFT_EYE = 2
    LEFT_EYE_OUTER = 3
    RIGHT_EYE_INNER = 4
    RIGHT_EYE = 5
    RIGHT_EYE_OUTER = 6
    LEFT_EAR = 7
    RIGHT_EAR = 8
    MOUTH_LEFT = 9
    MOUTH_RIGHT = 10
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_PINKY = 17
    RIGHT_PINKY = 18
    LEFT_INDEX = 19
    RIGHT_INDEX = 20
    LEFT_THUMB = 21
    RIGHT_THUMB = 22
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_HEEL = 29
    RIGHT_HEEL = 30
    LEFT_FOOT_INDEX = 31
    RIGHT_FOOT_INDEX = 32


class RunningConstants:
    """Constants for running analysis"""
    MIN_CONFIDENCE_THRESHOLD = 0.5
    MIN_VISIBILITY_THRESHOLD = 0.5
    SMOOTHING_WINDOW_SIZE = 5
    MIN_VIDEO_FPS = 15
    MIN_VIDEO_DURATION = 5.0  # seconds
    MAX_VIDEO_DURATION = 300.0  # seconds
    MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
    
    # Anatomical constants
    AVERAGE_STRIDE_HEIGHT_RATIO = 0.45  # stride length / height
    AVERAGE_STEP_HEIGHT_RATIO = 0.225   # step length / height