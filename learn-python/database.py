"""
Database models and connection setup using SQLAlchemy.
Handles PostgreSQL connection and image transformation history.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Text, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List
import json

from config import get_database_url

# Create SQLAlchemy base class with custom schema
metadata = MetaData(schema='image_processor')
Base = declarative_base(metadata=metadata)


class TransformationHistory(Base):
    """Model for storing image transformation history."""
    
    __tablename__ = "transformation_history"
    __table_args__ = {'schema': 'image_processor'}
    
    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, nullable=False)
    transformation_type = Column(String, nullable=False)
    parameters = Column(JSON, nullable=True)
    output_path = Column(String, nullable=True)
    processing_time = Column(Integer, nullable=True)  # in milliseconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<TransformationHistory(id={self.id}, type={self.transformation_type}, image={self.image_path})>"


class DatabaseManager:
    """Database manager for handling connections and operations."""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._setup_database()
    
    def _setup_database(self):
        """Setup database connection and create schema and tables."""
        try:
            database_url = get_database_url()
            self.engine = create_engine(database_url, echo=False)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create schema first
            with self.engine.connect() as connection:
                from sqlalchemy import text
                connection.execute(text("CREATE SCHEMA IF NOT EXISTS image_processor"))
                connection.commit()
            
            # Create tables in the new schema
            Base.metadata.create_all(bind=self.engine)
            print("✅ Database connection established and schema 'image_processor' created with tables")
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("Please check your PostgreSQL connection and .env file")
    
    def get_session(self) -> Session:
        """Get database session with schema search path set."""
        if not self.SessionLocal:
            raise Exception("Database not initialized")
        session = self.SessionLocal()
        # Set the search path to use the image_processor schema
        from sqlalchemy import text
        session.execute(text("SET search_path TO image_processor, public"))
        return session
    
    def save_transformation(
        self,
        image_path: str,
        transformation_type: str,
        parameters: Optional[dict] = None,
        output_path: Optional[str] = None,
        processing_time: Optional[int] = None
    ) -> Optional[TransformationHistory]:
        """Save transformation history to database."""
        try:
            with self.get_session() as session:
                transformation = TransformationHistory(
                    image_path=image_path,
                    transformation_type=transformation_type,
                    parameters=parameters or {},
                    output_path=output_path,
                    processing_time=processing_time
                )
                session.add(transformation)
                session.commit()
                session.refresh(transformation)
                return transformation
                
        except Exception as e:
            print(f"❌ Error saving transformation: {e}")
            return None
    
    def get_transformation_history(
        self,
        limit: int = 100,
        offset: int = 0,
        transformation_type: Optional[str] = None
    ) -> List[TransformationHistory]:
        """Get transformation history with optional filtering."""
        try:
            with self.get_session() as session:
                query = session.query(TransformationHistory)
                
                if transformation_type:
                    query = query.filter(TransformationHistory.transformation_type == transformation_type)
                
                return query.order_by(TransformationHistory.created_at.desc()).offset(offset).limit(limit).all()
                
        except Exception as e:
            print(f"❌ Error retrieving transformation history: {e}")
            return []
    
    def get_transformation_by_id(self, transformation_id: int) -> Optional[TransformationHistory]:
        """Get transformation by ID."""
        try:
            with self.get_session() as session:
                return session.query(TransformationHistory).filter(TransformationHistory.id == transformation_id).first()
                
        except Exception as e:
            print(f"❌ Error retrieving transformation: {e}")
            return None
    
    def delete_transformation(self, transformation_id: int) -> bool:
        """Delete transformation by ID."""
        try:
            with self.get_session() as session:
                transformation = session.query(TransformationHistory).filter(TransformationHistory.id == transformation_id).first()
                if transformation:
                    session.delete(transformation)
                    session.commit()
                    return True
                return False
                
        except Exception as e:
            print(f"❌ Error deleting transformation: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager() 