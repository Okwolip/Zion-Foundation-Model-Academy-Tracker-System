from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime


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
    file_name = f"{student_name}_statement.pdf"

    c = canvas.Canvas(file_name, pagesize=letter)
    width, height = letter

    y = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, y, "STUDENT FINANCIAL STATEMENT")

    y -= 40

    c.setFont("Helvetica", 12)

    c.drawString(50, y, f"Student Name: {student_name}")
    y -= 20
    c.drawString(50, y, f"Class: {student_class}")
    y -= 20
    c.drawString(50, y, f"Section: {section}")
    y -= 20
    c.drawString(50, y, f"Session: {session}")

    y -= 40

    c.drawString(50, y, f"Previous Outstanding: ₦{previous_outstanding:,.2f}")
    y -= 20
    c.drawString(50, y, f"Current Term Fee: ₦{current_fee:,.2f}")
    y -= 20
    c.drawString(50, y, f"Total Paid: ₦{total_paid:,.2f}")
    y -= 20
    c.drawString(50, y, f"Amount Owed: ₦{amount_owed:,.2f}")

    y -= 40
    c.drawString(50, y, f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    c.save()

    return file_name
