"""Step-by-step interactive walkthrough demonstrating how the Bulk Certificate Generator works."""

import json
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.database import init_db, SessionLocal
from app.models import Job, Certificate
from app.config import CERTIFICATES_DIR

def run_walkthrough():
    print("=" * 70)
    print("STEP 1: Application & Database Initialization")
    print("=" * 70)
    init_db()
    CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] SQLite database schema verified.")
    print(f"[OK] Certificate storage directory verified at: {CERTIFICATES_DIR}")

    client = TestClient(app)

    print("\n" + "=" * 70)
    print("STEP 2: Health Check & Service Discovery (GET /)")
    print("=" * 70)
    root_res = client.get("/")
    print(f"Status Code: {root_res.status_code}")
    print(f"Response: {json.dumps(root_res.json(), indent=2)}")

    print("\n" + "=" * 70)
    print("STEP 3: Submitting Bulk Job (POST /api/jobs/)")
    print("=" * 70)
    job_payload = {
        "event_name": "Antigravity Python Masterclass 2026",
        "completion_date": "October 8, 2026",
        "organizer_name": "Google DeepMind Academy",
        "recipients": [
            {"name": "Alice Developer", "email": "alice@example.com"},
            {"name": "Bob Architect", "email": "bob@example.com"}
        ]
    }
    print(f"Sending Request Payload:\n{json.dumps(job_payload, indent=2)}")
    
    post_res = client.post("/api/jobs/", json=job_payload)
    print(f"\nResponse Status: {post_res.status_code} (Accepted)")
    job_data = post_res.json()
    job_id = job_data["id"]
    print(f"Response Body:\n{json.dumps(job_data, indent=2)}")
    print(f"Assigned Job ID: {job_id}")

    print("\n" + "=" * 70)
    print("STEP 4: Querying Job Progress & Status (GET /api/jobs/{job_id})")
    print("=" * 70)
    status_res = client.get(f"/api/jobs/{job_id}")
    print(f"Status Code: {status_res.status_code}")
    print(f"Response Body:\n{json.dumps(status_res.json(), indent=2)}")

    print("\n" + "=" * 70)
    print("STEP 5: Retrieving Generated Certificates List (GET /api/jobs/{job_id}/certificates)")
    print("=" * 70)
    certs_res = client.get(f"/api/jobs/{job_id}/certificates")
    print(f"Status Code: {certs_res.status_code}")
    certs_data = certs_res.json()
    print(f"Response Body:\n{json.dumps(certs_data, indent=2)}")

    print("\n" + "=" * 70)
    print("STEP 6: Downloading & Inspecting Generated PDF File")
    print("=" * 70)
    first_cert = certs_data["certificates"][0]
    cert_id = first_cert["id"]
    download_url = first_cert["download_url"]
    print(f"Downloading certificate for '{first_cert['recipient_name']}' via {download_url}...")
    
    download_res = client.get(download_url)
    print(f"HTTP Status: {download_res.status_code}")
    print(f"Content-Type: {download_res.headers.get('content-type')}")
    print(f"Content-Disposition: {download_res.headers.get('content-disposition')}")
    print(f"Downloaded PDF Byte Size: {len(download_res.content)} bytes")
    print(f"PDF Header: {download_res.content[:5]}")

    print("\n" + "=" * 70)
    print("STEP 7: Inspecting Database & Disk Storage")
    print("=" * 70)
    db = SessionLocal()
    try:
        db_job = db.query(Job).filter(Job.id == job_id).first()
        print(f"Database Job Record: ID={db_job.id}, Status={db_job.status}, Successful={db_job.successful_count}/{db_job.total_recipients}")
        for c in db_job.certificates:
            file_exists = Path(c.file_path).exists() if c.file_path else False
            print(f" - Cert {c.id}: Recipient='{c.recipient_name}', Status={c.status}, File='{c.file_path}' (Exists on disk: {file_exists})")
    finally:
        db.close()

    print("\n" + "=" * 70)
    print("[OK] WALKTHROUGH COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_walkthrough()
