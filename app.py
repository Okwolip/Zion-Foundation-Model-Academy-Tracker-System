import pandas as pd
import streamlit as st
from database import create_tables
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

# Initialize database
create_tables()

# -------------------------------
# SIDEBAR NAVIGATION
# -------------------------------
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

st.title("Zion Foundation Model Academy")

# ==================================================
# DASHBOARD
# ==================================================
if menu == "Dashboard":

    st.header("School Overview")

    # Select session
    session = st.text_input("Enter Session to View Revenue (Example: 2024/2025)")

    col1, col2 = st.columns(2)

    col1.metric("Total Students", total_students())

    if session:
        revenue = total_revenue(session)
        col2.metric(
            f"Revenue for {session}",
            f"₦{revenue:,.2f}"
        )
    else:
        col2.metric(
            "Revenue (Enter Session)",
            "₦0.00"
        )
# ==================================================
# MANAGE STUDENTS
# ==================================================
elif menu == "Manage Students":

    st.header("Add New Student")

    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    gender = st.selectbox("Gender", ["Male", "Female"], key="gender_select")
    section = st.selectbox("Section", ["Nursery", "Primary", "Secondary"])
    student_class = st.text_input("Class")
    parent_phone = st.text_input("Parent Phone")
    admission_date = st.date_input("Admission Date")
    status = st.selectbox("Status", ["Active", "Inactive"])

    if st.button("Add Student"):
        if first_name.strip() and last_name.strip():
            add_student(
                first_name.strip(),
                last_name.strip(),
                gender,
                section,
                student_class.strip(),
                parent_phone.strip(),
                str(admission_date),
                status
            )
            st.success("Student added successfully!")
            st.rerun()
        else:
            st.warning("Please enter student first and last name.")

    st.divider()
    st.subheader("All Students")

    students = get_all_students()

    if students:
        student_df = pd.DataFrame(students, columns=[
            "ID", "First Name", "Last Name", "Gender",
            "Section", "Class", "Phone", "Admission Date", "Status"
        ])

        student_df["Name"] = student_df["First Name"] + " " + student_df["Last Name"]

        for index, row in student_df.iterrows():
            col1, col2, col3, col4 = st.columns([3,2,2,1])

            with col1:
                st.write(f"**{row['Name']}**")

            with col2:
                st.write(row["Class"])

            with col3:
                st.write(row["Section"])

            with col4:
                if st.button("Delete", key=f"del_{row['ID']}"):
                    st.session_state["delete_id"] = row["ID"]

        # Confirmation warning
        if "delete_id" in st.session_state:
            st.warning("Are you sure you want to permanently delete this student?")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Yes, Delete"):
                    delete_student(st.session_state["delete_id"])
                    st.success("Student deleted successfully.")
                    del st.session_state["delete_id"]
                    st.rerun()

            with col2:
                if st.button("Cancel"):
                    del st.session_state["delete_id"]
                    st.rerun()

    else:
        st.info("No students found.")

# ==================================================
# PAYMENTS
# ==================================================
elif menu == "Payments":

    st.header("Student Payments")

    students = get_all_students()

    if not students:
        st.warning("Please add students first.")
    else:

        student_df = pd.DataFrame(students, columns=[
            "ID", "First Name", "Last Name", "Gender",
            "Section", "Class", "Phone", "Admission Date", "Status"
        ])

        student_df["Name"] = student_df["First Name"] + " " + student_df["Last Name"]

        selected_name = st.selectbox(
            "Select Student",
            student_df["Name"],
            key="payment_student"
        )

        student_row = student_df[student_df["Name"] == selected_name].iloc[0]

        student_id = student_row["ID"]
        section = student_row["Section"]
        student_class = student_row["Class"]

        term = st.selectbox("Term", ["1st", "2nd", "3rd"], key="payment_term")
        session = st.text_input("Session (Example: 2024/2025)", key="payment_session")

        if session:

            previous_outstanding = get_previous_outstanding(student_id, session)
            current_fee = get_current_fee(section, term, session)
            total_paid = get_total_paid(student_id, term, session)

            amount_owed = (previous_outstanding + current_fee) - total_paid

            st.subheader("Financial Summary")

            col1, col2 = st.columns(2)

            col1.metric("Previous Outstanding", f"₦{previous_outstanding:,.2f}")
            col1.metric("Current Term Fee", f"₦{current_fee:,.2f}")

            col2.metric("Total Paid This Term", f"₦{total_paid:,.2f}")
            col2.metric("Amount Owed", f"₦{amount_owed:,.2f}")

            if current_fee == 0:
                st.warning("Fee has not been set for this section, term, and session.")

            st.divider()

            st.subheader("Record Payment")

            amount = st.number_input("Amount Paid", min_value=0.0)
            payment_date = st.date_input("Payment Date")

            if st.button("Save Payment"):
                if amount > 0:
                    add_payment(
                        student_id,
                        term,
                        session,
                        amount,
                        str(payment_date)
                    )
                    st.success("Payment recorded successfully.")
                    st.rerun()
                else:
                    st.warning("Enter payment amount.")
