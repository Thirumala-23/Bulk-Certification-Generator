# Bulk Certificate Generator Backend

A complete, beginner-friendly, and production-ready Python backend application built for an internship assignment. This service accepts bulk recipient lists, generates personalized, tamper-evident PDF certificates in landscape format using **ReportLab**, processes tasks asynchronously in the background using **FastAPI BackgroundTasks**, and tracks execution statuses with **SQLite** and **SQLAlchemy ORM**.

---

## 1. Project Overview & Features

When organizing hackathons, bootcamps, workshops, or academic conferences, manual certificate issuance is time-consuming and error-prone. The **Bulk Certificate Generator** solves this by offering an automated, resilient batch-generation system.

### Key Features
- **Bulk Processing via Single Request**: Submit event details and a list of up to 500 recipients in a single `POST /api/jobs/` request.
- **Asynchronous Non-Blocking Execution**: Jobs are accepted immediately (HTTP 202) with a unique Job ID while certificate generation happens in the background.
- **Fault-Tolerant & Isolated Failures**: If one recipient's certificate generation encounters an issue, subsequent recipients continue uninterrupted.
- **Granular Status Tracking**: Detailed tracking across `PENDING`, `PROCESSING`, `COMPLETED`, `COMPLETED_WITH_ERRORS`, and `FAILED` states, including real-time progress percentages and pending counts.
- **Professional PDF Certificate Design**: Standard landscape US Letter layout generated dynamically with ReportLab, featuring double borders, decorative accents, verification seals, and typography.
- **Secure File Storage & Streaming**: Clean, collision-resistant UUID-based filenames stored locally with traversal protection. Files are safely served via `GET /api/certificates/{certificate_id}` without exposing underlying server paths.
- **Full Test Coverage**: 100% automated test suite using `pytest` and `FastAPI TestClient` covering positive flows, validation errors, partial failure isolation, and edge cases.

---

## 2. Technology Stack

| Technology | Purpose |
| :--- | :--- |
| **Python 3.10+** (tested on 3.14) | Core programming language |
| **FastAPI** | High-performance, asynchronous web framework for RESTful APIs |
| **Uvicorn** | ASGI web server for running the FastAPI application |
| **SQLite** | Lightweight, zero-configuration relational database |
| **SQLAlchemy 2.0** | Object-Relational Mapping (ORM) and database session management |
| **Pydantic v2** | Data modeling, strict request validation, and response serialization |
| **ReportLab** | Vector graphics and PDF rendering engine for generating certificates |
| **Pytest & HTTPX** | Automated testing suite and mock client for API integration tests |

---

## 3. Project Structure

```text
bulk_certification/
├── .gitignore                     # Git ignore rules for virtualenv, DB, and PDFs
├── requirements.txt               # Pinned project dependencies
├── README.md                      # Comprehensive project documentation
├── generated_certificates/        # Storage directory for generated PDF files
│   └── .gitkeep                   # Directory placeholder for Git
├── app/
│   ├── __init__.py                # App package initializer
│   ├── config.py                  # Storage paths, SQLite URL, and validation limits
│   ├── database.py                # SQLAlchemy engine, session maker, and get_db dependency
│   ├── models.py                  # SQLAlchemy ORM models (Job, Certificate) and Enums
│   ├── schemas.py                 # Pydantic request and response validation schemas
│   ├── main.py                    # FastAPI application setup, CORS, and lifespan hooks
│   ├── routes/
│   │   ├── __init__.py            # Routes package initializer
│   │   ├── jobs.py                # POST /api/jobs/, GET status, GET certificates list
│   │   └── certificates.py        # GET /api/certificates/{id} download endpoint
│   └── services/
│       ├── __init__.py            # Services package initializer
│       ├── certificate_generator.py # ReportLab PDF canvas drawing and layout logic
│       └── job_processor.py       # Background worker for batch processing & DB updates
└── tests/
    ├── __init__.py                # Test package initializer
    ├── conftest.py                # Pytest fixtures, isolated SQLite DB, and temp storage
    ├── test_jobs.py               # Job creation, validation, status tracking & partial failure
    ├── test_certificates.py       # PDF downloading, header verification, and 400/404 handling
    └── test_generator.py          # Direct ReportLab unit tests and edge cases
```

---

## 4. Windows Setup Instructions Using a Virtual Environment

Open **PowerShell** or **Command Prompt** and follow these steps:

### Step 1: Clone or Navigate to the Project Directory
```powershell
cd C:\Users\kthir\OneDrive\Pictures\Documents\projects\bulk_certification
```

### Step 2: Create a Python Virtual Environment
Creating a virtual environment ensures project dependencies do not conflict with system packages:
```powershell
python -m venv .venv
```

### Step 3: Activate the Virtual Environment
On Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell displays an execution policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once, or activate via Command Prompt using `.\.venv\Scripts\activate.bat`)*

When activated, you will see `(.venv)` in your terminal prompt.

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## 5. Installation & Run Commands

### Run the FastAPI Development Server
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once running:
- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

---

## 6. API Endpoints

| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Service health check and endpoint overview | `200 OK` |
| `POST` | `/api/jobs/` | Submit a bulk certificate generation job | `202 Accepted` |
| `GET` | `/api/jobs/{job_id}` | Retrieve job status, counts, and progress percentage | `200 OK` / `404 Not Found` |
| `GET` | `/api/jobs/{job_id}/certificates` | List all certificates and their individual statuses | `200 OK` / `404 Not Found` |
| `GET` | `/api/certificates/{certificate_id}` | Download the generated PDF certificate | `200 OK` / `400` / `404` |

---

## 7. Example Requests and Responses

### 1. Create a Bulk Generation Job (`POST /api/jobs/`)
**Request Body**:
```json
{
  "event_name": "Full Stack Cloud & DevOps Bootcamp",
  "completion_date": "October 15, 2026",
  "organizer_name": "TechNova Academy",
  "recipients": [
    {
      "name": "Jane Doe",
      "email": "jane.doe@example.com"
    },
    {
      "name": "John Smith",
      "email": "john.smith@example.com"
    }
  ]
}
```

**Response (`202 Accepted`)**:
```json
{
  "id": "e4f8b91c-8b89-4b68-98f5-19e913a52148",
  "event_name": "Full Stack Cloud & DevOps Bootcamp",
  "completion_date": "October 15, 2026",
  "organizer_name": "TechNova Academy",
  "status": "PENDING",
  "total_recipients": 2,
  "successful_count": 0,
  "failed_count": 0,
  "pending_count": 2,
  "created_at": "2026-10-07T13:30:00",
  "updated_at": "2026-10-07T13:30:00",
  "message": "Job accepted. Certificate generation has been scheduled in the background."
}
```

---

### 2. Check Job Status (`GET /api/jobs/{job_id}`)
**Response (`200 OK`)**:
```json
{
  "id": "e4f8b91c-8b89-4b68-98f5-19e913a52148",
  "event_name": "Full Stack Cloud & DevOps Bootcamp",
  "completion_date": "October 15, 2026",
  "organizer_name": "TechNova Academy",
  "status": "COMPLETED",
  "total_recipients": 2,
  "successful_count": 2,
  "failed_count": 0,
  "pending_count": 0,
  "created_at": "2026-10-07T13:30:00",
  "updated_at": "2026-10-07T13:30:02",
  "progress_percentage": 100.0,
  "message": null
}
```

---

### 3. List Certificates for Job (`GET /api/jobs/{job_id}/certificates`)
**Response (`200 OK`)**:
```json
{
  "job_id": "e4f8b91c-8b89-4b68-98f5-19e913a52148",
  "total_certificates": 2,
  "certificates": [
    {
      "id": "761d4924-a212-4099-a4a3-cbbab793a6c9",
      "job_id": "e4f8b91c-8b89-4b68-98f5-19e913a52148",
      "recipient_name": "Jane Doe",
      "recipient_email": "jane.doe@example.com",
      "status": "GENERATED",
      "error_message": null,
      "download_url": "/api/certificates/761d4924-a212-4099-a4a3-cbbab793a6c9",
      "created_at": "2026-10-07T13:30:00",
      "updated_at": "2026-10-07T13:30:01"
    },
    {
      "id": "67b931dc-cb16-43ad-8d96-c148cf378b27",
      "job_id": "e4f8b91c-8b89-4b68-98f5-19e913a52148",
      "recipient_name": "John Smith",
      "recipient_email": "john.smith@example.com",
      "status": "GENERATED",
      "error_message": null,
      "download_url": "/api/certificates/67b931dc-cb16-43ad-8d96-c148cf378b27",
      "created_at": "2026-10-07T13:30:00",
      "updated_at": "2026-10-07T13:30:02"
    }
  ]
}
```

---

### 4. Download Certificate (`GET /api/certificates/{certificate_id}`)
- Returns binary stream with Content-Type `application/pdf`
- Sets `Content-Disposition: attachment; filename="Certificate_Jane_Doe_761d4924.pdf"`
- Displays or downloads directly in browser/client.

---

## 8. How to Test the APIs Using Swagger UI

1. Open your browser and navigate to: `http://127.0.0.1:8000/docs`.
2. Expand the **`POST /api/jobs/`** section and click **Try it out**.
3. Paste an example payload into the request body and click **Execute**.
4. Note the returned `"id"` (Job ID) in the response.
5. Expand **`GET /api/jobs/{job_id}`**, click **Try it out**, paste the `"id"`, and click **Execute** to view real-time progress and final status.
6. Expand **`GET /api/jobs/{job_id}/certificates`** and execute with the same Job ID. Copy any certificate ID.
7. Expand **`GET /api/certificates/{certificate_id}`**, paste the certificate ID, and click **Execute**. Click **Download file** to open and view the generated PDF certificate!

---

## 9. How to Run Pytest

The project contains 19 comprehensive unit and integration tests. Run the test suite using:

```powershell
.\.venv\Scripts\pytest -v
```

### Verified Test Suite Breakdown:
- **`test_create_bulk_job_success`**: Validates end-to-end job creation, background execution, and status transitions.
- **`test_create_job_validation_*`**: Verifies whole-request rejection (HTTP 422) for blank event names, empty recipient lists, blank recipient names, and exceeding maximum bounds.
- **`test_create_job_skips_invalid_email_and_executes_valid`**: Verifies that invalid emails are isolated and marked FAILED without halting valid recipients.
- **`test_get_job_status_unknown_id`**: Verifies HTTP 404 response on unknown Job IDs.
- **`test_list_certificates_for_job`**: Verifies listing certificates, download URLs, and status mappings.
- **`test_partial_failure_isolation`**: Simulates single recipient generator crash while others succeed; ensures job transitions to `COMPLETED_WITH_ERRORS`.
- **`test_all_recipients_failing_sets_status_failed`**: Tests fallback when every recipient fails.
- **`test_download_generated_certificate_success`**: Confirms PDF header bytes (`%PDF-`), valid Content-Type, and download headers.
- **`test_download_pending_certificate` & `test_download_failed_certificate`**: Confirms HTTP 400 Bad Request with explanatory error message.
- **`test_download_missing_file_on_disk`**: Confirms HTTP 404 when database record exists but file is missing.
- **`test_generate_certificate_pdf_*`**: Tests ReportLab canvas generation, error triggers, and long text resilience.

---

## 10. Database and File Storage Explanation

### Database Architecture (SQLite + SQLAlchemy ORM)
1. **`jobs` table**:
   - `id`: UUID string primary key.
   - `event_name`, `completion_date`, `organizer_name`: Metadata strings.
   - `status`: String state (`PENDING`, `PROCESSING`, `COMPLETED`, `COMPLETED_WITH_ERRORS`, `FAILED`).
   - `total_recipients`, `successful_count`, `failed_count`: Integer metrics.
   - `created_at`, `updated_at`: UTC timestamps.
2. **`certificates` table**:
   - `id`: UUID string primary key.
   - `job_id`: Foreign key referencing `jobs.id` with `ondelete="CASCADE"`.
   - `recipient_name`, `recipient_email`: Validated recipient info.
   - `status`: Generation status (`PENDING`, `GENERATED`, `FAILED`).
   - `file_path`: Relative disk location of the generated PDF.
   - `error_message`: Captured exception message if generation failed.
   - `created_at`, `updated_at`: UTC timestamps.

### File Storage Security
- All certificates are stored in `generated_certificates/`.
- File naming format: `cert_{certificate_id}.pdf`.
- User input is **never** used in file paths or directory traversal.
- The download endpoint verifies that the resolved target path exists strictly within the allowed directory and streams the file safely without exposing internal server folder paths.

---

## 11. Architecture and Processing Flow

```mermaid
flowchart TD
    Client([Client / Frontend]) -->|1. POST /api/jobs/| API[FastAPI Route Handler]
    API -->|2. Validate Schema| Pydantic[Pydantic Models]
    Pydantic -->|Valid Payload| DBInit[(SQLite Database)]
    DBInit -->|Job + Certificates saved as PENDING| Background[FastAPI BackgroundTasks]
    API -->|3. Return HTTP 202 with Job ID| Client

    Background -->|4. Trigger process_bulk_job| Worker[Background Worker]
    Worker -->|Update Status: PROCESSING| DBInit

    subgraph Loop [For each recipient in Job]
        Worker -->|Call generator| Gen[ReportLab PDF Engine]
        Gen -->|Generate PDF| Disk[(generated_certificates/)]
        Gen -->|Success| DBInit
        Gen -->|Failure| Catch[Catch Exception & record error_message]
        Catch --> DBInit
    end

    Worker -->|5. Update Final Status| DBInit
    Client -->|6. GET /api/jobs/{id}| API
    Client -->|7. GET /api/certificates/{id}| FileStream[Download PDF Stream]
```

### Validation Strategy: Request-Level vs. Recipient-Level
- **Whole-Request Rejection (HTTP 422)**:
  - If the event name is empty or whitespace.
  - If the completion date or organizer name is missing or blank.
  - If the recipients list is empty (`< 1`) or exceeds the bulk limit (`> 500`).
  - If any recipient name is blank or missing.
  *Rationale*: Structural payload errors and missing essential event details must be rejected upfront before creating jobs.
- **Individual Recipient Failure & Isolation (Recorded in DB)**:
  - **Invalid email formats**: If a recipient's email address is malformed (missing `@` or invalid domain), the background worker isolates the issue, marks that recipient's status as `FAILED` with an explanatory error message, skips their PDF generation, and continues processing the rest of the batch.
  - **Generation crashes**: If a specific PDF write fails (disk IO glitch, unrenderable characters), that recipient is marked `FAILED` while remaining certificates continue.
  *Rationale*: In bulk issuance, one faulty email or recipient record should never cancel or halt the valid recipients.

---

## 12. Design Decisions & Alternatives

1. **FastAPI BackgroundTasks vs. Celery / Redis**:
   - *Decision*: Used FastAPI `BackgroundTasks`.
   - *Rationale*: For an internship assignment and small-to-medium workloads, `BackgroundTasks` requires zero external infrastructure (no Redis or RabbitMQ service to configure on Windows). It runs natively in the process while maintaining clean code separation.
2. **SQLite vs. PostgreSQL**:
   - *Decision*: SQLite with SQLAlchemy.
   - *Rationale*: Zero-setup, file-based relational database that is fully standard across Windows, macOS, and Linux. Enabled `check_same_thread=False` to safely support multi-threaded background writes.
3. **ReportLab Canvas Drawing vs. HTML-to-PDF (WeasyPrint/wkhtmltopdf)**:
   - *Decision*: Direct ReportLab canvas drawing.
   - *Rationale*: Direct vector drawing has zero external OS binaries (unlike wkhtmltopdf or cairo/pango dependencies for WeasyPrint on Windows), executes in milliseconds, and produces crisp, vector-sharp certificates.
4. **Isolated Test Fixtures**:
   - *Decision*: Using `tmp_path` to create temporary test databases and certificate folders.
   - *Rationale*: Prevents automated tests from polluting runtime databases and disk folders.

---

## 13. Known Limitations

- **Single Worker Threading**: `BackgroundTasks` runs inside the same Python process. If the server is forcibly terminated while a job is running, in-flight jobs remain in `PROCESSING` state unless a startup reconciliation job is implemented.
- **Single Server Storage**: Generated PDFs are saved to the local filesystem. In a multi-instance cloud cluster, a shared object store (e.g., AWS S3, Google Cloud Storage, or MinIO) would be used.

---

## 14. What I Learned

- Designing asynchronous background pipelines in FastAPI and decoupling long-running workloads from HTTP request-response cycles.
- Managing database sessions cleanly between request handlers and background tasks using SQLAlchemy session factories.
- Structuring strict schema validation rules using Pydantic v2 field validators.
- Building vector graphics and typography programmatically using ReportLab.
- Writing isolated, deterministic unit and integration test fixtures using `pytest` and dependency injection overrides.

---

## 15. Future Scope

- **Email Dispatching**: Automatically email certificates as PDF attachments to recipients using an asynchronous SMTP service.
- **Custom Certificate Badges & Logos**: Allow organizers to upload custom logos and dynamic signatures.
- **Distributed Queues**: Integrate Celery or ARQ with Redis for distributed multi-worker scaling across servers.
- **Verification Portal**: A public QR code on the certificate linking to a public verification webpage (`/verify/{certificate_id}`).
