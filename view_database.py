"""Helper script to inspect all rows and tables in the SQLite database."""

import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent / "bulk_certificates.db"

def display_database():
    if not DB_FILE.exists():
        print(f"Database file not found at {DB_FILE}")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("=" * 80)
    print(f"DATABASE FILE: {DB_FILE}")
    print("=" * 80)

    # 1. Inspect Jobs Table
    print("\n[TABLE: jobs]")
    cursor.execute("SELECT id, event_name, status, total_recipients, successful_count, failed_count, created_at FROM jobs")
    jobs = cursor.fetchall()
    if not jobs:
        print("  (No jobs recorded yet)")
    else:
        print(f"  {'Job ID':<38} | {'Status':<22} | {'Success/Total':<13} | Event Name")
        print("  " + "-" * 100)
        for job in jobs:
            jid, event, status, total, success, failed, created = job
            counts = f"{success}/{total} (fail:{failed})"
            print(f"  {jid:<38} | {status:<22} | {counts:<13} | {event}")

    # 2. Inspect Certificates Table
    print("\n[TABLE: certificates]")
    cursor.execute("SELECT id, job_id, recipient_name, recipient_email, status, file_path, error_message FROM certificates")
    certs = cursor.fetchall()
    if not certs:
        print("  (No certificates recorded yet)")
    else:
        print(f"  {'Cert ID':<38} | {'Status':<10} | {'Recipient Name':<20} | {'Email':<25} | Details / File")
        print("  " + "-" * 115)
        for c in certs:
            cid, jid, name, email, status, fpath, err = c
            detail = fpath if status == "GENERATED" else f"Err: {err}"
            print(f"  {cid:<38} | {status:<10} | {name:<20} | {email:<25} | {detail}")

    print("\n" + "=" * 80)
    conn.close()

if __name__ == "__main__":
    display_database()
