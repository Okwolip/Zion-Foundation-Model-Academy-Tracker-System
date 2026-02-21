import sqlite3

# ---------------------------------------------------
# DATABASE NAME
# ---------------------------------------------------

DB_NAME = "school.db"


# ---------------------------------------------------
# GET DATABASE CONNECTION
# ---------------------------------------------------

def get_connection():
    """
    Returns a SQLite connection with foreign keys enabled
    """
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# ---------------------------------------------------
# CREATE TABLES
# ---------------------------------------------------

def create_tables():
    """
    Creates all system tables if they do not exist
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # ---------------------------------------------------
        # STUDENTS TABLE
        # ---------------------------------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            gender TEXT,
            section TEXT NOT NULL,
            class TEXT NOT NULL,
            parent_phone TEXT,
            admission_date TEXT,
            status TEXT DEFAULT 'Active'
        );
        """)

        # ---------------------------------------------------
        # FEES TABLE
        # ---------------------------------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section TEXT NOT NULL,
            term TEXT NOT NULL,
            session TEXT NOT NULL,
            total_fee REAL NOT NULL,
            UNIQUE(section, term, session)
        );
        """)

        # ---------------------------------------------------
        # PAYMENTS TABLE
        # ---------------------------------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            term TEXT NOT NULL,
            session TEXT NOT NULL,
            amount_paid REAL NOT NULL CHECK(amount_paid >= 0),
            payment_date TEXT NOT NULL,
            FOREIGN KEY (student_id)
            REFERENCES students(student_id)
            ON DELETE CASCADE
        );
        """)
        # USERS TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            name TEXT,
            password TEXT,
            role TEXT
        );
        """)

        # ---------------------------------------------------
        # OUTSTANDING BALANCES
        # ---------------------------------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS outstanding_balances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            session TEXT NOT NULL,
            amount REAL NOT NULL,
            UNIQUE(student_id, session),
            FOREIGN KEY (student_id)
            REFERENCES students(student_id)
            ON DELETE CASCADE
        );
        """)

        # ---------------------------------------------------
        # INDEXES (Performance)
        # ---------------------------------------------------
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payment_student
        ON payments(student_id);
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payment_session
        ON payments(session);
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_fee_lookup
        ON fees(section, term, session);
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_student_section
        ON students(section);
        """)

        conn.commit()

    finally:
        conn.close()


# ---------------------------------------------------
# RESET DATABASE (FOR DEVELOPMENT ONLY)
# ---------------------------------------------------

def reset_database():
    """
    Deletes all tables and recreates them.
    Use only during development/testing.
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Drop dependent tables first
        cursor.execute("DROP TABLE IF EXISTS payments")
        cursor.execute("DROP TABLE IF EXISTS outstanding_balances")
        cursor.execute("DROP TABLE IF EXISTS fees")
        cursor.execute("DROP TABLE IF EXISTS students")

        conn.commit()

    finally:
        conn.close()

    # Recreate tables
    create_tables()

import sqlite3

# ---------------------------------------------------
# DATABASE NAME
# ---------------------------------------------------

DB_NAME = "school.db"


# ---------------------------------------------------
# GET DATABASE CONNECTION
# ---------------------------------------------------

def get_connection():
    """
    Returns a SQLite connection with foreign keys enabled
    """
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# ---------------------------------------------------
# CREATE TABLES
# ---------------------------------------------------

def create_tables():
    """
    Creates all system tables if they do not exist
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # ---------------------------------------------------
        # STUDENTS TABLE
        # ---------------------------------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            gender TEXT,
            section TEXT NOT NULL,
            class TEXT NOT NULL,
            parent_phone TEXT,
            admission_date TEXT,
            status TEXT DEFAULT 'Active'
        );
        """)

        # ---------------------------------------------------
        # FEES TABLE
        # ---------------------------------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section TEXT NOT NULL,
            term TEXT NOT NULL,
            session TEXT NOT NULL,
            total_fee REAL NOT NULL,
            UNIQUE(section, term, session)
        );
        """)

        # ---------------------------------------------------
        # PAYMENTS TABLE
        # ---------------------------------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            term TEXT NOT NULL,
            session TEXT NOT NULL,
            amount_paid REAL NOT NULL CHECK(amount_paid >= 0),
            payment_date TEXT NOT NULL,
            FOREIGN KEY (student_id)
            REFERENCES students(student_id)
            ON DELETE CASCADE
        );
        """)

        # ---------------------------------------------------
        # OUTSTANDING BALANCES
        # ---------------------------------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS outstanding_balances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            session TEXT NOT NULL,
            amount REAL NOT NULL,
            UNIQUE(student_id, session),
            FOREIGN KEY (student_id)
            REFERENCES students(student_id)
            ON DELETE CASCADE
        );
        """)

        # ---------------------------------------------------
        # INDEXES (Performance)
        # ---------------------------------------------------
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payment_student
        ON payments(student_id);
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payment_session
        ON payments(session);
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_fee_lookup
        ON fees(section, term, session);
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_student_section
        ON students(section);
        """)

        conn.commit()

    finally:
        conn.close()


# ---------------------------------------------------
# RESET DATABASE (FOR DEVELOPMENT ONLY)
# ---------------------------------------------------

def reset_database():
    """
    Deletes all tables and recreates them.
    Use only during development/testing.
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Drop dependent tables first
        cursor.execute("DROP TABLE IF EXISTS payments")
        cursor.execute("DROP TABLE IF EXISTS outstanding_balances")
        cursor.execute("DROP TABLE IF EXISTS fees")
        cursor.execute("DROP TABLE IF EXISTS students")

        conn.commit()

    finally:
        conn.close()

    # Recreate tables
    create_tables()

    def create_default_admin():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    user = cursor.fetchone()

    if not user:
        cursor.execute("""
        INSERT INTO users (username, name, password, role)
        VALUES (?, ?, ?, ?)
        """, (
            "admin",
            "Administrator",
            "admin123",
            "Admin"
        ))

        conn.commit()

    conn.close()
