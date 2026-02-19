import uuid
from database import get_connection


# =========================================================
# STUDENT FUNCTIONS
# =========================================================

def add_student(first_name, last_name, gender, section,
                student_class, parent_phone,
                admission_date, status):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        student_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO students (
                student_id,
                first_name,
                last_name,
                gender,
                section,
                class,
                parent_phone,
                admission_date,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            first_name,
            last_name,
            gender,
            section,
            student_class,
            parent_phone,
            admission_date,
            status
        ))

        conn.commit()
        return student_id

    finally:
        conn.close()


def get_all_students():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                student_id,
                first_name,
                last_name,
                gender,
                section,
                class,
                parent_phone,
                admission_date,
                status
            FROM students
            ORDER BY first_name ASC
        """)

        return cursor.fetchall()

    finally:
        conn.close()


def get_student(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM students
            WHERE student_id = ?
        """, (student_id,))
        return cursor.fetchone()

    finally:
        conn.close()


# =========================================================
# PAYMENT FUNCTIONS
# =========================================================

def add_payment(student_id, term, session,
                amount_paid, payment_date):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        payment_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO payments (
                payment_id,
                student_id,
                term,
                session,
                amount_paid,
                payment_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            payment_id,
            student_id,
            term,
            session,
            amount_paid,
            payment_date
        ))

        conn.commit()
        return payment_id

    finally:
        conn.close()


def get_payments():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                payment_id,
                student_id,
                term,
                session,
                amount_paid,
                payment_date
            FROM payments
            ORDER BY payment_date DESC
        """)

        return cursor.fetchall()

    finally:
        conn.close()


def get_student_payments(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                payment_id,
                term,
                session,
                amount_paid,
                payment_date
            FROM payments
            WHERE student_id = ?
            ORDER BY payment_date DESC
        """, (student_id,))

        return cursor.fetchall()

    finally:
        conn.close()


# =========================================================
# DASHBOARD FUNCTIONS
# =========================================================

def total_students():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM students")
        result = cursor.fetchone()
        return result[0] if result else 0
    finally:
        conn.close()


def total_revenue():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT SUM(amount_paid) FROM payments")
        result = cursor.fetchone()
        return result[0] if result and result[0] else 0
    finally:
        conn.close()


# =========================================================
# FEE MANAGEMENT
# =========================================================

def set_fee(section, term, session, total_fee):
    """
    Set or update school fee for a section in a term/session
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id
            FROM fees
            WHERE section = ?
            AND term = ?
            AND session = ?
        """, (section, term, session))

        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE fees
                SET total_fee = ?
                WHERE section = ?
                AND term = ?
                AND session = ?
            """, (total_fee, section, term, session))
        else:
            cursor.execute("""
                INSERT INTO fees (
                    section,
                    term,
                    session,
                    total_fee
                )
                VALUES (?, ?, ?, ?)
            """, (section, term, session, total_fee))

        conn.commit()

    finally:
        conn.close()


def get_current_fee(section, term, session):
    """
    Get fee for a section in a specific term/session
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT total_fee
            FROM fees
            WHERE section = ?
            AND term = ?
            AND session = ?
        """, (section, term, session))

        result = cursor.fetchone()
        return result[0] if result else 0

    finally:
        conn.close()


# =========================================================
# PAYMENT CALCULATIONS
# =========================================================

def get_total_paid(student_id, term, session):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT SUM(amount_paid)
            FROM payments
            WHERE student_id = ?
            AND term = ?
            AND session = ?
        """, (student_id, term, session))

        result = cursor.fetchone()
        return result[0] if result and result[0] else 0

    finally:
        conn.close()


def get_previous_outstanding(student_id, current_session):
    """
    Outstanding balance from previous sessions
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Get student section
        cursor.execute("""
            SELECT section
            FROM students
            WHERE student_id = ?
        """, (student_id,))
        student = cursor.fetchone()

        if not student:
            return 0

        section = student[0]

        # Get all previous sessions
        cursor.execute("""
            SELECT DISTINCT session
            FROM fees
            WHERE session != ?
        """, (current_session,))
        sessions = cursor.fetchall()

        total_outstanding = 0

        for sess in sessions:
            session_name = sess[0]

            # Total fee for that session
            cursor.execute("""
                SELECT SUM(total_fee)
                FROM fees
                WHERE section = ?
                AND session = ?
            """, (section, session_name))
            total_fee = cursor.fetchone()[0] or 0

            # Total paid in that session
            cursor.execute("""
                SELECT SUM(amount_paid)
                FROM payments
                WHERE student_id = ?
                AND session = ?
            """, (student_id, session_name))
            total_paid = cursor.fetchone()[0] or 0

            outstanding = max(total_fee - total_paid, 0)
            total_outstanding += outstanding

        return total_outstanding

    finally:
        conn.close()


# =========================================================
# SESSION PROMOTION / ROLLOVER
# =========================================================

def rollover_outstanding(new_session):
    """
    Processes outstanding balances when a new session starts.
    Currently recalculates outstanding but does not modify records.
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT student_id FROM students")
        students = cursor.fetchall()

        results = []

        for student in students:
            student_id = student[0]
            outstanding = get_previous_outstanding(student_id, new_session)

            results.append({
                "student_id": student_id,
                "outstanding": outstanding
            })

        return results

    finally:
        conn.close()
