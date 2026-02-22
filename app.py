import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="School Record Tracker", layout="wide")

st.title("School Record Tracker System")

# ----------------------------
# DATABASE CONNECTION
# ----------------------------
DATABASE_URL = st.secrets["DATABASE_URL"]

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def get_connection():
    return engine.connect()

# ----------------------------
# CREATE DEFAULT ADMIN USER
# ----------------------------
def create_admin():
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO users (username, password, role)
                SELECT 'admin', 'admin123', 'admin'
                WHERE NOT EXISTS (
                    SELECT 1 FROM users WHERE username='admin'
                )
            """))
    except:
        pass

create_admin()

# ----------------------------
# LOGIN FUNCTION
# ----------------------------
def check_login(username, password):
    with get_connection() as conn:
        result = conn.execute(text("""
        SELECT * FROM users
        WHERE username = :username
        AND password = :password
        """), {
            "username": username,
            "password": password
        }).fetchone()
        return result

# ----------------------------
# SESSION STATE
# ----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ----------------------------
# LOGIN PAGE
# ----------------------------
if not st.session_state.logged_in:

    st.subheader("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = check_login(username, password)

        if user:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid username or password")

    st.stop()

# ----------------------------
# SIDEBAR
# ----------------------------
st.sidebar.title("Navigation")

menu = st.sidebar.selectbox(
    "Select Option",
    [
        "Dashboard",
        "Add Student",
        "View Students",
        "Attendance",
        "Results",
        "Payment",
        "Fee Settings"
    ]
)

# ----------------------------
# DASHBOARD
# ----------------------------
if menu == "Dashboard":

    st.header("Dashboard")

    with get_connection() as conn:
        students = conn.execute(text("SELECT COUNT(*) FROM students")).scalar()
        attendance = conn.execute(text("SELECT COUNT(*) FROM attendance")).scalar()
        results = conn.execute(text("SELECT COUNT(*) FROM results")).scalar()

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Students", students)
    col2.metric("Attendance Records", attendance)
    col3.metric("Results Records", results)

# ----------------------------
# ADD STUDENT
# ----------------------------
elif menu == "Add Student":

    st.header("Add Student")

    student_id = st.text_input("Student ID")
    name = st.text_input("Student Name")
    gender = st.selectbox("Gender", ["Male", "Female"])
    student_class = st.text_input("Class")

    section = st.selectbox(
        "Section",
        ["Nursery", "Primary", "Secondary"]
    )

    dob = st.date_input("Date of Birth")
    parent_name = st.text_input("Parent Name")
    parent_phone = st.text_input("Parent Phone")
    address = st.text_area("Address")

    if st.button("Save Student"):

        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO students
                (student_id, name, gender, class, section, date_of_birth, parent_name, parent_phone, address)
                VALUES
                (:student_id, :name, :gender, :class, :section, :dob, :parent_name, :parent_phone, :address)
            """), {
                "student_id": student_id,
                "name": name,
                "gender": gender,
                "class": student_class,
                "section": section,
                "dob": dob,
                "parent_name": parent_name,
                "parent_phone": parent_phone,
                "address": address
            })

        st.success("Student saved successfully")

# ----------------------------
# VIEW STUDENTS
# ----------------------------
elif menu == "View Students":

    st.header("All Students")

    with get_connection() as conn:
        data = conn.execute(text("SELECT * FROM students ORDER BY created_at DESC"))
        df = pd.DataFrame(data.fetchall(), columns=data.keys())

    st.dataframe(df, use_container_width=True)

# ----------------------------
# ATTENDANCE
# ----------------------------
elif menu == "Attendance":

    st.header("Mark Attendance")

    with get_connection() as conn:
        students = conn.execute(text("SELECT student_id, name FROM students")).fetchall()

    student_options = {f"{s.name} ({s.student_id})": s.student_id for s in students}

    selected_student = st.selectbox("Select Student", list(student_options.keys()))
    status = st.selectbox("Status", ["Present", "Absent"])
    date = st.date_input("Date")

    if st.button("Save Attendance"):

        student_id = student_options[selected_student]

        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO attendance (student_id, date, status)
                VALUES (:student_id, :date, :status)
            """), {
                "student_id": student_id,
                "date": date,
                "status": status
            })

        st.success("Attendance saved")

# ----------------------------
# RESULTS
# ----------------------------
elif menu == "Results":

    st.header("Enter Result")

    with get_connection() as conn:
        students = conn.execute(text("SELECT student_id, name FROM students")).fetchall()

    student_options = {f"{s.name} ({s.student_id})": s.student_id for s in students}

    selected_student = st.selectbox("Student", list(student_options.keys()))
    subject = st.text_input("Subject")
    score = st.number_input("Score", 0, 100)
    term = st.selectbox("Term", ["First Term", "Second Term", "Third Term"])
    session = st.text_input("Session (e.g. 2024/2025)")

    if st.button("Save Result"):

        student_id = student_options[selected_student]

        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO results
                (student_id, subject, score, term, session)
                VALUES
                (:student_id, :subject, :score, :term, :session)
            """), {
                "student_id": student_id,
                "subject": subject,
                "score": score,
                "term": term,
                "session": session
            })

        st.success("Result saved")

# ----------------------------
# FEE SETTINGS (ADMIN ONLY)
# ----------------------------
elif menu == "Fee Settings":

    st.header("School Fee Settings")

    if st.session_state.username != "admin":
        st.warning("Only admin can set school fees")
        st.stop()

    section = st.selectbox(
        "Section",
        ["Nursery", "Primary", "Secondary"]
    )

    term = st.selectbox(
        "Term",
        ["First Term", "Second Term", "Third Term"]
    )

    fee_amount = st.number_input("Fee Amount", 0)

    if st.button("Save Fee"):

        with engine.begin() as conn:
            conn.execute(text("""
            INSERT INTO fee_settings (section, term, fee_amount)
            VALUES (:section, :term, :fee_amount)
            ON CONFLICT (section, term)
            DO UPDATE SET fee_amount = EXCLUDED.fee_amount
            """), {
                "section": section,
                "term": term,
                "fee_amount": fee_amount
            })

        st.success("Fee saved successfully")

# ----------------------------
# PAYMENT SYSTEM
# ----------------------------
elif menu == "Payment":

    st.header("Student Payment")

    with get_connection() as conn:
        students = conn.execute(text("""
        SELECT student_id, name, section FROM students
        """)).fetchall()

    student_dict = {
        f"{s.name} ({s.student_id})": (s.student_id, s.section)
        for s in students
    }

    selected_student = st.selectbox("Select Student", list(student_dict.keys()))

    term = st.selectbox(
        "Term",
        ["First Term", "Second Term", "Third Term"]
    )

    session = st.text_input("Session (e.g 2025/2026)")

    outstanding = st.number_input("Outstanding From Previous Term (X)", 0)
    amount_paid = st.number_input("Amount Paid (Z)", 0)

    if st.button("Calculate & Save Payment"):

        student_id, section = student_dict[selected_student]

        with get_connection() as conn:
            fee = conn.execute(text("""
            SELECT fee_amount FROM fee_settings
            WHERE section = :section AND term = :term
            """), {
                "section": section,
                "term": term
            }).fetchone()

        if not fee:
            st.error("Fee not set for this section and term")
            st.stop()

        X = outstanding
        Y = fee.fee_amount
        Z = amount_paid

        J = (X + Y) - Z

        with engine.begin() as conn:
            conn.execute(text("""
            INSERT INTO payments
            (student_id, term, session, outstanding, amount_paid)
            VALUES
            (:student_id, :term, :session, :outstanding, :amount_paid)
            """), {
                "student_id": student_id,
                "term": term,
                "session": session,
                "outstanding": X,
                "amount_paid": Z
            })

        st.success("Payment recorded")

        st.write("### Payment Summary")
        st.write(f"Outstanding Previous Term (X): {X}")
        st.write(f"Current Fee (Y): {Y}")
        st.write(f"Amount Paid (Z): {Z}")
        st.write(f"Amount Owed (J): {J}")
