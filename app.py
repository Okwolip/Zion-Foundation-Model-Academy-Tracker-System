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
    rollover_outstanding
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
    ]
)

st.title("Smart School Record Tracker")

# ==================================================
# DASHBOARD
# ==================================================
if menu == "Dashboard":

    st.header("School Overview")

    col1, col2 = st.columns(2)

    col1.metric("Total Students", total_students())
    col2.metric("Total Revenue Collected", f"₦{total_revenue():,.2f}")


# ==================================================
# ADD / MANAGE STUDENTS
# ==================================================
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
            st.success("Student added successfully!")
            st.rerun()
        else:
            st.warning("Enter student name.")

    st.subheader("All Students")

    students = get_all_students()

    if students:
        student_df = pd.DataFrame(students, columns=[
            "ID", "First Name", "Last Name", "Gender",
            "Section", "Class", "Phone", "Admission Date", "Status"
        ])
        student_df["Name"] = student_df["First Name"] + " " + student_df["Last Name"]
        st.dataframe(student_df)
    else:
        st.info("No students yet.")


# ==================================================
# PAYMENTS
# ==================================================
elif menu == "Payments":

    st.header("Student Payments")

    students = get_all_students()

    if not students:
        st.warning("No students available.")
    else:

        student_df = pd.DataFrame(students, columns=[
            "ID", "First Name", "Last Name", "Gender",
            "Section", "Class", "Phone", "Admission Date", "Status"
        ])

        student_df["Name"] = student_df["First Name"] + " " + student_df["Last Name"]

        selected_name = st.selectbox("Select Student", student_df["Name"])

        student_row = student_df[student_df["Name"] == selected_name].iloc[0]

        student_id = student_row["ID"]
        section = student_row["Section"]

        term = st.selectbox("Term", ["1st", "2nd", "3rd"])
        session = st.text_input("Session (example: 2024/2025)")

        if session:

            # Accounting logic
            previous_outstanding = get_previous_outstanding(student_id, session)
            current_fee = get_current_fee(section, term, session)
            total_paid = get_total_paid(student_id, term, session)

            amount_owed = (previous_outstanding + current_fee) - total_paid

            st.markdown("### Financial Summary")

            col1, col2 = st.columns(2)

            col1.metric("Previous Outstanding", f"₦{previous_outstanding:,.2f}")
            col1.metric("Current Fee", f"₦{current_fee:,.2f}")

            col2.metric("Total Paid", f"₦{total_paid:,.2f}")
            col2.metric("Amount Owed", f"₦{amount_owed:,.2f}")

            st.divider()

            # Record Payment
            st.subheader("Record Payment")

            amount = st.number_input("Amount Paid", min_value=0.0)
            payment_date = st.date_input("Payment Date")

            if st.button("Save Payment"):
                add_payment(
                    student_id,
                    term,
                    session,
                    amount,
                    str(payment_date)
                )
                st.success("Payment recorded successfully.")
                st.rerun()

            st.divider()

            # Payment History
            st.subheader("Payment History")

            payments = get_payments()

            if payments:
                payment_df = pd.DataFrame(payments, columns=[
                    "Payment ID",
                    "Student ID",
                    "Term",
                    "Session",
                    "Amount",
                    "Date"
                ])

                student_payments = payment_df[payment_df["Student ID"] == student_id]
                st.dataframe(student_payments)
            else:
                st.info("No payment history.")

            st.divider()

            # PDF GENERATION
            st.subheader("Generate Student Statement")

            if st.button("Generate PDF Statement"):

                file_path = generate_student_statement(
                    selected_name,
                    section,
                    student_row["Class"],
                    session,
                    previous_outstanding,
                    current_fee,
                    total_paid,
                    amount_owed
                )

                with open(file_path, "rb") as file:
                    st.download_button(
                        label="Download Statement",
                        data=file,
                        file_name=file_path,
                        mime="application/pdf"
                    )


# ==================================================
# FEE MANAGEMENT
# ==================================================
elif menu == "Fee Management":

    st.header("Set School Fees")

    section = st.selectbox("Section", ["Nursery", "Primary", "Secondary"])
    term = st.selectbox("Term", ["1st", "2nd", "3rd"])
    session = st.text_input("Session (example: 2024/2025)")
    fee = st.number_input("Fee Amount", min_value=0.0)

    if st.button("Save Fee"):
        set_fee(section, term, session, fee)
        st.success("Fee saved successfully.")
        st.rerun()


# ==================================================
# PROMOTE SESSION (AUTO ROLLOVER)
# ==================================================
elif menu == "Promote Session":

    st.header("Promote to New Session")

    new_session = st.text_input("Enter New Session")

    if st.button("Roll Over Outstanding Balances"):
        rollover_outstanding(new_session)
        st.success("Students promoted and outstanding balances rolled over.")
