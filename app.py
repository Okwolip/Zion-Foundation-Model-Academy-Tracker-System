import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="School Record Tracker", layout="wide")
st.title("School Record Tracker System")

# ---------------------------------------------------
# DATABASE CONNECTION (Production Ready)
# ---------------------------------------------------
DATABASE_URL = st.secrets["DATABASE_URL"]

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300
)

def get_connection():
    return engine.connect()

# ---------------------------------------------------
# INITIAL DATABASE SAFETY CHECK
# ---------------------------------------------------
def create_admin():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
        """))

        conn.execute(text("""
        INSERT INTO users (username, password, role)
        SELECT 'admin', 'admin123', 'admin'
        WHERE NOT EXISTS (
            SELECT 1 FROM users WHERE username='admin'
        )
        """))

create_admin()

# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------
def check_login(username, password):
    with get_connection() as conn:
        result = conn.execute(text("""
        SELECT * FROM users
        WHERE username=:username
        AND password=:password
        """), {"username": username, "password": password}).fetchone()
        return result

# ---------------------------------------------------
# SESSION STATE
# ---------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

# ---------------------------------------------------
# LOGIN PAGE
# ---------------------------------------------------
if not st.session_state.logged_in:

    st.subheader("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = check_login(username, password)

        if user:
            st.session_state.logged_in = True
            st.session_state.role = user.role
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid login")

    st.stop()

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
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
        "School Fee Settings"
    ]
)

# ---------------------------------------------------
# DASHBOARD
# ---------------------------------------------------
if menu == "Dashboard":

    st.header("Dashboard")

    with get_connection() as conn:
        students = conn.execute(text("SELECT COUNT(*) FROM students")).scalar()
        payments = conn.execute(text("SELECT COUNT(*) FROM payments")).scalar()

    col1, col2 = st.columns(2)

    col1.metric("Total Students", students)
    col2.metric("Payments Recorded", payments)

# ---------------------------------------------------
# ADD STUDENT
# ---------------------------------------------------
elif menu == "Add Student":

    st.header("Register Student")

    student_id = st.text_input("Student ID")
    name = st.text_input("Student Name")
    gender = st.selectbox("Gender", ["Male", "Female"])
    section = st.selectbox("Section", ["Nursery", "Primary", "Secondary"])
    student_class = st.text_input("Class")
    parent_phone = st.text_input("Parent Phone")

    if st.button("Save Student"):

        with engine.begin() as conn:
            conn.execute(text("""
            INSERT INTO students
            (student_id, name, gender, section, class, parent_phone)
            VALUES
            (:student_id, :name, :gender, :section, :class, :parent_phone)
            """), {
                "student_id": student_id,
                "name": name,
                "gender": gender,
                "section": section,
                "class": student_class,
                "parent_phone": parent_phone
            })

        st.success("Student Added Successfully")

# ---------------------------------------------------
# VIEW STUDENTS (SEARCH + DELETE)
# ---------------------------------------------------
elif menu == "View Students":

    st.header("Students")

    search = st.text_input("Search Student")

    query = """
    SELECT * FROM students
    WHERE name ILIKE :search
    OR student_id ILIKE :search
    ORDER BY id DESC
    """

    with get_connection() as conn:
        data = conn.execute(text(query), {"search": f"%{search}%"}).fetchall()

    df = pd.DataFrame(data)

    st.dataframe(df, use_container_width=True)

    st.subheader("Delete Student")

    student_to_delete = st.text_input("Enter Student ID to delete")

    if st.button("Delete Student"):
        with engine.begin() as conn:
            conn.execute(text("""
            DELETE FROM students
            WHERE student_id=:student_id
            """), {"student_id": student_to_delete})

        st.success("Student deleted")

# ---------------------------------------------------
# ATTENDANCE
# ---------------------------------------------------
elif menu == "Attendance":

    st.header("Attendance")

    with get_connection() as conn:
        students = conn.execute(text("""
        SELECT student_id, name FROM students
        """)).fetchall()

    options = {f"{s.name} ({s.student_id})": s.student_id for s in students}

    selected = st.selectbox("Select Student", list(options.keys()))
    status = st.selectbox("Status", ["Present", "Absent"])
    date = st.date_input("Date")

    if st.button("Save Attendance"):
        with engine.begin() as conn:
            conn.execute(text("""
            INSERT INTO attendance
            (student_id, date, status)
            VALUES
            (:student_id, :date, :status)
            """), {
                "student_id": options[selected],
                "date": date,
                "status": status
            })

        st.success("Attendance Recorded")

# ---------------------------------------------------
# RESULTS
# ---------------------------------------------------
elif menu == "Results":

    st.header("Enter Result")

    with get_connection() as conn:
        students = conn.execute(text("""
        SELECT student_id, name FROM students
        """)).fetchall()

    options = {f"{s.name} ({s.student_id})": s.student_id for s in students}

    student = st.selectbox("Student", list(options.keys()))
    subject = st.text_input("Subject")
    score = st.number_input("Score", 0, 100)
    term = st.selectbox("Term", ["First Term", "Second Term", "Third Term"])
    session = st.text_input("Session (2024/2025)")

    if st.button("Save Result"):
        with engine.begin() as conn:
            conn.execute(text("""
            INSERT INTO results
            (student_id, subject, score, term, session)
            VALUES
            (:student_id, :subject, :score, :term, :session)
            """), {
                "student_id": options[student],
                "subject": subject,
                "score": score,
                "term": term,
                "session": session
            })

        st.success("Result saved")

# ---------------------------------------------------
# PAYMENT SYSTEM (AUTO OUTSTANDING)
# ---------------------------------------------------
elif menu == "Payment":

    st.header("Student Payment")

    with get_connection() as conn:
        students = conn.execute(text("""
        SELECT student_id, name, section
        FROM students
        """)).fetchall()

    options = {f"{s.name} ({s.student_id})": s for s in students}

    selected = st.selectbox("Student", list(options.keys()))
    term = st.selectbox("Term", ["First Term", "Second Term", "Third Term"])
    session = st.text_input("Session (Example: 2025/2026)").strip()

    if selected:
        student = options[selected]

        with get_connection() as conn:

            fee = conn.execute(text("""
            SELECT fee_amount
            FROM school_fee_settings
            WHERE LOWER(TRIM(section)) = LOWER(TRIM(:section))
            AND LOWER(TRIM(term)) = LOWER(TRIM(:term))
            AND LOWER(TRIM(session)) = LOWER(TRIM(:session))
            LIMIT 1
            """), {
                "section": student.section,
                "term": term,
                "session": session
            }).fetchone()

            if not fee:
                st.error("Fee not set. Go to School Fee Settings.")
                st.stop()

            fee_amount = fee.fee_amount

            paid = conn.execute(text("""
            SELECT COALESCE(SUM(amount_paid),0)
            FROM payments
            WHERE student_id=:student_id
            AND term=:term
            AND session=:session
            """), {
                "student_id": student.student_id,
                "term": term,
                "session": session
            }).scalar()

        outstanding_previous = 0
        total_due = outstanding_previous + fee_amount
        owed = total_due - paid

        st.info(f"Outstanding Previous Term: ₦{outstanding_previous}")
        st.info(f"Current Term Fee: ₦{fee_amount}")
        st.success(f"Amount Paid: ₦{paid}")
        st.error(f"Amount Owed: ₦{owed}")
        st.write("Student Section:", student.section)
        st.write("Selected Term:", term)
        st.write("Entered Session:", session)

        payment = st.number_input("Enter Payment", min_value=0)

        if st.button("Record Payment"):
            with engine.begin() as conn:
                conn.execute(text("""
                INSERT INTO payments
                (student_id, amount_paid, term, session)
                VALUES
                (:student_id, :amount_paid, :term, :session)
                """), {
                    "student_id": student.student_id,
                    "amount_paid": payment,
                    "term": term,
                    "session": session
                })

            st.success("Payment Recorded")

# ---------------------------------------------------
# SCHOOL FEE SETTINGS (ADMIN ONLY)
# ---------------------------------------------------
elif menu == "School Fee Settings":

    if st.session_state.role != "admin":
        st.error("Only Admin can set school fees")
        st.stop()

    st.header("School Fee Settings")

    col1, col2 = st.columns(2)

    with col1:
        section = st.selectbox(
            "Section",
            ["Nursery", "Primary", "Secondary"]
        )

        term = st.selectbox(
            "Term",
            ["First Term", "Second Term", "Third Term"]
        )

        # ✅ SESSION FIELD (THIS WAS MISSING)
        session = st.text_input("Session (Example: 2024/2025)").strip()
        #session = st.text_input(
        #    "Session (Example: 2024/2025)",
        #    placeholder="e.g. 2025/2026"
        #)

    with col2:
        fee = st.number_input(
            "Fee Amount",
            min_value=0,
            step=1000
        )

        st.write("")  # spacing
        st.write("")

        save_fee = st.button("Save Fee", use_container_width=True)

    if save_fee:

        if session == "":
            st.warning("Please enter session")
            st.stop()

        with engine.begin() as conn:
            conn.execute(text("""
            INSERT INTO school_fee_settings
            (section, term, session, fee_amount)
            VALUES
            (:section, :term, :session, :fee)
            """), {
                "section": section,
                "term": term,
                "session": session,
                "fee": fee
            })

        st.success("Fee saved successfully")

    st.divider()
    st.subheader("Existing Fee Structure")

    with get_connection() as conn:
        fees = conn.execute(text("""
        SELECT section, term, session, fee_amount
        FROM school_fee_settings
        ORDER BY session DESC
        """)).fetchall()

    if fees:
        df = pd.DataFrame(fees, columns=["Section", "Term", "Session", "Fee"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No fee settings yet")
