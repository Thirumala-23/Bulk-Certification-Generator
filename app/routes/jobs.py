"""API endpoints for managing bulk certificate jobs."""

import uuid
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job, Certificate, JobStatus, CertificateStatus
from app.schemas import JobCreate, JobResponse, JobDetailResponse, CertificateResponse, CertificateListResponse
from app.services.job_processor import process_bulk_job

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


@router.post(
    "/",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a bulk certificate generation job",
    description=(
        "Accepts event details and a list of recipients. Validates the entire payload, "
        "records the job and recipient entries as PENDING, initiates background processing, "
        "and immediately returns the job ID."
    ),
)
def create_bulk_job(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> JobResponse:
    """Creates a new job and enqueues generation in the background."""
    new_job = Job(
        id=str(uuid.uuid4()),
        event_name=payload.event_name,
        completion_date=payload.completion_date,
        organizer_name=payload.organizer_name,
        status=JobStatus.PENDING.value,
        total_recipients=len(payload.recipients),
        successful_count=0,
        failed_count=0,
    )
    db.add(new_job)

    # Pre-populate all certificate records in PENDING status
    for item in payload.recipients:
        cert = Certificate(
            id=str(uuid.uuid4()),
            job_id=new_job.id,
            recipient_name=item.name,
            recipient_email=str(item.email),
            status=CertificateStatus.PENDING.value,
        )
        db.add(cert)

    db.commit()
    db.refresh(new_job)

    # Dispatch background worker
    background_tasks.add_task(process_bulk_job, new_job.id)

    response_data = JobResponse.model_validate(new_job)
    response_data.message = (
        "Job accepted. Certificate generation has been scheduled in the background."
    )
    return response_data


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="Get job status and progress",
    description="Retrieves current status, metrics, and progress percentage for a bulk generation job.",
)
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
) -> JobDetailResponse:
    """Fetches job details by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found.",
        )

    return JobDetailResponse.model_validate(job)


@router.get(
    "/{job_id}/certificates",
    response_model=CertificateListResponse,
    summary="List certificates for a job",
    description="Lists all certificates for a specified job along with their generation statuses and download URLs.",
)
def get_job_certificates(
    job_id: str,
    db: Session = Depends(get_db),
) -> CertificateListResponse:
    """Lists certificates and download URLs for a job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found.",
        )

    certs: List[Certificate] = (
        db.query(Certificate)
        .filter(Certificate.job_id == job_id)
        .order_by(Certificate.created_at.asc())
        .all()
    )

    cert_responses = []
    for c in certs:
        resp = CertificateResponse.model_validate(c)
        if c.status == CertificateStatus.GENERATED.value:
            resp.download_url = f"/api/certificates/{c.id}"
        cert_responses.append(resp)

    return CertificateListResponse(
        job_id=job.id,
        total_certificates=len(cert_responses),
        certificates=cert_responses,
    )
