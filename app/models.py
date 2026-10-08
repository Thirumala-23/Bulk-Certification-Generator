"""SQLAlchemy ORM models for jobs and certificates."""

import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class JobStatus(str, enum.Enum):
    """Enumeration of bulk job statuses."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    FAILED = "FAILED"


class CertificateStatus(str, enum.Enum):
    """Enumeration of individual certificate generation statuses."""
    PENDING = "PENDING"
    GENERATED = "GENERATED"
    FAILED = "FAILED"


def get_utc_now() -> datetime:
    """Returns current datetime in UTC (naive for SQLite compatibility)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Job(Base):
    """Represents a bulk certificate generation job."""
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_name = Column(String(150), nullable=False)
    completion_date = Column(String(50), nullable=False)
    organizer_name = Column(String(100), nullable=False)
    
    status = Column(String(30), default=JobStatus.PENDING.value, nullable=False, index=True)
    total_recipients = Column(Integer, default=0, nullable=False)
    successful_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationship to certificates
    certificates = relationship(
        "Certificate",
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def pending_count(self) -> int:
        """Dynamically calculates remaining pending certificates."""
        return max(0, self.total_recipients - (self.successful_count + self.failed_count))

    @property
    def progress_percentage(self) -> float:
        """Dynamically calculates completion percentage (0.0 to 100.0)."""
        if self.total_recipients == 0:
            return 100.0
        processed = self.successful_count + self.failed_count
        return round((processed / self.total_recipients) * 100.0, 2)


class Certificate(Base):
    """Represents an individual personalized certificate."""
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_name = Column(String(100), nullable=False)
    recipient_email = Column(String(150), nullable=False)
    
    status = Column(String(30), default=CertificateStatus.PENDING.value, nullable=False, index=True)
    file_path = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationship back to job
    job = relationship("Job", back_populates="certificates")
