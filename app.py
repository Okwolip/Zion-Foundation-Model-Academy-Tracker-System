import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os

st.set_page_config(page_title="School Record Tracker", layout="wide")
st.title("School Record Tracker System")

DATABASE_URL = st.secrets["DATABASE_URL"]

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300
)

def get_connection():
    return engine.connect()

# -------------------------
# ADMIN SETUP
# -------------------------
def create_admin():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
        """))

        conn.execute(text("""
        INSERT INTO users(username,password,role)
        SELECT 'admin','admin123','admin'
        WHERE NOT EXISTS (
        SELECT 1 FROM users WHERE username='admin'
        )
        """))

create_admin()

# -------------------------
# LOGIN
# -------------------------
def login(username,password):
    with get_connection() as conn:
        user = conn.execute(text("""
        SELECT * FROM users
        WHERE username=:u AND password=:p
        """),{"u":username,"p":password}).fetchone()
        return user

if "logged_in" not in st.session_state:
    st.session_state.logged_in=False
    st.session_state.role=None

if not st.session_state.logged_in:
    st.subheader("Login")
    u=st.text_input("Username")
    p=st.text_input("Password",type="password")

    if st.button("Login"):
        user=login(u,p)
        if user:
            st.session_state.logged_in=True
            st.session_state.role=user.role
            st.rerun()
        else:
            st.error("Invalid login")
    st.stop()

# -------------------------
# SIDEBAR
# -------------------------
menu = st.sidebar.selectbox("Navigation",[
"Dashboard",
"Add Student",
"View Students",
"Payment",
"School Fee Settings"
])

# -------------------------
# DASHBOARD SEARCH
# -------------------------
if menu=="Dashboard":

    st.header("Dashboard")

    search = st.text_input("Search student (Name or ID)")

    if st.button("Search"):
        with get_connection() as conn:
            student = conn.execute(text("""
            SELECT *
            FROM students
            WHERE name ILIKE :q
            OR student_id ILIKE :q
            LIMIT 1
            """),{"q":f"%{search}%"}).fetchone()

        if student:
            st.success("Student Found")

            st.write("Name:",student.name)
            st.write("Student ID:",student.student_id)
            st.write("Section:",student.section)
            st.write("Class:",student.class)
        else:
            st.warning("Student not found")

# -------------------------
# ADD STUDENT
# -------------------------
elif menu=="Add Student":

    st.header("Add Student")

    sid = st.text_input("Student ID")
    name = st.text_input("Name")
    gender = st.selectbox("Gender",["Male","Female"])
    section = st.selectbox("Section",["Nursery","Primary","Secondary"])
    class_name = st.text_input("Class")

    if st.button("Save Student"):

        with engine.begin() as conn:
            conn.execute(text("""
            INSERT INTO students
            (student_id,name,gender,section,class)
            VALUES
            (:sid,:name,:gender,:section,:class)
            """),{
                "sid":sid.strip(),
                "name":name.strip(),
                "gender":gender,
                "section":section,
                "class":class_name.strip()
            })

        st.success("Student added")

# -------------------------
# VIEW STUDENTS
# -------------------------
elif menu=="View Students":

    with get_connection() as conn:
        data = conn.execute(text("SELECT * FROM students ORDER BY id DESC")).fetchall()

    df = pd.DataFrame(data)
    st.dataframe(df,use_container_width=True)

    delete_id = st.text_input("Enter Student ID to delete")

    if st.button("Delete Student"):
        with engine.begin() as conn:
            conn.execute(text("""
            DELETE FROM students WHERE student_id=:id
            """),{"id":delete_id})
        st.success("Student deleted")
        st.rerun()

# -------------------------
# PAYMENT SYSTEM
# -------------------------
elif menu=="Payment":

    st.header("Student Payment")

    with get_connection() as conn:
        students = conn.execute(text("""
        SELECT student_id,name,COALESCE(section,'Primary') as section
        FROM students
        """)).fetchall()

    options = {f"{s.name} ({s.student_id})":s for s in students}
    selected = st.selectbox("Select Student",options.keys())

    term = st.selectbox("Term",[
    "First Term","Second Term","Third Term"
    ])

    session = st.text_input("Session e.g 2025/2026").strip()

    if selected:

        student = options[selected]
        section = (student.section or "").strip()

        with get_connection() as conn:

            # Current Fee (Y)
            fee = conn.execute(text("""
            SELECT fee_amount
            FROM school_fee_settings
            WHERE section ILIKE :section
            AND term ILIKE :term
            AND session ILIKE :session
            LIMIT 1
            """),{
                "section":section,
                "term":term,
                "session":session
            }).fetchone()

            if not fee:
                st.error("Fee not set. Go to School Fee Settings")
                st.stop()

            fee_amount = float(fee.fee_amount)

            # Previous debt (X)
            previous_debt = conn.execute(text("""
            SELECT COALESCE(SUM(balance),0)
            FROM student_balances
            WHERE student_id=:sid
            """),{"sid":student.student_id}).scalar()

            previous_debt = float(previous_debt or 0)

            # Amount already paid (Z)
            paid = conn.execute(text("""
            SELECT COALESCE(SUM(amount_paid),0)
            FROM payments
            WHERE student_id=:sid
            AND term=:term
            AND session=:session
            """),{
                "sid":student.student_id,
                "term":term,
                "session":session
            }).scalar()

            paid = float(paid or 0)

        total_due = previous_debt + fee_amount
        balance = total_due - paid

        st.info(f"Previous Debt (X): ₦{previous_debt}")
        st.info(f"Current Fee (Y): ₦{fee_amount}")
        st.success(f"Paid (Z): ₦{paid}")
        st.error(f"Balance (J): ₦{balance}")

        pay = st.number_input("Enter Payment",min_value=0.0,step=1000.0)

        if st.button("Record Payment"):

            new_paid = paid + pay
            new_balance = total_due - new_paid

            with engine.begin() as conn:
                conn.execute(text("""
                INSERT INTO payments
                (student_id,amount_paid,term,session)
                VALUES
                (:sid,:amt,:term,:session)
                """),{
                    "sid":student.student_id,
                    "amt":pay,
                    "term":term,
                    "session":session
                })

            # Generate receipt
            filename = f"receipt_{student.student_id}.pdf"
            styles = getSampleStyleSheet()
            doc = SimpleDocTemplate(filename)

            story = []
            story.append(Paragraph("School Payment Receipt",styles["Title"]))
            story.append(Spacer(1,20))
            story.append(Paragraph(f"Student: {student.name}",styles["Normal"]))
            story.append(Paragraph(f"Student ID: {student.student_id}",styles["Normal"]))
            story.append(Paragraph(f"Session: {session}",styles["Normal"]))
            story.append(Paragraph(f"Term: {term}",styles["Normal"]))
            story.append(Spacer(1,10))
            story.append(Paragraph(f"Previous Debt (X): ₦{previous_debt}",styles["Normal"]))
            story.append(Paragraph(f"Current Fee (Y): ₦{fee_amount}",styles["Normal"]))
            story.append(Paragraph(f"Amount Paid Now (Z): ₦{pay}",styles["Normal"]))
            story.append(Paragraph(f"Remaining Balance (J): ₦{new_balance}",styles["Normal"]))
            story.append(Spacer(1,10))
            story.append(Paragraph(f"Date: {datetime.now()}",styles["Normal"]))

            doc.build(story)

            with open(filename,"rb") as f:
                st.download_button("Download Receipt",f,file_name=filename)

            st.success("Payment recorded successfully")

# -------------------------
# SCHOOL FEE SETTINGS
# -------------------------
elif menu=="School Fee Settings":

    if st.session_state.role!="admin":
        st.error("Admin only")
        st.stop()

    st.header("Set School Fee")

    section = st.selectbox("Section",["Nursery","Primary","Secondary"])
    term = st.selectbox("Term",[
    "First Term","Second Term","Third Term"
    ])
    session = st.text_input("Session e.g 2025/2026").strip()
    fee = st.number_input("Fee Amount",min_value=0)

    if st.button("Save Fee"):

        with engine.begin() as conn:
            conn.execute(text("""
            INSERT INTO school_fee_settings
            (section,term,session,fee_amount)
            VALUES
            (:section,:term,:session,:fee)
            """),{
                "section":section,
                "term":term,
                "session":session,
                "fee":fee
            })

        st.success("Fee saved")

    with get_connection() as conn:
        fees = conn.execute(text("""
        SELECT section,term,session,fee_amount
        FROM school_fee_settings
        ORDER BY id DESC
        """)).fetchall()

    st.dataframe(pd.DataFrame(fees))
