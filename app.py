import streamlit as st
import pandas as pd
import sqlite3

# -------------------------------------------------
# PAGE CONFIG (must be first Streamlit command)
# -------------------------------------------------
st.set_page_config(
    page_title="School Management System",
    page_icon="🏫",
    layout="wide"
)

# -------------------------------------------------
# UI Styling
# -------------------------------------------------
st.markdown("""
<style>
.main {
    background-color: #f5f7fb;
}
h1, h2, h3 {
    color: #1f4e79;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# IMPORT PROJECT FILES
# -------------------------------------------------
from database import create_tables, create_default_admin
create_tables()
create_default_admin()
from models import (
    add_student,
    get_all_students,
    add_payment,
    get_payments,
    total_students,
    total_revenue,
    set_fee,
    get_current_fee,
    get_total_paid,
    get_previous_outstanding,
    rollover_outstanding,
    delete_student
)
from pdf_report import generate_student_statement

# -------------------------------------------------
# INITIALIZE DATABASE
# -------------------------------------------------
create_tables()
create_default_admin()

# -------------------------------------------------
# LOGIN FUNCTION
# -------------------------------------------------
#def check_login(username, password):
    #import sqlite3

    #conn = sqlite3.connect("school.db")
    #cursor = conn.cursor()
    import streamlit as st
    from sqlalchemy import create_engine, text

    DATABASE_URL = st.secrets["DATABASE_URL"]

    engine = create_engine(DATABASE_URL)
    conn = engine.connect()


 def check_login(username, password):
    query = text("SELECT * FROM users WHERE username=:username AND password=:password")
    result = conn.execute(query, {"username": username, "password": password}).fetchone()
    return result

#    cursor.execute(
#        "SELECT username, role FROM users WHERE username=? AND password=?",
#        (username, password)
#    )
#
#    user = cursor.fetchone()
#    conn.close()

 #   return user


# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# -------------------------------------------------
# LOGIN PAGE
# -------------------------------------------------
if not st.session_state.logged_in:

    st.title("School Management System Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = check_login(username, password)

        if user:
            st.session_state.logged_in = True
            st.session_state.name = user[0]
            st.session_state.role = user[1]
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid username or password")

    st.stop()

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.title("Navigation")

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Dashboard",
        "Manage Students",
        "Payments",
        "Fee Management",
        "Promote Session"
    ],
    key="main_menu"
)

st.sidebar.write(f"Logged in as: {st.session_state.name}")
st.sidebar.write(f"Role: {st.session_state.role}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.title("Zion Foundation Model Academy")

# =================================================
# DASHBOARD
# =================================================
if menu == "Dashboard":

    st.header("School Overview")

    session = st.text_input("Enter Session (Example: 2024/2025)")

    col1, col2 = st.columns(2)

    col1.metric("Total Students", total_students())

    if session:
        revenue = total_revenue(session)
        col2.metric(f"Revenue for {session}", f"₦{revenue:,.2f}")
    else:
        col2.metric("Revenue", "Enter Session")

# =================================================
# MANAGE STUDENTS
# =================================================
elif menu == "Manage Students":

    st.header("Add New Student")

    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    gender = st.selectbox("Gender", ["Male", "Female"])
    section = st.selectbox("Section", ["Nursery", "Primary", "Secondary"])
    student_class = st.text_input("Class")
    parent_phone = st.text_input("Parent Phone")
    admission_date = st.date_input("Admission Date")
    status = st.selectbox("Status", ["Active", "Inactive"])

    if st.button("Add Student"):
        if first_name and last_name:
            add_student(
                first_name,
                last_name,
                gender,
                section,
                student_class,
                parent_phone,
                str(admission_date),
                status
            )
            st.success("Student added successfully")
            st.rerun()

    st.divider()
    st.subheader("Students List")

    students = get_all_students()

    if students:
        df = pd.DataFrame(students, columns=[
            "ID","First Name","Last Name","Gender",
            "Section","Class","Phone","Admission Date","Status"
        ])

        df["Name"] = df["First Name"] + " " + df["Last Name"]

        for _, row in df.iterrows():
            col1, col2, col3, col4 = st.columns([4,2,2,1])

            col1.write(row["Name"])
            col2.write(row["Class"])
            col3.write(row["Section"])

            if col4.button("Delete", key=row["ID"]):
                st.session_state.delete_id = row["ID"]

        if "delete_id" in st.session_state:
            st.warning("Confirm delete student")

            c1, c2 = st.columns(2)

            if c1.button("Yes Delete"):
                delete_student(st.session_state.delete_id)
                del st.session_state.delete_id
                st.success("Student deleted")
                st.rerun()

            if c2.button("Cancel"):
                del st.session_state.delete_id
                st.rerun()

# =================================================
# PAYMENTS
# =================================================
elif menu == "Payments":

    st.header("Student Payments")

    students = get_all_students()

    if not students:
        st.warning("Add students first")
    else:

        df = pd.DataFrame(students, columns=[
            "ID","First Name","Last Name","Gender",
            "Section","Class","Phone","Admission Date","Status"
        ])

        df["Name"] = df["First Name"] + " " + df["Last Name"]

        selected = st.selectbox("Select Student", df["Name"])

        row = df[df["Name"] == selected].iloc[0]

        student_id = row["ID"]
        section = row["Section"]
        student_class = row["Class"]

        term = st.selectbox("Term", ["1st","2nd","3rd"])
        session = st.text_input("Session")

        if session:

            prev = get_previous_outstanding(student_id, session)
            fee = get_current_fee(section, term, session)
            paid = get_total_paid(student_id, term, session)

            owed = (prev + fee) - paid

            col1, col2 = st.columns(2)

            col1.metric("Previous Outstanding", f"₦{prev:,.2f}")
            col1.metric("Current Fee", f"₦{fee:,.2f}")

            col2.metric("Paid", f"₦{paid:,.2f}")
            col2.metric("Amount Owed", f"₦{owed:,.2f}")

            st.divider()

            amount = st.number_input("Amount Paid", min_value=0.0)
            date = st.date_input("Payment Date")

            if st.button("Save Payment"):
                add_payment(student_id, term, session, amount, str(date))
                st.success("Payment recorded")
                st.rerun()

            st.divider()

            st.subheader("Generate Statement")

            if st.button("Generate PDF"):
                file = generate_student_statement(
                    selected,
                    section,
                    student_class,
                    session,
                    prev,
                    fee,
                    paid,
                    owed
                )

                with open(file, "rb") as f:
                    st.download_button(
                        "Download Statement",
                        data=f,
                        file_name=file
                    )

# =================================================
# FEE MANAGEMENT
# =================================================
elif menu == "Fee Management":

    if st.session_state.role != "Admin":
        st.warning("Admin only")
        st.stop()

    st.header("Set School Fees")

    section = st.selectbox("Section", ["Nursery","Primary","Secondary"])
    term = st.selectbox("Term", ["1st","2nd","3rd"])
    session = st.text_input("Session")
    fee = st.number_input("Fee Amount")

    if st.button("Save Fee"):
        set_fee(section, term, session, fee)
        st.success("Fee saved")

# =================================================
# PROMOTE SESSION
# =================================================
elif menu == "Promote Session":

    if st.session_state.role != "Admin":
        st.warning("Admin only")
        st.stop()

    st.header("Promote Session")

    new_session = st.text_input("New Session")

    if st.button("Roll Over"):
        rollover_outstanding(new_session)
        st.success("Promotion complete")
