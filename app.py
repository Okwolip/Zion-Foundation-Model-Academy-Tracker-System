import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import io

# =========================================
# PAGE CONFIG
# =========================================

st.set_page_config(
    page_title="Zion Foundation Model Academy ERP",
    layout="wide"
)

# =========================================
# STYLING
# =========================================

st.markdown("""
<style>
.main-title {
    font-size:36px;
    font-weight:bold;
    color:#ff4b4b;
}
.subtitle {
    font-size:18px;
    color:#444;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">Zion Foundation Model Academy</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">School ERP Management System</p>', unsafe_allow_html=True)

# =========================================
# DATABASE CONNECTION
# =========================================

DATABASE_URL = st.secrets["DATABASE_URL"]
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def run_query(query, params=None, fetch=False):
    with engine.begin() as conn:
        result = conn.execute(text(query), params or {})
        if fetch:
            return result.fetchall()

# =========================================
# LOGIN SYSTEM
# =========================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

def check_login(username, password):
    user = run_query("""
    SELECT username, role
    FROM users
    WHERE username=:username
    AND password=:password
    """, {"username": username, "password": password}, True)
    return user

if not st.session_state.logged_in:

    st.subheader("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        user = check_login(username, password)

        if user:
            st.session_state.logged_in = True
            st.session_state.role = user[0]._mapping["role"]
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid login")

    st.stop()

# =========================================
# SIDEBAR
# =========================================

role = st.session_state.role

menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Dashboard",
        "Add Student",
        "All Students",
        "Promote Students",
        "Payment",
        "Payment Records",
        "Debt Report",
        "Revenue Dashboard",
        "School Fee Settings",
        "School Fee Records"
    ]
)

# =========================================
# DASHBOARD
# =========================================

if menu == "Dashboard":

    st.header("Student Search")

    search = st.text_input("Search Student (Name or ID)")

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

        st.subheader("Student Details")
        st.write("Name:", s["name"])
        st.write("Student ID:", s["student_id"])
        st.write("Class:", s.get("student_class", ""))
        st.write("Section:", s.get("section", ""))

# =========================================
# ADD STUDENT
# =========================================

elif menu == "Add Student":

    if role not in ["admin", "bursar"]:
        st.warning("Permission denied")
        st.stop()

    st.header("Register Student")

    name = st.text_input("Student Name")
    student_class = st.text_input("Class")
    section = st.selectbox("Section", ["Nursery", "Primary", "Secondary"])

    if st.button("Add Student"):

        student_id = str(int(datetime.now().timestamp()))

        run_query("""
        INSERT INTO students (student_id, name, student_class, section)
        VALUES (:id, :name, :class, :section)
        """, {
            "id": student_id,
            "name": name,
            "class": student_class,
            "section": section
        })

        st.success("Student added")

# =========================================
# ALL STUDENTS
# =========================================

elif menu == "All Students":

    st.header("Student List")

    students = run_query("""
    SELECT * FROM students
    ORDER BY created_at DESC
    """, fetch=True)

    if students:
        df = pd.DataFrame([s._mapping for s in students])
        st.dataframe(df)

        st.download_button(
            "Export to Excel",
            df.to_csv(index=False),
            "students_report.csv"
        )

        if role == "admin":

            student_id = st.selectbox("Delete Student", df["student_id"])

            if st.button("Delete Student"):
                run_query("DELETE FROM students WHERE student_id=:id", {"id": student_id})
                st.success("Student deleted")
                st.rerun()

# =========================================
# STUDENT PROMOTION SYSTEM
# =========================================

elif menu == "Promote Students":

    if role != "admin":
        st.warning("Admin only")
        st.stop()

    st.header("Promote Students to Next Class")

    current_class = st.text_input("Current Class")
    next_class = st.text_input("Next Class")

    if st.button("Promote"):

        run_query("""
        UPDATE students
        SET student_class=:next_class
        WHERE student_class=:current_class
        """, {
            "next_class": next_class,
            "current_class": current_class
        })

        st.success("Students promoted successfully")

# =========================================
# PAYMENT
# =========================================

elif menu == "Payment":

    if role not in ["admin", "bursar"]:
        st.warning("Permission denied")
        st.stop()

    st.header("Student Payment")

    students = run_query("SELECT student_id,name,section FROM students", fetch=True)

    student_map = {
        f"{s._mapping['name']} ({s._mapping['student_id']})": s._mapping
        for s in students
    }

    selected = st.selectbox("Select Student", list(student_map.keys()))

    term = st.selectbox("Term", ["First Term", "Second Term", "Third Term"])
    session = st.text_input("Session (2025/2026)")
    amount_paid = st.number_input("Amount Paid", min_value=0)

    if st.button("Process Payment"):

        student = student_map[selected]
        student_id = student["student_id"]
        section = student["section"]

        fee = run_query("""
        SELECT fee_amount
        FROM school_fee_settings
        WHERE session=:session
        AND term=:term
        AND section=:section
        """, {
            "session": session,
            "term": term,
            "section": section
        }, True)

        if not fee:
            st.error("Fee not set")
            st.stop()

        current_fee = float(fee[0]._mapping["fee_amount"])

        debt = run_query("""
        SELECT COALESCE(SUM(balance),0) AS debt
        FROM payments
        WHERE student_id=:student_id
        """, {"student_id": student_id}, True)

        previous_debt = float(debt[0]._mapping["debt"])

        total_due = previous_debt + current_fee
        balance = total_due - amount_paid

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

        st.success("Payment recorded")

# =========================================
# PAYMENT RECORDS
# =========================================

elif menu == "Payment Records":

    st.header("Payment History")

    payments = run_query("SELECT * FROM payments ORDER BY created_at DESC", fetch=True)

    if payments:
        df = pd.DataFrame([p._mapping for p in payments])
        st.dataframe(df)

        st.download_button(
            "Export to Excel",
            df.to_csv(index=False),
            "payments_report.csv"
        )

        if role == "admin":

            payment_id = st.selectbox("Delete Payment", df["id"])

            if st.button("Delete Payment"):
                run_query("DELETE FROM payments WHERE id=:id", {"id": payment_id})
                st.success("Payment deleted")
                st.rerun()

# =========================================
# DEBT REPORT
# =========================================

elif menu == "Debt Report":

    st.header("Students With Debt")

    debts = run_query("""
    SELECT student_id, SUM(balance) as total_debt
    FROM payments
    GROUP BY student_id
    HAVING SUM(balance) > 0
    """, fetch=True)

    if debts:
        df = pd.DataFrame([d._mapping for d in debts])
        st.dataframe(df)

# =========================================
# REVENUE DASHBOARD
# =========================================

elif menu == "Revenue Dashboard":

    st.header("Total Revenue Per Session")

    revenue = run_query("""
    SELECT session, SUM(amount_paid) as revenue
    FROM payments
    GROUP BY session
    """, fetch=True)

    if revenue:
        df = pd.DataFrame([r._mapping for r in revenue])
        st.bar_chart(df.set_index("session"))

# =========================================
# SCHOOL FEE SETTINGS
# =========================================

elif menu == "School Fee Settings":

    if role != "admin":
        st.warning("Admin only")
        st.stop()

    st.header("Set School Fee")

    session = st.text_input("Session")
    term = st.selectbox("Term", ["First Term", "Second Term", "Third Term"])
    section = st.selectbox("Section", ["Nursery", "Primary", "Secondary"])
    fee = st.number_input("Fee Amount", min_value=0)

    if st.button("Save Fee"):

        run_query("""
        INSERT INTO school_fee_settings
        (session, term, section, fee_amount)
        VALUES (:session, :term, :section, :fee)
        """, {
            "session": session,
            "term": term,
            "section": section,
            "fee": fee
        })

        st.success("Fee saved")

# =========================================
# SCHOOL FEE RECORDS
# =========================================

elif menu == "School Fee Records":

    st.header("Fee Records")

    fees = run_query("SELECT * FROM school_fee_settings", fetch=True)

    if fees:
        df = pd.DataFrame([f._mapping for f in fees])
        st.dataframe(df)

        if role == "admin":

            fee_id = st.selectbox("Delete Fee", df["id"])

            if st.button("Delete Fee"):
                run_query("DELETE FROM school_fee_settings WHERE id=:id", {"id": fee_id})
                st.success("Fee deleted")
                st.rerun()
