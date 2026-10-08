"""Tests for bulk generation job creation, validation, status tracking, and error handling."""

from unittest.mock import patch
from fastapi.testclient import TestClient
from app.models import Job, Certificate, JobStatus, CertificateStatus


def test_create_bulk_job_success(client: TestClient):
    """Test successful creation and execution of a bulk certificate job."""
    payload = {
        "event_name": "Full Stack Python Bootcamp",
        "completion_date": "October 15, 2026",
        "organizer_name": "Global Tech Institute",
        "recipients": [
            {"name": "Alice Johnson", "email": "alice@example.com"},
            {"name": "Bob Smith", "email": "bob@example.com"},
        ],
    }

    response = client.post("/api/jobs/", json=payload)
    assert response.status_code == 202
    data = response.json()

    assert "id" in data
    assert data["event_name"] == payload["event_name"]
    assert data["organizer_name"] == payload["organizer_name"]
    assert data["total_recipients"] == 2

    job_id = data["id"]

    # Verify status via GET /api/jobs/{job_id}
    status_response = client.get(f"/api/jobs/{job_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()

    assert status_data["id"] == job_id
    assert status_data["status"] == JobStatus.COMPLETED.value
    assert status_data["total_recipients"] == 2
    assert status_data["successful_count"] == 2
    assert status_data["failed_count"] == 0
    assert status_data["pending_count"] == 0
    assert status_data["progress_percentage"] == 100.0


def test_create_job_validation_empty_event_name(client: TestClient):
    """Whole request must be rejected if event name is blank or missing."""
    payload = {
        "event_name": "   ",
        "completion_date": "2026-10-15",
        "organizer_name": "Tech Corp",
        "recipients": [{"name": "Alice", "email": "alice@example.com"}],
    }
    response = client.post("/api/jobs/", json=payload)
    assert response.status_code == 422


def test_create_job_validation_empty_recipients_list(client: TestClient):
    """Whole request must be rejected if recipients list is empty."""
    payload = {
        "event_name": "Cybersecurity Workshop",
        "completion_date": "2026-10-15",
        "organizer_name": "Tech Corp",
        "recipients": [],
    }
    response = client.post("/api/jobs/", json=payload)
    assert response.status_code == 422


def test_create_job_skips_invalid_email_and_executes_valid(client: TestClient):
    """If a recipient has an invalid email, it must be skipped and marked FAILED while valid recipients succeed."""
    payload = {
        "event_name": "Cloud Computing Seminar",
        "completion_date": "2026-10-15",
        "organizer_name": "Tech Corp",
        "recipients": [
            {"name": "Valid User", "email": "valid@example.com"},
            {"name": "Invalid User", "email": "not-an-email"},
        ],
    }
    response = client.post("/api/jobs/", json=payload)
    assert response.status_code == 202
    job_id = response.json()["id"]

    # Verify job status transitioned to COMPLETED_WITH_ERRORS
    status_response = client.get(f"/api/jobs/{job_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()

    assert status_data["status"] == JobStatus.COMPLETED_WITH_ERRORS.value
    assert status_data["total_recipients"] == 2
    assert status_data["successful_count"] == 1
    assert status_data["failed_count"] == 1

    # Verify certificate details
    certs_res = client.get(f"/api/jobs/{job_id}/certificates")
    assert certs_res.status_code == 200
    certs = certs_res.json()["certificates"]

    valid_cert = next(c for c in certs if c["recipient_name"] == "Valid User")
    assert valid_cert["status"] == CertificateStatus.GENERATED.value
    assert valid_cert["download_url"] is not None

    invalid_cert = next(c for c in certs if c["recipient_name"] == "Invalid User")
    assert invalid_cert["status"] == CertificateStatus.FAILED.value
    assert "Invalid email" in invalid_cert["error_message"]
    assert invalid_cert["download_url"] is None


def test_create_job_validation_blank_recipient_name(client: TestClient):
    """Whole request must be rejected if a recipient name is empty or spaces only."""
    payload = {
        "event_name": "Cloud Computing Seminar",
        "completion_date": "2026-10-15",
        "organizer_name": "Tech Corp",
        "recipients": [
            {"name": "   ", "email": "user@example.com"},
        ],
    }
    response = client.post("/api/jobs/", json=payload)
    assert response.status_code == 422


def test_get_job_status_unknown_id(client: TestClient):
    """Non-existent job ID should return 404."""
    response = client.get("/api/jobs/non-existent-uuid-12345")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_certificates_for_job(client: TestClient):
    """Test listing certificates and checking status and download URLs."""
    payload = {
        "event_name": "AI Foundations",
        "completion_date": "2026-10-10",
        "organizer_name": "AI Lab",
        "recipients": [
            {"name": "Charlie Brown", "email": "charlie@example.com"},
        ],
    }
    res = client.post("/api/jobs/", json=payload)
    assert res.status_code == 202
    job_id = res.json()["id"]

    certs_res = client.get(f"/api/jobs/{job_id}/certificates")
    assert certs_res.status_code == 200
    certs_data = certs_res.json()

    assert certs_data["job_id"] == job_id
    assert certs_data["total_certificates"] == 1
    cert_item = certs_data["certificates"][0]
    assert cert_item["recipient_name"] == "Charlie Brown"
    assert cert_item["recipient_email"] == "charlie@example.com"
    assert cert_item["status"] == CertificateStatus.GENERATED.value
    assert cert_item["download_url"] == f"/api/certificates/{cert_item['id']}"


def test_list_certificates_unknown_job(client: TestClient):
    """Listing certificates for non-existent job must return 404."""
    res = client.get("/api/jobs/missing-job-id/certificates")
    assert res.status_code == 404


def test_partial_failure_isolation(client: TestClient):
    """
    Simulate a scenario where one recipient fails during PDF generation,
    while other recipients succeed.
    Verifies that failure does not halt processing, and the job transitions to COMPLETED_WITH_ERRORS.
    """
    from app.services.job_processor import generate_certificate_pdf as orig_generate

    def mock_generate_with_single_failure(**kwargs):
        if kwargs.get("recipient_name") == "Error Recipient":
            raise RuntimeError("Simulated PDF generator engine crash")
        return orig_generate(**kwargs)

    payload = {
        "event_name": "Resilience Engineering",
        "completion_date": "2026-10-12",
        "organizer_name": "DevOps Hub",
        "recipients": [
            {"name": "Good Recipient 1", "email": "good1@example.com"},
            {"name": "Error Recipient", "email": "error@example.com"},
            {"name": "Good Recipient 2", "email": "good2@example.com"},
        ],
    }

    with patch("app.services.job_processor.generate_certificate_pdf", side_effect=mock_generate_with_single_failure):
        response = client.post("/api/jobs/", json=payload)
        assert response.status_code == 202
        job_id = response.json()["id"]

    # Check job metrics
    job_res = client.get(f"/api/jobs/{job_id}")
    assert job_res.status_code == 200
    job_data = job_res.json()

    assert job_data["status"] == JobStatus.COMPLETED_WITH_ERRORS.value
    assert job_data["total_recipients"] == 3
    assert job_data["successful_count"] == 2
    assert job_data["failed_count"] == 1
    assert job_data["pending_count"] == 0

    # Check individual certificates list
    certs_res = client.get(f"/api/jobs/{job_id}/certificates")
    assert certs_res.status_code == 200
    cert_items = certs_res.json()["certificates"]

    by_name = {c["recipient_name"]: c for c in cert_items}
    assert by_name["Good Recipient 1"]["status"] == CertificateStatus.GENERATED.value
    assert by_name["Good Recipient 1"]["download_url"] is not None

    assert by_name["Error Recipient"]["status"] == CertificateStatus.FAILED.value
    assert by_name["Error Recipient"]["download_url"] is None
    assert "Simulated PDF generator engine crash" in by_name["Error Recipient"]["error_message"]

    assert by_name["Good Recipient 2"]["status"] == CertificateStatus.GENERATED.value
    assert by_name["Good Recipient 2"]["download_url"] is not None


def test_all_recipients_failing_sets_status_failed(client: TestClient):
    """When all recipients fail during generation, job status must become FAILED."""
    def fail_all(**kwargs):
        raise OSError("Disk out of space")

    payload = {
        "event_name": "Failure Testing",
        "completion_date": "2026-10-12",
        "organizer_name": "DevOps Hub",
        "recipients": [
            {"name": "User One", "email": "user1@example.com"},
            {"name": "User Two", "email": "user2@example.com"},
        ],
    }

    with patch("app.services.job_processor.generate_certificate_pdf", side_effect=fail_all):
        response = client.post("/api/jobs/", json=payload)
        assert response.status_code == 202
        job_id = response.json()["id"]

    job_res = client.get(f"/api/jobs/{job_id}")
    assert job_res.status_code == 200
    job_data = job_res.json()

    assert job_data["status"] == JobStatus.FAILED.value
    assert job_data["total_recipients"] == 2
    assert job_data["successful_count"] == 0
    assert job_data["failed_count"] == 2


def test_create_job_exceeds_max_recipients_limit(client: TestClient):
    """Whole request must be rejected if recipient count exceeds MAX_RECIPIENTS_PER_JOB (500)."""
    payload = {
        "event_name": "Mega Conference",
        "completion_date": "2026-10-12",
        "organizer_name": "Mega Corp",
        "recipients": [{"name": f"User {i}", "email": f"user{i}@example.com"} for i in range(501)],
    }
    response = client.post("/api/jobs/", json=payload)
    assert response.status_code == 422
