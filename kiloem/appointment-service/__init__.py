"""
Appointment Service Package
Provides appointment management functionality with REST API and event publishing.
"""

from .main import app
from .api.routes import router
from .core.business_logic import AppointmentService
from .models.appointment import Appointment, AppointmentCreate, AppointmentUpdate

__version__ = "1.0.0"
__all__ = ["app", "router", "AppointmentService", "Appointment", "AppointmentCreate", "AppointmentUpdate"]