"""Background processing worker for executing certificate generation jobs."""

import logging
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from app.config import CERTIFICATES_DIR, BASE_DIR
from app import database
from email_validator import validate_email, EmailNotValidError
from app.models import Job, Certificate, JobStatus, CertificateStatus, get_utc_now
from app.services.certificate_generator import generate_certificate_pdf

logger = logging.getLogger(__name__)


def process_bulk_job(
    job_id: str,
    db_factory=None,
    output_dir: Optional[Path] = None,
) -> None:
    """
    Executes a bulk certificate generation job in the background.

    - Updates job status to PROCESSING.
    - Generates personalized PDF for each recipient sequentially.
    - Isolates failures per recipient so one bad certificate does not halt the batch.
    - Updates database progress in real-time as each certificate completes.
    - Transitions job to COMPLETED, COMPLETED_WITH_ERRORS, or FAILED.

    Args:
        job_id: The UUID of the job to process.
        db_factory: Optional SQLAlchemy sessionmaker factory. If None, uses app.database.SessionLocal.
        output_dir: Optional target directory for generated certificates (defaults to CERTIFICATES_DIR).
    """
    target_dir = output_dir if output_dir is not None else CERTIFICATES_DIR
    factory = db_factory if db_factory is not None else database.SessionLocal
    db: Session = factory()

    try:
        job: Optional[Job] = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error("Job with ID %s not found in database for background processing.", job_id)
            return

        # Mark job as PROCESSING
        job.status = JobStatus.PROCESSING.value
        job.updated_at = get_utc_now()
        db.commit()
        db.refresh(job)

        # Retrieve all pending certificates for this job
        certificates = (
            db.query(Certificate)
            .filter(Certificate.job_id == job_id)
            .order_by(Certificate.created_at.asc())
            .all()
        )

        for cert in certificates:
            # Validate recipient email format; if invalid, skip generation and isolate failure
            try:
                validate_email(cert.recipient_email, check_deliverability=False)
            except EmailNotValidError as email_err:
                logger.warning(
                    "Skipping certificate %s for %s due to invalid email '%s': %s",
                    cert.id,
                    cert.recipient_name,
                    cert.recipient_email,
                    email_err,
                )
                cert.status = CertificateStatus.FAILED.value
                cert.error_message = f"Invalid email format: {email_err}"
                cert.file_path = None
                job.failed_count += 1
                cert.updated_at = get_utc_now()
                job.updated_at = get_utc_now()
                db.commit()
                continue

            try:
                # Generate the PDF certificate
                pdf_path = generate_certificate_pdf(
                    recipient_name=cert.recipient_name,
                    event_name=job.event_name,
                    completion_date=job.completion_date,
                    organizer_name=job.organizer_name,
                    certificate_id=cert.id,
                    output_dir=target_dir,
                )

                # Store relative path safe from arbitrary machine root disclosure
                try:
                    rel_path = str(pdf_path.relative_to(BASE_DIR))
                except ValueError:
                    rel_path = str(pdf_path)

                cert.file_path = rel_path
                cert.status = CertificateStatus.GENERATED.value
                cert.error_message = None
                job.successful_count += 1

            except Exception as exc:
                logger.warning(
                    "Failed to generate certificate %s for %s: %s",
                    cert.id,
                    cert.recipient_name,
                    str(exc),
                )
                cert.status = CertificateStatus.FAILED.value
                cert.error_message = str(exc)
                cert.file_path = None
                job.failed_count += 1

            cert.updated_at = get_utc_now()
            job.updated_at = get_utc_now()
            # Commit after each recipient for incremental progress visibility
            db.commit()

        # Update final job status
        db.refresh(job)
        if job.total_recipients == 0:
            job.status = JobStatus.COMPLETED.value
        elif job.successful_count == job.total_recipients:
            job.status = JobStatus.COMPLETED.value
        elif job.successful_count > 0 and job.failed_count > 0:
            job.status = JobStatus.COMPLETED_WITH_ERRORS.value
        else:
            job.status = JobStatus.FAILED.value

        job.updated_at = get_utc_now()
        db.commit()
        logger.info(
            "Completed bulk job %s: status=%s, success=%d, failed=%d",
            job.id,
            job.status,
            job.successful_count,
            job.failed_count,
        )

    except Exception as exc:
        logger.exception("Critical error processing bulk job %s: %s", job_id, exc)
        try:
            db.rollback()
            failed_job = db.query(Job).filter(Job.id == job_id).first()
            if failed_job:
                failed_job.status = JobStatus.FAILED.value
                failed_job.updated_at = get_utc_now()
                db.commit()
        except Exception as rollback_err:
            logger.error("Failed to mark job %s as FAILED: %s", job_id, rollback_err)
    finally:
        db.close()
