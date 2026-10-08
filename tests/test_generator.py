"""Direct unit tests for ReportLab PDF generator service."""

import pytest
from pathlib import Path
from app.services.certificate_generator import generate_certificate_pdf


def test_generate_certificate_pdf_creates_valid_file(tmp_path: Path):
    """Test generating a certificate PDF directly and checking file validity."""
    cert_id = "unit-test-12345"
    file_path = generate_certificate_pdf(
        recipient_name="Grace Hopper",
        event_name="Advanced Computer Science",
        completion_date="October 20, 2026",
        organizer_name="Pioneer Institute",
        certificate_id=cert_id,
        output_dir=tmp_path,
    )

    assert file_path.exists()
    assert file_path.is_file()
    assert file_path.name == f"cert_{cert_id}.pdf"
    assert file_path.stat().st_size > 1000

    # Validate PDF content header
    with open(file_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"


def test_generate_certificate_pdf_missing_arguments(tmp_path: Path):
    """Test that missing mandatory fields raise ValueError."""
    with pytest.raises(ValueError, match="required"):
        generate_certificate_pdf(
            recipient_name="",
            event_name="Test Event",
            completion_date="2026-10-20",
            organizer_name="Org",
            certificate_id="123",
            output_dir=tmp_path,
        )


def test_generate_certificate_pdf_handles_long_names(tmp_path: Path):
    """Test that unusually long recipient or event names generate without throwing layout errors."""
    file_path = generate_certificate_pdf(
        recipient_name="Dr. Alexandria Elizabeth Montgomery-Wellington III",
        event_name="International Symposium on Advanced Distributed Quantum Machine Learning Systems",
        completion_date="November 30, 2026",
        organizer_name="Global Consortium for Advanced Computational Research",
        certificate_id="long-name-test-999",
        output_dir=tmp_path,
    )
    assert file_path.exists()
    assert file_path.stat().st_size > 1000
