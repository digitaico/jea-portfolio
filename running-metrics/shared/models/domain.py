from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, EmailStr, validator


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RunnerProfile(BaseModel):
    """Runner profile information"""
    gender: Gender
    height_cm: int = Field(..., ge=50, le=230, description="Height in centimeters")
    age: int = Field(..., ge=10, le=125, description="Age in years")
    email: EmailStr
    
    @validator('height_cm')
    def validate_height(cls, v):
        if not 50 <= v <= 230:
            raise ValueError('Height must be between 50 and 230 cm')
        return v


class PoseLandmark(BaseModel):
    """Individual pose landmark"""
    x: float = Field(..., ge=0.0, le=1.0, description="Normalized x coordinate")
    y: float = Field(..., ge=0.0, le=1.0, description="Normalized y coordinate")
    z: float = Field(..., description="Depth coordinate")
    visibility: float = Field(..., ge=0.0, le=1.0, description="Visibility score")


class FramePose(BaseModel):
    """Pose data for a single frame"""
    frame_number: int
    timestamp: float
    landmarks: List[PoseLandmark]
    confidence: float = Field(..., ge=0.0, le=1.0)


class RunningMetrics(BaseModel):
    """Calculated running metrics"""
    cadence: float = Field(..., ge=0, description="Steps per minute")
    speed: float = Field(..., ge=0, description="Speed in m/s")
    step_length: float = Field(..., ge=0, description="Average step length in meters")
    stride_length: float = Field(..., ge=0, description="Average stride length in meters")
    ground_contact_time: float = Field(..., ge=0, description="Ground contact time in seconds")
    flight_time: float = Field(..., ge=0, description="Flight time in seconds")
    vertical_oscillation: float = Field(..., ge=0, description="Vertical oscillation in meters")
    forward_lean: float = Field(..., description="Forward lean angle in degrees")
    left_right_symmetry: float = Field(..., ge=0, le=1, description="Symmetry score")
    center_of_gravity: Dict[str, float] = Field(..., description="Center of gravity coordinates")
    joint_angles: Dict[str, List[float]] = Field(..., description="Joint angles throughout gait cycle")


class VideoMetadata(BaseModel):
    """Video file metadata"""
    filename: str
    file_size: int
    duration: float
    fps: float
    width: int
    height: int
    format: str
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)


class RunningSession(BaseModel):
    """Main running analysis session"""
    id: UUID = Field(default_factory=uuid4)
    video_metadata: VideoMetadata
    runner_profile: RunnerProfile
    status: ProcessingStatus = ProcessingStatus.PENDING
    pose_data: Optional[List[FramePose]] = None
    metrics: Optional[RunningMetrics] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time: Optional[float] = None
    
    class Config:
        use_enum_values = True


class AnalysisRequest(BaseModel):
    """Request model for analysis"""
    runner_profile: RunnerProfile
    video_filename: str


class AnalysisResponse(BaseModel):
    """Response model for analysis"""
    session_id: UUID
    status: ProcessingStatus
    message: str


class ProcessingProgress(BaseModel):
    """Progress update model"""
    session_id: UUID
    status: ProcessingStatus
    progress_percentage: float = Field(..., ge=0, le=100)
    current_step: str
    estimated_time_remaining: Optional[float] = None