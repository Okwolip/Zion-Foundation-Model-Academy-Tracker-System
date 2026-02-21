import sqlite3

DB_NAME = "school.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# CREATE TABLES
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # USERS TABLE (Login system)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)

    # STUDENTS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        class_name TEXT,
        gender TEXT,
        parent_name TEXT,
        parent_phone TEXT,
        address TEXT,
        session TEXT
    )
    """)

    # FEES TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        amount REAL,
        term TEXT,
        session TEXT,
        date_paid TEXT,
        FOREIGN KEY(student_id) REFERENCES students(student_id)
    )
    """)

    conn.commit()
    conn.close()


# CREATE DEFAULT ADMIN
def create_default_admin():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO users (username, password, role)
    VALUES (?, ?, ?)
    """, ("admin", "admin123", "admin"))

    conn.commit()
    conn.close()


# ADD USER
def add_user(username, password, role):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO users (username, password, role)
    VALUES (?, ?, ?)
    """, (username, password, role))

    conn.commit()
    conn.close()


# LOGIN USER
def login_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM users
    WHERE username = ? AND password = ?
    """, (username, password))

    user = cursor.fetchone()
    conn.close()

    return user


# ADD STUDENT
def add_student(name, class_name, gender, parent_name, parent_phone, address, session):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO students (name, class_name, gender, parent_name, parent_phone, address, session)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, class_name, gender, parent_name, parent_phone, address, session))

    conn.commit()
    conn.close()


# GET ALL STUDENTS
def get_students():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    conn.close()
    return students


# DELETE STUDENT
def delete_student(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))

    conn.commit()
    conn.close()


# RECORD FEE PAYMENT
def record_fee(student_id, amount, term, session, date_paid):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO fees (student_id, amount, term, session, date_paid)
    VALUES (?, ?, ?, ?, ?)
    """, (student_id, amount, term, session, date_paid))

    conn.commit()
    conn.close()


# GET TOTAL STUDENTS
def get_total_students():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM students")
    total = cursor.fetchone()["total"]

    conn.close()
    return total


# TOTAL REVENUE BY SESSION
def get_total_revenue_by_session(session):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT SUM(amount) as total
    FROM fees
    WHERE session = ?
    """, (session,))

    result = cursor.fetchone()["total"]
    conn.close()

    if result is None:
        return 0
    return result


# GET ALL TRANSACTIONS
def get_transactions():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT students.name, fees.amount, fees.term, fees.session, fees.date_paid
    FROM fees
    JOIN students ON students.student_id = fees.student_id
    """)

    transactions = cursor.fetchall()
    conn.close()

    return transactions
