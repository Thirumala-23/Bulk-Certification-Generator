"""Certificate PDF generation service using ReportLab."""

from pathlib import Path
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from app.config import CERTIFICATES_DIR


def generate_certificate_pdf(
    recipient_name: str,
    event_name: str,
    completion_date: str,
    organizer_name: str,
    certificate_id: str,
    output_dir: Path = CERTIFICATES_DIR,
) -> Path:
    """
    Generates a personalized, professional landscape PDF certificate.

    Args:
        recipient_name: Full name of the recipient.
        event_name: Title of the completed event/course.
        completion_date: Formatted date of completion.
        organizer_name: Name of the event organizer/instructor.
        certificate_id: Unique UUID of the certificate.
        output_dir: Target directory for storing the PDF file.

    Returns:
        Path: The absolute path to the generated PDF file.

    Raises:
        ValueError: If parameters are invalid or path traversal is detected.
        IOError: If file writing fails.
    """
    if not recipient_name or not event_name or not certificate_id:
        raise ValueError("Recipient name, event name, and certificate ID are required.")

    # Guarantee output directory exists
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Safe filename generation based purely on UUID to prevent path traversal
    safe_filename = f"cert_{certificate_id}.pdf"
    file_path = (output_dir / safe_filename).resolve()

    # Safety check: ensure file_path is strictly inside output_dir
    if not str(file_path).startswith(str(output_dir)):
        raise ValueError("Invalid target path detected. Path traversal rejected.")

    # Page setup: Standard US Letter in Landscape (792 x 612 pt)
    page_width, page_height = landscape(letter)
    c = canvas.Canvas(str(file_path), pagesize=(page_width, page_height))
    c.setTitle(f"Certificate - {recipient_name}")
    c.setAuthor(organizer_name)
    c.setSubject(event_name)

    # Color Palette
    navy_dark = HexColor("#0F172A")    # Deep slate navy
    navy_blue = HexColor("#1E3A8A")    # Primary rich blue
    gold = HexColor("#D97706")         # Warm gold accent
    slate_dark = HexColor("#1E293B")   # Header text
    slate_muted = HexColor("#64748B")  # Subtitles and labels
    slate_body = HexColor("#475569")   # Descriptive body text
    border_cream = HexColor("#F8FAFC") # Inner background tint
    gray_line = HexColor("#CBD5E1")    # Subtle signature lines

    center_x = page_width / 2.0

    # 1. Background tint
    c.setFillColor(border_cream)
    c.rect(15, 15, page_width - 30, page_height - 30, stroke=0, fill=1)

    # 2. Outer Border (Deep Navy, 3.5pt)
    c.setStrokeColor(navy_dark)
    c.setLineWidth(3.5)
    c.rect(28, 28, page_width - 56, page_height - 56, stroke=1, fill=0)

    # 3. Inner Decorative Border (Gold, 1.5pt)
    c.setStrokeColor(gold)
    c.setLineWidth(1.5)
    c.rect(38, 38, page_width - 76, page_height - 76, stroke=1, fill=0)

    # 4. Corner Accents (Decorative Gold Diamonds)
    corner_offset = 38
    corner_size = 6
    for cx, cy in [
        (corner_offset, corner_offset),
        (page_width - corner_offset, corner_offset),
        (corner_offset, page_height - corner_offset),
        (page_width - corner_offset, page_height - corner_offset),
    ]:
        p = c.beginPath()
        p.moveTo(cx, cy - corner_size)
        p.lineTo(cx + corner_size, cy)
        p.lineTo(cx, cy + corner_size)
        p.lineTo(cx - corner_size, cy)
        p.close()
        c.setFillColor(gold)
        c.drawPath(p, fill=1, stroke=0)

    # 5. Top Header Badge
    c.setFillColor(gold)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(center_x, page_height - 95, "★ ★ ★   OFFICIAL CITATION OF ACHIEVEMENT   ★ ★ ★")

    # 6. Main Title
    c.setFillColor(navy_dark)
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(center_x, page_height - 145, "CERTIFICATE OF COMPLETION")

    # 7. Presentation Subtitle
    c.setFillColor(slate_muted)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(center_x, page_height - 185, "THIS IS PROUDLY PRESENTED TO")

    # 8. Recipient Name
    c.setFillColor(navy_blue)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(center_x, page_height - 235, recipient_name)

    # Gold Decorative Line under Recipient Name
    name_line_width = max(240.0, min(500.0, len(recipient_name) * 16.0))
    c.setStrokeColor(gold)
    c.setLineWidth(1.5)
    c.line(
        center_x - (name_line_width / 2.0),
        page_height - 248,
        center_x + (name_line_width / 2.0),
        page_height - 248,
    )

    # 9. Body Explanation
    c.setFillColor(slate_body)
    c.setFont("Helvetica", 12)
    c.drawCentredString(
        center_x,
        page_height - 280,
        "for successfully participating in and fulfilling all requirements of",
    )

    # 10. Event Name
    c.setFillColor(slate_dark)
    c.setFont("Helvetica-Bold", 19)
    c.drawCentredString(center_x, page_height - 315, event_name)

    # 11. Footer Section (Signatures & Verification)
    sig_line_y = 155
    sig_text_y = 170
    sig_label_y = 138

    # Left: Completion Date
    date_center_x = 180
    c.setStrokeColor(gray_line)
    c.setLineWidth(1)
    c.line(date_center_x - 90, sig_line_y, date_center_x + 90, sig_line_y)

    c.setFillColor(slate_dark)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(date_center_x, sig_text_y, completion_date)

    c.setFillColor(slate_muted)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(date_center_x, sig_label_y, "DATE OF COMPLETION")

    # Center: Seal / Verified Emblem
    c.setFillColor(HexColor("#F1F5F9"))
    c.circle(center_x, 155, 30, fill=1, stroke=0)
    c.setStrokeColor(gold)
    c.setLineWidth(1.5)
    c.circle(center_x, 155, 27, fill=0, stroke=1)
    c.setFillColor(navy_blue)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(center_x, 158, "VERIFIED")
    c.setFont("Helvetica", 7)
    c.drawCentredString(center_x, 147, "CREDENTIAL")

    # Right: Organizer Signature Area
    org_center_x = page_width - 180
    c.setStrokeColor(gray_line)
    c.setLineWidth(1)
    c.line(org_center_x - 90, sig_line_y, org_center_x + 90, sig_line_y)

    c.setFillColor(slate_dark)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(org_center_x, sig_text_y, organizer_name)

    c.setFillColor(slate_muted)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(org_center_x, sig_label_y, "AUTHORIZED ORGANIZER")

    # 12. Bottom Certificate ID & Security Reference
    c.setFillColor(slate_muted)
    c.setFont("Helvetica", 8)
    c.drawCentredString(
        center_x,
        65,
        f"Certificate ID: {certificate_id}   •   Tamper-Evident Digital Document",
    )

    # Save PDF
    c.showPage()
    c.save()

    return file_path
