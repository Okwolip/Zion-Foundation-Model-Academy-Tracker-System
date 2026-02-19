from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
import os


def generate_student_statement(
    student_name,
    section,
    student_class,
    session,
    previous_outstanding,
    current_fee,
    total_paid,
    amount_owed
):
    # Clean file name (important for Streamlit Cloud)
    safe_name = student_name.replace(" ", "_")
    file_name = f"{safe_name}_statement.pdf"

    c = canvas.Canvas(file_name, pagesize=letter)
    width, height = letter

    y = height - 60

    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, y, "STUDENT FINANCIAL STATEMENT")

    y -= 50

    c.setFont("Helvetica", 12)

    # Student Info
    c.drawString(50, y, f"Student Name: {student_name}")
    y -= 25
    c.drawString(50, y, f"Class: {student_class}")
    y -= 25
    c.drawString(50, y, f"Section: {section}")
    y -= 25
    c.drawString(50, y, f"Session: {session}")

    y -= 40

    # Financial Breakdown
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, "Financial Summary")
    y -= 30

    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Previous Outstanding: ₦{previous_outstanding:,.2f}")
    y -= 25
    c.drawString(50, y, f"Current Term Fee: ₦{current_fee:,.2f}")
    y -= 25
    c.drawString(50, y, f"Total Paid: ₦{total_paid:,.2f}")
    y -= 25
    c.drawString(50, y, f"Amount Owed: ₦{amount_owed:,.2f}")

    y -= 40

    # Footer
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(
        50,
        y,
        f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    c.save()

    return file_name
