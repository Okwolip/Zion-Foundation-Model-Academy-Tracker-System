import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# DATABASE CONNECTION
# =========================

DATABASE_URL = st.secrets["DATABASE_URL"]
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def run_query(query, params=None, fetch=False):
    with engine.begin() as conn:
        result = conn.execute(text(query), params or {})
        if fetch:
            return result.fetchall()

# =========================
# LOGIN SYSTEM
# =========================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def check_login(username, password):
    user = run_query("""
    SELECT * FROM users
    WHERE username=:username
    AND password=:password
    """, {"username": username, "password": password}, True)

    return user

if not st.session_state.logged_in:

    st.title("School System Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = check_login(username, password)

        if user:
            st.session_state.logged_in = True
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid login")

    st.stop()

# =========================
# APP HEADER
# =========================

st.title("School Record Tracker System")

menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Dashboard",
        "Add Student",
        "Student List",
        "Payment",
        "Payment History",
        "School Fee Settings",
        "Fee History"
    ]
)

# =========================
# DASHBOARD
# =========================

if menu == "Dashboard":

    st.header("Search Student (Name or ID)")

    search = st.text_input("Enter student name or ID")

    if st.button("Search"):

        student = run_query("""
        SELECT * FROM students
        WHERE name ILIKE :search
        OR student_id ILIKE :search
        """, {"search": f"%{search}%"}, True)

        if not student:
            st.warning("Student not found")
            st.stop()

        s = student[0]._mapping

        st.subheader("School Payment Receipt")

        st.write("Student Name:", s["name"])
        st.write("Student ID:", s["student_id"])
        st.write("Class:", s.get("student_class", ""))
        st.write("Section:", s.get("section", ""))

        payments = run_query("""
        SELECT session, term, amount_paid, balance, created_at
        FROM payments
        WHERE student_id=:student_id
        ORDER BY created_at DESC
        """, {"student_id": s["student_id"]}, True)

        if payments:
            df = pd.DataFrame([p._mapping for p in payments])
            st.dataframe(df)
        else:
            st.info("No payment record found.")
# =========================
# ADD STUDENT
# =========================

elif menu == "Add Student":
    st.header("Add Student")

    name = st.text_input("Student Name")
    student_class = st.text_input("Class")
    section = st.selectbox(
        "Section",
        ["Nursery", "Primary", "Secondary"]
    )

    if st.button("Add Student"):
        student_id = str(int(datetime.now().timestamp()))

        run_query("""
        INSERT INTO students (student_id, name, student_class, section)
        VALUES (:id, :name, :student_class, :section)
        """, {
            "id": student_id,
            "name": name,
            "student_class": student_class,
            "section": section
        })

        st.success("Student added successfully")
#Just added
elif menu == "Student List":

    st.header("All Students")

    students = run_query("""
    SELECT * FROM students
    ORDER BY created_at DESC
    """, fetch=True)

    if students:
        df = pd.DataFrame([s._mapping for s in students])
        st.dataframe(df)
# =========================
# SCHOOL FEE SETTINGS
# =========================

elif menu == "School Fee Settings":
    st.header("Set School Fee")

    session = st.text_input("Session (e.g 2025/2026)")
    term = st.selectbox("Term", ["First Term", "Second Term", "Third Term"])
    section = st.selectbox(
        "Section",
        ["Nursery", "Primary", "Secondary"]
    )
    fee = st.number_input("Fee Amount", min_value=0)

    if st.button("Save Fee"):
        run_query("""
        INSERT INTO school_fee_settings (session, term, section, fee_amount)
        VALUES (:session, :term, :section, :fee)
        """, {
            "session": session.strip(),
            "term": term.strip(),
            "section": section.strip(),
            "fee": fee
        })

        st.success("Fee saved successfully")
#just na
elif menu == "Fee History":

    st.header("School Fee Records")

    fees = run_query("""
    SELECT * FROM school_fee_settings
    ORDER BY id DESC
    """, fetch=True)

    if fees:
        df = pd.DataFrame([f._mapping for f in fees])
        st.dataframe(df)

# =========================
# PAYMENT SYSTEM
# =========================

elif menu == "Payment":
    st.header("Student Payment")

    students = run_query("""
    SELECT student_id, name, student_class, section
    FROM students
    ORDER BY name
    """, fetch=True)

    student_dict = {
        f"{s._mapping['name']} ({s._mapping['student_id']})": s._mapping
        for s in students
    }

    selected = st.selectbox("Select Student", list(student_dict.keys()))

    term = st.selectbox("Term", ["First Term", "Second Term", "Third Term"])
    session = st.text_input("Session e.g 2025/2026")

    amount_paid = st.number_input("Amount Paid", min_value=0)

    if st.button("Process Payment"):

        student = student_dict[selected]
        student_id = student["student_id"]
        section = student.get("section") or ""

        # GET CURRENT TERM FEE (Y)
        fee_result = run_query("""
        SELECT fee_amount
        FROM school_fee_settings
        WHERE session=:session
        AND term=:term
        AND section=:section
        """, {
            "session": session.strip(),
            "term": term.strip(),
            "section": section.strip()
        }, True)

        if not fee_result:
            st.error("Fee not set. Go to School Fee Settings.")
            st.stop()

        current_fee = float(fee_result[0]._mapping["fee_amount"])

        # PREVIOUS DEBT (X)
        debt_result = run_query("""
        SELECT COALESCE(SUM(balance), 0) AS debt
        FROM payments
        WHERE student_id = :student_id
        """, {"student_id": student_id}, True)

        previous_debt = 0

        if debt_result and len(debt_result) > 0:
            previous_debt = float(debt_result[0]._mapping["debt"] or 0)        # SAVE PAYMENT
        run_query("""
        INSERT INTO payments
        (student_id, session, term, amount_paid, balance)
        VALUES (:student_id, :session, :term, :paid, :balance)
        """, {
            "student_id": student_id,
            "session": session,
            "term": term,
            "paid": amount_paid,
            "balance": balance
        })

        st.success("Payment recorded successfully")
#just now
elif menu == "Payment History":

    st.header("Payment Records")

    payments = run_query("""
    SELECT * FROM payments
    ORDER BY created_at DESC
    """, fetch=True)

    if payments:
        df = pd.DataFrame([p._mapping for p in payments])
        st.dataframe(df)

        # =========================
        # GENERATE PDF RECEIPT
        # =========================

        filename = f"receipt_{student_id}.pdf"
        styles = getSampleStyleSheet()
        pdf = SimpleDocTemplate(filename)

        elements = []

        elements.append(Paragraph("School Payment Receipt", styles['Title']))
        elements.append(Spacer(1, 20))

        elements.append(Paragraph(f"Student: {student['name']}", styles['Normal']))
        elements.append(Paragraph(f"Student ID: {student_id}", styles['Normal']))
        elements.append(Paragraph(f"Session: {session}", styles['Normal']))
        elements.append(Paragraph(f"Term: {term}", styles['Normal']))

        elements.append(Spacer(1, 20))

        elements.append(Paragraph(f"Previous Debt (X): {previous_debt}", styles['Normal']))
        elements.append(Paragraph(f"Current Fee (Y): {current_fee}", styles['Normal']))
        elements.append(Paragraph(f"Amount Paid (Z): {amount_paid}", styles['Normal']))
        elements.append(Paragraph(f"Remaining Balance (J): {balance}", styles['Normal']))

        pdf.build(elements)

        with open(filename, "rb") as f:
            st.download_button(
                "Download Receipt",
                f,
                file_name=filename
            )
