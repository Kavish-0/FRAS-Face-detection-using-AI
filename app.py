from flask import Flask, render_template, redirect, url_for, request
from recognise import run_recognition
from collect_face import collect_faces
from trainer import train_model
from database import (
    add_student,
    get_attendance_records,
    get_total_students,
    get_today_attendance,
    get_last_attendance
)

app = Flask(__name__)


# ===============================
# DASHBOARD HOME
# ===============================
@app.route("/")
def home():
    return render_template(
        "index.html",
        total_students=get_total_students(),
        today_attendance=get_today_attendance(),
        last_student=get_last_attendance(),
        success=None
    )


# ===============================
# START ATTENDANCE
# ===============================
@app.route("/start")
def start():

    name = run_recognition()

    return render_template(
        "index.html",
        success=name if name else None,
        total_students=get_total_students(),
        today_attendance=get_today_attendance(),
        last_student=get_last_attendance()
    )


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        student_id = request.form["student_id"]
        name = request.form["name"]

        add_student(student_id, name)
        collect_faces(student_id)
        train_model()

        return redirect(url_for("home"))

    return render_template("register.html")


# ===============================
# VIEW ATTENDANCE
# ===============================
@app.route("/attendance")
def attendance():
    records = get_attendance_records()
    return render_template("attendance.html", records=records)



if __name__ == "__main__":
    app.run(debug=True)