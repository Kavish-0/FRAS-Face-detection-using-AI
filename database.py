<<<<<<< HEAD
import mysql.connector
from datetime import datetime
import csv
import io

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "test@123456789",
    "database": "face_attendance"
}

def _get_conn():
    return mysql.connector.connect(**DB_CONFIG)


# ===============================
# ADD STUDENT
# ===============================

def add_student(student_id, name):

    conn = _get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO students (id, name) VALUES (%s,%s)",
        (student_id, name)
    )

    conn.commit()
    cursor.close()
    conn.close()


# ===============================
# DELETE STUDENT
# ===============================

def delete_student(student_id):

    conn = _get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM attendance WHERE id=%s",
        (student_id,)
    )

    cursor.execute(
        "DELETE FROM students WHERE id=%s",
        (student_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()


# ===============================
# GET STUDENTS
# ===============================

def get_all_students():

    conn = _get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT id,name FROM students")

    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return students


# ===============================
# GET STUDENT NAME
# ===============================

def get_student_name(student_id):

    conn = _get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM students WHERE id=%s",
        (student_id,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result[0] if result else None


# ===============================
# MARK ATTENDANCE
# ===============================

def mark_attendance(student_id):

    conn = _get_conn()
    cursor = conn.cursor()

    today = datetime.now().date()

    cursor.execute(
        "SELECT * FROM attendance WHERE id=%s AND date=%s",
        (student_id, today)
    )

    if cursor.fetchone() is None:

        cursor.execute(
            "INSERT INTO attendance (id,date,time) VALUES (%s,CURDATE(),NOW())",
            (student_id,)
        )

        conn.commit()

    cursor.close()
    conn.close()


# ===============================
# DASHBOARD STATS
# ===============================

def get_total_students():

    conn = _get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")

    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return count


def get_today_attendance():

    conn = _get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM attendance WHERE date=CURDATE()"
    )

    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return count


def get_last_attendance():

    conn = _get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT students.name
        FROM attendance
        JOIN students ON attendance.id=students.id
        ORDER BY attendance.date DESC,attendance.time DESC
        LIMIT 1
        """
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result[0] if result else "None"


# ===============================
# ATTENDANCE RECORDS
# ===============================

def get_attendance_records():

    conn = _get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT students.name,attendance.date,attendance.time
        FROM attendance
        JOIN students ON attendance.id=students.id
        ORDER BY attendance.date DESC
        """
    )

    records = cursor.fetchall()

    cursor.close()
    conn.close()

    return records

import csv
import io

def export_attendance_csv():

    records = get_attendance_records()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(["Name", "Date", "Time"])

    for row in records:
        writer.writerow(row)

    return output.getvalue()
=======
import mysql.connector
from datetime import datetime

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "test@123456789",
    "database": "face_attendance"
}

def connect_db():
    return mysql.connector.connect(**DB_CONFIG)

def add_student(student_id, name):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT IGNORE INTO students (id, name) VALUES (%s, %s)",
        (student_id, name)
    )
    conn.commit()
    cursor.close()
    conn.close()

def mark_attendance(student_id):
    conn = connect_db()
    cursor = conn.cursor()

    today = datetime.now().date()
    time_now = datetime.now().time()

    cursor.execute(
        "INSERT IGNORE INTO attendance (id, date, time) VALUES (%s, %s, %s)",
        (student_id, today, time_now)
    )

    conn.commit()
    cursor.close()
    conn.close()

def get_student_name(student_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM students WHERE id = %s", (student_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else "Unknown"

def get_attendance_records():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT students.name, attendance.date, attendance.time
        FROM attendance
        JOIN students ON attendance.id = students.id
    """)
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    return records

def get_total_students():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM students")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count

def get_today_attendance():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = CURDATE()")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count

def get_last_attendance():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT students.name
        FROM attendance
        JOIN students ON attendance.id = students.id
        ORDER BY attendance.time DESC
        LIMIT 1
    """)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else "No records"
>>>>>>> 94f5c06e7a69eeceeaa7353e178e1f24186bf456
