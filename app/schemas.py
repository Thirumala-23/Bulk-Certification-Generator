"""Pydantic schemas for request validation and response serialization."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.config import MAX_RECIPIENTS_PER_JOB, MIN_RECIPIENTS_PER_JOB


class RecipientCreate(BaseModel):
    """Schema for individual recipient input."""
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full name of the recipient (non-empty)",
        examples=["Jane Doe"],
    )
    email: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Email address for the recipient",
        examples=["jane.doe@example.com"],
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Recipient name must not be blank or only whitespace.")
        return trimmed


class JobCreate(BaseModel):
    """Schema for creating a new bulk certificate generation job."""
    event_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Name of the course, event, or workshop",
        examples=["Full Stack Web Development Bootcamp"],
    )
    completion_date: str = Field(
        ...,
        min_length=4,
        max_length=50,
        description="Date of event completion (e.g., '2026-10-15' or 'October 15, 2026')",
        examples=["October 15, 2026"],
    )
    organizer_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Name of the organizer, instructor, or issuing entity",
        examples=["TechNova Academy"],
    )
    recipients: List[RecipientCreate] = Field(
        ...,
        min_length=MIN_RECIPIENTS_PER_JOB,
        max_length=MAX_RECIPIENTS_PER_JOB,
        description=f"List of certificate recipients (between {MIN_RECIPIENTS_PER_JOB} and {MAX_RECIPIENTS_PER_JOB})",
    )

    @field_validator("event_name", "completion_date", "organizer_name")
    @classmethod
    def validate_fields_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Field must not be blank or only whitespace.")
        return trimmed


class JobResponse(BaseModel):
    """Basic response schema when a job is created or queued."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_name: str
    completion_date: str
    organizer_name: str
    status: str
    total_recipients: int
    successful_count: int
    failed_count: int
    pending_count: int
    created_at: datetime
    updated_at: datetime
    message: Optional[str] = None


class JobDetailResponse(JobResponse):
    """Detailed response schema including progress metrics."""
    progress_percentage: float = Field(
        ...,
        description="Percentage of recipients processed so far (0.0 to 100.0)",
        examples=[100.0],
    )


class CertificateResponse(BaseModel):
    """Schema representing an individual certificate."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    recipient_name: str
    recipient_email: str
    status: str
    error_message: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CertificateListResponse(BaseModel):
    """Schema for listing all certificates belonging to a job."""
    job_id: str
    total_certificates: int
    certificates: List[CertificateResponse]
