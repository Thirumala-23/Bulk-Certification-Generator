from pathlib import Path

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Storage directory for generated PDF certificates
CERTIFICATES_DIR = BASE_DIR / "generated_certificates"
CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)

# SQLite database configuration
DATABASE_URL = "sqlite:///./bulk_certificates.db"

# Validation limits
MAX_RECIPIENTS_PER_JOB = 500
MIN_RECIPIENTS_PER_JOB = 1
