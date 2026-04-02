import os
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv
import csv
import io

# Load variables from .env file
load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "face_attendance"),
}


def connect_db():
    return mysql.connector.connect(**DB_CONFIG)


def add_student(student_id, name):
    """Returns True on success, False if student ID already exists."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO students (id, name) VALUES (%s,%s)", (student_id, name))
        conn.commit()
        return True
    except mysql.connector.errors.IntegrityError:
        return False
    finally:
        cursor.close()
        conn.close()


def update_student(student_id, name):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET name=%s WHERE id=%s", (name, student_id))
    conn.commit()
    cursor.close()
    conn.close()


def delete_student(student_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendance WHERE id=%s", (student_id,))
    cursor.execute("DELETE FROM students WHERE id=%s", (student_id,))
    conn.commit()
    cursor.close()
    conn.close()


def get_all_students():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return students


def get_student_name(student_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM students WHERE id=%s", (student_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else "Unknown"


def mark_attendance(student_id):
    """Returns 'marked' on success, 'already' if attendance already exists for today."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO attendance (id, date, time) VALUES (%s, CURDATE(), NOW())",
            (student_id,)
        )
        conn.commit()
        return "marked"
    except mysql.connector.errors.IntegrityError as e:
        if e.errno == 1062:
            return "already"
        raise
    finally:
        cursor.close()
        conn.close()


def add_past_attendance(student_id, date, time):
    """
    Insert an attendance record for a past date.
    Returns 'marked' on success, 'already' if a record already exists for that date.
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO attendance (id, date, time) VALUES (%s, %s, %s)",
            (student_id, date, time)
        )
        conn.commit()
        return "marked"
    except mysql.connector.errors.IntegrityError as e:
        if e.errno == 1062:
            return "already"
        raise
    finally:
        cursor.close()
        conn.close()


def edit_attendance(original_name, original_date, new_name, new_date, new_time):
    """Edit an existing attendance record — can change student, date, and time."""
    conn = connect_db()
    cursor = conn.cursor()
    # Get student id from new_name
    cursor.execute("SELECT id FROM students WHERE name=%s", (new_name,))
    result = cursor.fetchone()
    if not result:
        cursor.close()
        conn.close()
        return False
    new_id = result[0]
    # Get original student id
    cursor.execute("SELECT id FROM students WHERE name=%s", (original_name,))
    orig = cursor.fetchone()
    if not orig:
        cursor.close()
        conn.close()
        return False
    original_id = orig[0]
    try:
        cursor.execute("""
            UPDATE attendance
            SET id=%s, date=%s, time=%s
            WHERE id=%s AND date=%s
        """, (new_id, new_date, new_time, original_id, original_date))
        conn.commit()
        return True
    except mysql.connector.errors.IntegrityError:
        return False
    finally:
        cursor.close()
        conn.close()


def remove_today_attendance(student_id):
    """Remove today's attendance for a specific student."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM attendance WHERE id=%s AND date=CURDATE()",
        (student_id,)
    )
    conn.commit()
    cursor.close()
    conn.close()


def remove_attendance_by_record(student_name, date):
    """Remove a specific attendance record by student name and date."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE attendance FROM attendance
        JOIN students ON attendance.id = students.id
        WHERE students.name = %s AND attendance.date = %s
        LIMIT 1
    """, (student_name, date))
    conn.commit()
    cursor.close()
    conn.close()


def get_today_present_ids():
    """Return a set of student IDs who have attendance marked today."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM attendance WHERE date = CURDATE()")
    ids = {row[0] for row in cursor.fetchall()}
    cursor.close()
    conn.close()
    return ids


def reset_today_attendance():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendance WHERE date = CURDATE()")
    conn.commit()
    cursor.close()
    conn.close()


def get_attendance_records(name=None, date=None):
    conn = connect_db()
    cursor = conn.cursor()
    query = """
        SELECT students.name, attendance.date, attendance.time
        FROM attendance
        JOIN students ON attendance.id = students.id
    """
    conditions, values = [], []
    if name:
        conditions.append("students.name = %s")
        values.append(name)
    if date:
        conditions.append("attendance.date = %s")
        values.append(date)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY attendance.date DESC, attendance.time DESC"
    cursor.execute(query, values)
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
    cursor.execute("SELECT COUNT(DISTINCT id) FROM attendance WHERE date = CURDATE()")
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
        ORDER BY attendance.date DESC, attendance.time DESC
        LIMIT 1
    """)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else "None"


def get_weekly_attendance():
    conn = connect_db()
    cursor = conn.cursor()
    labels, data = [], []
    today = datetime.now().date()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        cursor.execute("SELECT COUNT(DISTINCT id) FROM attendance WHERE date = %s", (day,))
        labels.append(day.strftime("%a %d"))
        data.append(cursor.fetchone()[0])
    cursor.close()
    conn.close()
    return labels, data


def get_monthly_attendance():
    conn = connect_db()
    cursor = conn.cursor()
    labels, data = [], []
    today = datetime.now().date()
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        cursor.execute("SELECT COUNT(DISTINCT id) FROM attendance WHERE date = %s", (day,))
        labels.append(day.strftime("%d %b"))
        data.append(cursor.fetchone()[0])
    cursor.close()
    conn.close()
    return labels, data


def get_attendance_rate():
    conn = connect_db()
    cursor = conn.cursor()
    today = datetime.now().date()
    first_of_month = today.replace(day=1)
    days_elapsed = (today - first_of_month).days + 1
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]
    if total_students == 0:
        cursor.close()
        conn.close()
        return 0
    possible = total_students * days_elapsed
    cursor.execute(
        "SELECT COUNT(DISTINCT id, date) FROM attendance WHERE date >= %s AND date <= %s",
        (first_of_month, today)
    )
    actual = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return min(round((actual / possible) * 100, 1), 100)


def export_csv():
    records = get_attendance_records()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Date", "Time"])
    for row in records:
        writer.writerow(row)
    return output.getvalue()