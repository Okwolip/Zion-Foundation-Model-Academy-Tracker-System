import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd

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

# -----------------------
# LOGIN SETUP
# -----------------------
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
        SELECT 'admin','admin123','admin'
        WHERE NOT EXISTS (
        SELECT 1 FROM users WHERE username='admin'
        )
        """))

create_admin()

def check_login(username, password):
    with get_connection() as conn:
        user = conn.execute(text("""
        SELECT * FROM users
        WHERE username=:u
        AND password=:p
        """), {"u":username,"p":password}).fetchone()
        return user

if "logged_in" not in st.session_state:
    st.session_state.logged_in=False
    st.session_state.role=None

if not st.session_state.logged_in:
    st.subheader("Login")
    u=st.text_input("Username")
    p=st.text_input("Password",type="password")

    if st.button("Login"):
        user=check_login(u,p)
        if user:
            st.session_state.logged_in=True
            st.session_state.role=user.role
            st.rerun()
        else:
            st.error("Invalid login")
    st.stop()

# -----------------------
# SIDEBAR
# -----------------------
menu=st.sidebar.selectbox("Navigation",[
"Dashboard",
"Add Student",
"View Students",
"Payment",
"School Fee Settings"
])

# -----------------------
# DASHBOARD
# -----------------------
if menu=="Dashboard":
    with get_connection() as conn:
        total=conn.execute(text("SELECT COUNT(*) FROM students")).scalar()
    st.metric("Students",total)

# -----------------------
# ADD STUDENT
# -----------------------
elif menu=="Add Student":

    st.header("Add Student")

    sid=st.text_input("Student ID")
    name=st.text_input("Name")
    gender=st.selectbox("Gender",["Male","Female"])
    section=st.selectbox("Section",["Nursery","Primary","Secondary"])
    class_name=st.text_input("Class")

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
            "section":section.strip(),
            "class":class_name.strip()
            })

        st.success("Student saved")

# -----------------------
# VIEW STUDENTS
# -----------------------
elif menu=="View Students":

    search=st.text_input("Search student")

    with get_connection() as conn:
        data=conn.execute(text("""
        SELECT * FROM students
        WHERE name ILIKE :s
        OR student_id ILIKE :s
        """),{"s":f"%{search}%"}).fetchall()

    df=pd.DataFrame(data)
    st.dataframe(df,use_container_width=True)

# -----------------------
# PAYMENT (FULLY FIXED)
# -----------------------
elif menu=="Payment":

    st.header("Student Payment")

    with get_connection() as conn:
        students = conn.execute(text("""
        SELECT student_id,name,
        COALESCE(section,'Primary') as section
        FROM students
        """)).fetchall()
        
    options={f"{s.name} ({s.student_id})":s for s in students}

    selected=st.selectbox("Select Student",options.keys())

    term=st.selectbox("Term",[
    "First Term","Second Term","Third Term"
    ])

    session=st.text_input("Session e.g 2025/2026").strip()

    if selected:

        student=options[selected]
        #section=student.section.strip()
        section = (student.section or "").strip()

        with get_connection() as conn:

            fee=conn.execute(text("""
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
                st.warning("Fee not found. Check Fee Settings.")
                st.stop()

            fee_amount=float(fee.fee_amount)

            paid=conn.execute(text("""
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

        previous_outstanding=0
        total_due=previous_outstanding+fee_amount
        balance=total_due-paid

        st.info(f"Previous Debt: ₦{previous_outstanding}")
        st.info(f"Current Fee: ₦{fee_amount}")
        st.success(f"Paid: ₦{paid}")
        st.error(f"Balance: ₦{balance}")

        pay=st.number_input("Enter Payment",0)

        if st.button("Record Payment"):
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
            st.success("Payment recorded")

# -----------------------
# FEE SETTINGS (ADMIN)
# -----------------------
elif menu=="School Fee Settings":

    if st.session_state.role!="admin":
        st.error("Admin only")
        st.stop()

    st.header("Set School Fee")

    section=st.selectbox("Section",["Nursery","Primary","Secondary"])
    term=st.selectbox("Term",[
    "First Term","Second Term","Third Term"
    ])
    session=st.text_input("Session e.g 2025/2026").strip()
    fee=st.number_input("Fee Amount",0)

    if st.button("Save Fee"):

        with engine.begin() as conn:
            conn.execute(text("""
            INSERT INTO school_fee_settings
            (section,term,session,fee_amount)
            VALUES
            (:section,:term,:session,:fee)
            """),{
            "section": section,
#            "section":section.strip(),
            "term":term.strip(),
            "session":session,
            "fee":fee
            })

        st.success("Fee saved")

    with get_connection() as conn:
        data=conn.execute(text("""
        SELECT section,term,session,fee_amount
        FROM school_fee_settings
        ORDER BY id DESC
        """)).fetchall()

    st.dataframe(pd.DataFrame(data))
