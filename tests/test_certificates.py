"""Tests for certificate retrieval, PDF file streaming, and download edge cases."""

import uuid
from fastapi.testclient import TestClient
from app.models import Certificate, Job, JobStatus, CertificateStatus


def test_download_generated_certificate_success(client: TestClient):
    """Test downloading a generated certificate PDF file."""
    # 1. Create a job to generate a certificate
    payload = {
        "event_name": "Cloud Security Masterclass",
        "completion_date": "2026-10-18",
        "organizer_name": "CyberSec Institute",
        "recipients": [
            {"name": "Diana Prince", "email": "diana@example.com"},
        ],
    }
    job_res = client.post("/api/jobs/", json=payload)
    assert job_res.status_code == 202
    job_id = job_res.json()["id"]

    # 2. Get certificate list to find certificate ID
    certs_res = client.get(f"/api/jobs/{job_id}/certificates")
    assert certs_res.status_code == 200
    cert = certs_res.json()["certificates"][0]
    cert_id = cert["id"]

    # 3. Download the PDF
    download_res = client.get(f"/api/certificates/{cert_id}")
    assert download_res.status_code == 200
    assert download_res.headers["content-type"] == "application/pdf"
    assert "attachment" in download_res.headers.get("content-disposition", "").lower()
    
    # Verify standard PDF header bytes
    content = download_res.content
    assert content.startswith(b"%PDF-")
    assert len(content) > 500


def test_download_unknown_certificate_id(client: TestClient):
    """Attempting to download a non-existent certificate ID must return 404."""
    unknown_id = str(uuid.uuid4())
    res = client.get(f"/api/certificates/{unknown_id}")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_download_pending_certificate(client: TestClient, db_session):
    """Attempting to download a certificate while still PENDING must return 400."""
    # Manually seed a PENDING certificate into DB
    job = Job(
        id=str(uuid.uuid4()),
        event_name="Draft Workshop",
        completion_date="2026-10-20",
        organizer_name="Org",
        status=JobStatus.PENDING.value,
        total_recipients=1,
    )
    db_session.add(job)

    cert_id = str(uuid.uuid4())
    cert = Certificate(
        id=cert_id,
        job_id=job.id,
        recipient_name="Pending Recipient",
        recipient_email="pending@example.com",
        status=CertificateStatus.PENDING.value,
        file_path=None,
    )
    db_session.add(cert)
    db_session.commit()

    res = client.get(f"/api/certificates/{cert_id}")
    assert res.status_code == 400
    assert "pending" in res.json()["detail"].lower()


def test_download_failed_certificate(client: TestClient, db_session):
    """Attempting to download a certificate marked FAILED must return 400 with error details."""
    job = Job(
        id=str(uuid.uuid4()),
        event_name="Failed Job",
        completion_date="2026-10-20",
        organizer_name="Org",
        status=JobStatus.FAILED.value,
        total_recipients=1,
    )
    db_session.add(job)

    cert_id = str(uuid.uuid4())
    cert = Certificate(
        id=cert_id,
        job_id=job.id,
        recipient_name="Failed Recipient",
        recipient_email="fail@example.com",
        status=CertificateStatus.FAILED.value,
        file_path=None,
        error_message="Font rendering failure",
    )
    db_session.add(cert)
    db_session.commit()

    res = client.get(f"/api/certificates/{cert_id}")
    assert res.status_code == 400
    assert "failed" in res.json()["detail"].lower()
    assert "Font rendering failure" in res.json()["detail"]


def test_download_missing_file_on_disk(client: TestClient, db_session):
    """If DB records GENERATED but the file was deleted on disk, return 404."""
    job = Job(
        id=str(uuid.uuid4()),
        event_name="Ghost Event",
        completion_date="2026-10-20",
        organizer_name="Org",
        status=JobStatus.COMPLETED.value,
        total_recipients=1,
    )
    db_session.add(job)

    cert_id = str(uuid.uuid4())
    cert = Certificate(
        id=cert_id,
        job_id=job.id,
        recipient_name="Ghost User",
        recipient_email="ghost@example.com",
        status=CertificateStatus.GENERATED.value,
        file_path="generated_certificates/non_existent_file.pdf",
    )
    db_session.add(cert)
    db_session.commit()

    res = client.get(f"/api/certificates/{cert_id}")
    assert res.status_code == 404
    assert "not found on disk" in res.json()["detail"].lower()
