"""API endpoints for retrieving and downloading individual certificates."""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import BASE_DIR, CERTIFICATES_DIR
from app.database import get_db
from app.models import Certificate, CertificateStatus

router = APIRouter(prefix="/api/certificates", tags=["Certificates"])


@router.get(
    "/{certificate_id}",
    response_class=FileResponse,
    summary="Download certificate PDF",
    description="Downloads the generated PDF file for a valid, generated certificate.",
)
def download_certificate(
    certificate_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves and streams the generated certificate PDF file."""
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' not found.",
        )

    if cert.status == CertificateStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificate generation is still pending or currently processing.",
        )

    if cert.status == CertificateStatus.FAILED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate generation failed: {cert.error_message or 'Unknown generation error'}",
        )

    if not cert.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate file path is not recorded.",
        )

    # Resolve file path safely
    candidate_path = Path(cert.file_path)
    if not candidate_path.is_absolute():
        resolved_path = (BASE_DIR / candidate_path).resolve()
    else:
        resolved_path = candidate_path.resolve()

    # Verify that file actually exists
    if not resolved_path.exists() or not resolved_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate PDF file was not found on disk.",
        )

    # Sanitize download filename for the browser
    clean_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in cert.recipient_name)
    download_filename = f"Certificate_{clean_name}_{cert.id[:8]}.pdf"

    return FileResponse(
        path=str(resolved_path),
        media_type="application/pdf",
        filename=download_filename,
    )
