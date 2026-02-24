import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
from io import BytesIO

# =========================================================
# APP CONFIG
# =========================================================
st.set_page_config(layout="wide")

st.markdown(
    """
    <h1 style='text-align:center; color:#2E86C1'>
    Zion Foundation Model Academy
    </h1>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# DATABASE CONNECTION
# =========================================================
DATABASE_URL = st.secrets["DATABASE_URL"]
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
def run_query(query, params=None, fetch=False):
    try:
        with engine.begin() as conn:
            result = conn.execute(text(query), params or {})
            if fetch:
                return result.fetchall()
    except Exception as e:
        st.error(f"Database error: {e}")
        return None


#def run_query(query, params=None, fetch=False):
#    with engine.begin() as conn:
#        result = conn.execute(text(query), params or {})
#        if fetch:
#            return result.fetchall()


# =========================================================
# CREATE DEFAULT ADMIN
# =========================================================
# CREATE DEFAULT ADMIN
existing_admin = run_query(
    "SELECT * FROM users WHERE username='admin'", fetch=True
)

if not existing_admin:
    run_query(
        """
        INSERT INTO users (username, password, role)
        VALUES ('admin','admin123','Admin')
        """
    )
#run_query(
#    """
#INSERT INTO users (username, password, role)
#SELECT 'admin','admin123','Admin'
#WHERE NOT EXISTS (
#SELECT 1 FROM users WHERE username='admin'
#)
#"""
#)

# =========================================================
# LOGIN
# =========================================================
def check_login(username, password):
    result = run_query(
        """
        SELECT username, role
        FROM users
        WHERE username=:username
        AND password=:password
        """,
        {"username": username, "password": password},
        True,
    )
    return result


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = check_login(username, password)

        if user:
            st.session_state.logged_in = True
            st.session_state.role = user[0][1]
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid login")

    st.stop()

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("Navigation")

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Dashboard",
        "Register Student",
        "Student List",
        "Student Payment",
        "Payment History",
        "School Fee Settings",
        "Revenue Dashboard",
        "Debt Report",
        "Promote Students",
    ],
)

# =========================================================
# DASHBOARD
# =========================================================
if menu == "Dashboard":
    st.subheader("Search Student")

    search = st.text_input("Search Student (Name or ID)")

    if st.button("Search"):
        result = run_query(
            """
        SELECT * FROM students
        WHERE student_id=:search
        OR full_name ILIKE :name
        """,
            {"search": search, "name": f"%{search}%"},
            True,
        )

        if result:
            df = pd.DataFrame(result)
            st.dataframe(df)

# =========================================================
# REGISTER STUDENT
# =========================================================
elif menu == "Register Student":
    st.subheader("Register Student")

    student_id = st.text_input("Student ID")
    name = st.text_input("Full Name")
    student_class = st.text_input("Class")
    section = st.selectbox("Section", ["Nursery", "Primary", "Secondary"])
    session = st.text_input("Session e.g 2025/2026")

    if st.button("Save Student"):
        run_query(
            """
        INSERT INTO students
        (student_id, full_name, student_class, section, session)
        VALUES (:student_id,:name,:student_class,:section,:session)
        """,
            {
                "student_id": student_id,
                "name": name,
                "student_class": student_class,
                "section": section,
                "session": session,
            },
        )
        st.success("Student Registered")

# =========================================================
# STUDENT LIST
# =========================================================
elif menu == "Student List":
    st.subheader("All Students")

    data = run_query("SELECT * FROM students ORDER BY id DESC", fetch=True)
    df = pd.DataFrame(data)
    st.dataframe(df)

    if st.session_state.role == "Admin":
        delete_id = st.text_input("Delete Student ID")

        if st.button("Delete Student"):
            run_query(
                "DELETE FROM students WHERE student_id=:id",
                {"id": delete_id},
            )
            st.success("Deleted")

# =========================================================
# SCHOOL FEE SETTINGS
# =========================================================
elif menu == "School Fee Settings":
    st.subheader("Set School Fees")

    section = st.selectbox("Section", ["Nursery", "Primary", "Secondary"])
    term = st.selectbox("Term", ["First Term", "Second Term", "Third Term"])
    session = st.text_input("Session")
    fee = st.number_input("Fee Amount")

    if st.button("Save Fee"):
        run_query(
            """
        INSERT INTO school_fee_settings
        (section, term, session, fee_amount)
        VALUES (:section,:term,:session,:fee)
        """,
            {
                "section": section,
                "term": term,
                "session": session,
                "fee": fee,
            },
        )
        st.success("Fee Saved")

    st.subheader("Fee Records")

    df = pd.DataFrame(
        run_query("SELECT * FROM school_fee_settings", fetch=True)
    )
    st.dataframe(df)

# =========================================================
# STUDENT PAYMENT
# =========================================================
elif menu == "Student Payment":
    st.subheader("Student Payment")

    students = run_query(
        "SELECT student_id, full_name, section FROM students",
        fetch=True,
    )

    options = {f"{s[1]} ({s[0]})": s for s in students}

    selected = st.selectbox("Select Student", list(options.keys()))

    term = st.selectbox("Term", ["First Term", "Second Term", "Third Term"])
    session = st.text_input("Session")

    amount_paid = st.number_input("Amount Paid")

    if st.button("Process Payment"):
        student = options[selected]

        student_id = student[0]
        name = student[1]
        section = student[2]

        fee_result = run_query(
            """
        SELECT fee_amount
        FROM school_fee_settings
        WHERE section=:section
        AND term=:term
        AND session=:session
        """,
            {
                "section": section,
                "term": term,
                "session": session,
            },
            True,
        )

        if not fee_result:
            st.error("Fee not set")
            st.stop()

        fee = fee_result[0][0]

        debt_result = run_query(
            """
        SELECT COALESCE(SUM(balance),0)
        FROM payments
        WHERE student_id=:student_id
        """,
            {"student_id": student_id},
            True,
        )

        previous_debt = debt_result[0][0]

        total_due = fee + previous_debt
        balance = total_due - amount_paid

        run_query(
            """
        INSERT INTO payments
        (student_id, student_name, term, session, fee_amount,
        previous_debt, amount_paid, balance)
        VALUES
        (:student_id,:name,:term,:session,:fee,
        :previous_debt,:paid,:balance)
        """,
            {
                "student_id": student_id,
                "name": name,
                "term": term,
                "session": session,
                "fee": fee,
                "previous_debt": previous_debt,
                "paid": amount_paid,
                "balance": balance,
            },
        )

        st.success("Payment Recorded")

        receipt = pd.DataFrame(
            {
                "Student": [name],
                "Fee": [fee],
                "Previous Debt": [previous_debt],
                "Paid": [amount_paid],
                "Balance": [balance],
            }
        )

        st.subheader("School Payment Receipt")
        st.table(receipt)

# =========================================================
# PAYMENT HISTORY
# =========================================================
elif menu == "Payment History":
    st.subheader("Payment Records")

    data = run_query(
        "SELECT * FROM payments ORDER BY id DESC",
        fetch=True,
    )
    df = pd.DataFrame(data)
    st.dataframe(df)

    if st.button("Export Excel"):
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button(
            "Download",
            output.getvalue(),
            file_name="payments.xlsx",
        )

    if st.session_state.role == "Admin":
        delete_id = st.number_input("Delete Payment ID")

        if st.button("Delete Payment"):
            run_query(
                "DELETE FROM payments WHERE id=:id",
                {"id": delete_id},
            )
            st.success("Deleted")

# =========================================================
# REVENUE DASHBOARD
# =========================================================
elif menu == "Revenue Dashboard":
    st.subheader("School Revenue")

    data = run_query(
        """
    SELECT session, SUM(amount_paid)
    FROM payments
    GROUP BY session
    """,
        fetch=True,
    )

    df = pd.DataFrame(data, columns=["Session", "Revenue"])
    st.bar_chart(df.set_index("Session"))

# =========================================================
# DEBT REPORT
# =========================================================
elif menu == "Debt Report":
    st.subheader("Student Debt Report")

    data = run_query(
        """
    SELECT student_name, SUM(balance)
    FROM payments
    GROUP BY student_name
    HAVING SUM(balance) > 0
    """,
        fetch=True,
    )

    df = pd.DataFrame(data, columns=["Student", "Debt"])
    st.dataframe(df)

# =========================================================
# PROMOTION SYSTEM
# =========================================================
elif menu == "Promote Students":
    st.subheader("Promote Students")

    new_session = st.text_input("New Session")

    if st.button("Promote All Students"):
        run_query(
            """
        UPDATE students
        SET session=:new_session
        """,
            {"new_session": new_session},
        )

        st.success("Students Promoted")
