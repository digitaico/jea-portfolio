from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, JSON, 
    Enum as SQLEnum, Boolean, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from shared.models.domain import Gender, ProcessingStatus

Base = declarative_base()


class RunningSessionDB(Base):
    """Database model for running sessions"""
    __tablename__ = "running_sessions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Video metadata
    video_filename = Column(String(255), nullable=False)
    video_file_size = Column(Integer, nullable=False)
    video_duration = Column(Float, nullable=False)
    video_fps = Column(Float, nullable=False)
    video_width = Column(Integer, nullable=False)
    video_height = Column(Integer, nullable=False)
    video_format = Column(String(50), nullable=False)
    
    # Runner profile
    runner_gender = Column(SQLEnum(Gender), nullable=False)
    runner_height_cm = Column(Integer, nullable=False)
    runner_age = Column(Integer, nullable=False)
    runner_email = Column(String(255), nullable=False)
    
    # Processing status
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processing_time = Column(Float, nullable=True)
    
    # Relationships
    pose_data = relationship("PoseDataDB", back_populates="session", cascade="all, delete-orphan")
    metrics = relationship("RunningMetricsDB", back_populates="session", uselist=False)

class PoseDataDB(Base):
    """Database model for pose detection data"""
    __tablename__ = "pose_data"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("running_sessions.id"), nullable=False)
    
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)
    landmarks = Column(JSON, nullable=False)  # List of landmark coordinates
    confidence = Column(Float, nullable=False)
    
    # Relationship
    session = relationship("RunningSessionDB", back_populates="pose_data")


class RunningMetricsDB(Base):
    """Database model for calculated running metrics"""
    __tablename__ = "running_metrics"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("running_sessions.id"), nullable=False)
    
    cadence = Column(Float, nullable=False)
    speed = Column(Float, nullable=False)
    step_length = Column(Float, nullable=False)
    stride_length = Column(Float, nullable=False)
    ground_contact_time = Column(Float, nullable=False)
    flight_time = Column(Float, nullable=False)
    vertical_oscillation = Column(Float, nullable=False)
    forward_lean = Column(Float, nullable=False)
    left_right_symmetry = Column(Float, nullable=False)
    center_of_gravity = Column(JSON, nullable=False)
    joint_angles = Column(JSON, nullable=False)
    
    # Relationship
    session = relationship("RunningSessionDB", back_populates="metrics")