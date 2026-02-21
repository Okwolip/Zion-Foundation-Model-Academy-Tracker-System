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
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO users (username, password, role)
            SELECT 'admin', 'admin123', 'admin'
            WHERE NOT EXISTS (
                SELECT 1 FROM users WHERE username='admin'
            )
        """))

create_admin()

# ----------------------------
# LOGIN FUNCTION
# ----------------------------
def check_login(username, password):
    with get_connection() as conn:
        query = text("""
        SELECT * FROM users
        WHERE username = :username
        AND password = :password
        """)
        result = conn.execute(query, {"username": username, "password": password}).fetchone()
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
        "Results"
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
    dob = st.date_input("Date of Birth")
    parent_name = st.text_input("Parent Name")
    parent_phone = st.text_input("Parent Phone")
    address = st.text_area("Address")

    if st.button("Save Student"):

        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO students
                (student_id, name, gender, class, date_of_birth, parent_name, parent_phone, address)
                VALUES
                (:student_id, :name, :gender, :class, :dob, :parent_name, :parent_phone, :address)
            """), {
                "student_id": student_id,
                "name": name,
                "gender": gender,
                "class": student_class,
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
