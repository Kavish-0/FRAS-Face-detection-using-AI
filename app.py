import cv2
from datetime import datetime, date
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    Response,
    flash
)

from recognise import run_recognition
from collect_face import collect_faces
from trainer import train_model

from database import (
    add_student,
    update_student,
    delete_student,
    get_all_students,
    get_attendance_records,
    get_total_students,
    get_today_attendance,
    get_last_attendance,
    get_weekly_attendance,
    get_monthly_attendance,
    get_attendance_rate,
    reset_today_attendance,
    export_csv,
    mark_attendance,
    get_student_name,
    remove_today_attendance,
    remove_attendance_by_record,
    get_today_present_ids,
    add_past_attendance,
    edit_attendance,
)

app = Flask(__name__)
app.secret_key = "fras_secret"


# ── Camera preview ────────────────────────────────────────────────────

camera = None


def generate_frames():
    global camera
    camera = cv2.VideoCapture(0)
    try:
        while True:
            success, frame = camera.read()
            if not success:
                break
            frame = cv2.flip(frame, 1)
            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                continue
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )
    finally:
        camera.release()
        camera = None


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ── Auth ──────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "admin123":
            session["admin"] = True
            return redirect(url_for("home"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Dashboard ─────────────────────────────────────────────────────────

@app.route("/")
def home():
    if "admin" not in session:
        return redirect(url_for("login"))

    week_labels,  week_data  = get_weekly_attendance()
    month_labels, month_data = get_monthly_attendance()
    attendance_rate          = get_attendance_rate()

    return render_template(
        "index.html",
        total_students=get_total_students(),
        today_attendance=get_today_attendance(),
        last_student=get_last_attendance(),
        week_labels=week_labels,
        week_data=week_data,
        month_labels=month_labels,
        month_data=month_data,
        attendance_rate=attendance_rate,
    )


# ── Recognition ───────────────────────────────────────────────────────

@app.route("/recognition")
def recognition():
    if "admin" not in session:
        return redirect(url_for("login"))
    return render_template("recognition.html")


@app.route("/start_recognition")
def start_recognition():
    if "admin" not in session:
        return redirect(url_for("login"))

    global camera

    if camera and camera.isOpened():
        camera.release()
        camera = None

    name, status = run_recognition()

    if status == 'marked':
        flash(f"✅ Welcome, {name}! Attendance marked.", "success")
    elif status == 'already':
        flash(f"ℹ️ {name}, your attendance was already marked today.", "info")
    elif status == 'unknown':
        flash("⚠️ Face detected but not recognized. Please try again.", "warning")
    elif status == 'no_face':
        flash("❌ No face detected within 15 seconds. Please try again.", "danger")
    elif status == 'no_model':
        flash("❌ No trained model found. Please register students first.", "danger")

    return redirect(url_for("attendance"))


# ── Manual reset ──────────────────────────────────────────────────────

@app.route("/reset_attendance")
def reset_attendance():
    if "admin" not in session:
        return redirect(url_for("login"))
    reset_today_attendance()
    return redirect(url_for("home"))


# ── Register student ──────────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if "admin" not in session:
        return redirect(url_for("login"))

    error = None

    if request.method == "POST":
        student_id = request.form["student_id"]
        name       = request.form["name"]

        success = add_student(student_id, name)
        if not success:
            error = f"Student ID {student_id} already exists. Please use a different ID."
            return render_template("register.html", error=error)

        global camera

        if camera and camera.isOpened():
            camera.release()
            camera = None

        collect_faces(student_id)
        train_model()

        flash(f"✅ Student '{name}' registered successfully.", "success")
        return redirect(url_for("students"))

    return render_template("register.html", error=error)


# ── Attendance ────────────────────────────────────────────────────────

@app.route("/attendance")
def attendance():
    if "admin" not in session:
        return redirect(url_for("login"))

    name      = request.args.get("name")
    date_filter = request.args.get("date")
    records   = get_attendance_records(name, date_filter)
    students  = get_all_students()
    today_ids = get_today_present_ids()
    today_present = len(today_ids)
    today_date = date.today().isoformat()   # for max= on past date picker

    return render_template(
        "attendance.html",
        records=records,
        students=students,
        today_ids=today_ids,
        today_present=today_present,
        today_date=today_date,
    )


@app.route("/manual_attendance", methods=["POST"])
def manual_attendance():
    if "admin" not in session:
        return redirect(url_for("login"))

    student_id = request.form.get("student_id")
    if student_id:
        name   = get_student_name(student_id)
        status = mark_attendance(student_id)
        if status == "already":
            flash(f"⚠️ Attendance already marked for {name} today.", "warning")
        else:
            flash(f"✅ Attendance marked manually for {name}.", "success")

    return redirect(url_for("attendance"))


@app.route("/remove_attendance", methods=["POST"])
def remove_attendance():
    if "admin" not in session:
        return redirect(url_for("login"))

    student_id = request.form.get("student_id")
    if student_id:
        name = get_student_name(student_id)
        remove_today_attendance(student_id)
        flash(f"🗑️ Today's attendance removed for {name}.", "warning")

    return redirect(url_for("attendance"))


@app.route("/remove_attendance_by_record", methods=["POST"])
def remove_attendance_by_record_route():
    if "admin" not in session:
        return redirect(url_for("login"))

    student_name = request.form.get("student_name")
    record_date  = request.form.get("date")
    if student_name and record_date:
        remove_attendance_by_record(student_name, record_date)
        flash(f"🗑️ Attendance record removed for {student_name} on {record_date}.", "warning")

    return redirect(url_for("attendance") + "?tab=records")


@app.route("/add_past_attendance", methods=["POST"])
def add_past_attendance_route():
    if "admin" not in session:
        return redirect(url_for("login"))

    student_id = request.form.get("student_id")
    past_date  = request.form.get("date")
    past_time  = request.form.get("time") or "09:00:00"

    # Ensure time has seconds
    if len(past_time) == 5:
        past_time += ":00"

    if student_id and past_date:
        name   = get_student_name(student_id)
        status = add_past_attendance(student_id, past_date, past_time)
        if status == "already":
            flash(f"⚠️ Attendance already exists for {name} on {past_date}.", "warning")
        else:
            flash(f"✅ Past attendance added for {name} on {past_date}.", "success")

    return redirect(url_for("attendance") + "?tab=addpast")


@app.route("/edit_attendance", methods=["POST"])
def edit_attendance_route():
    if "admin" not in session:
        return redirect(url_for("login"))

    original_name = request.form.get("original_name")
    original_date = request.form.get("original_date")
    new_name      = request.form.get("student_name")
    new_date      = request.form.get("date")
    new_time      = request.form.get("time") or "09:00:00"

    if len(new_time) == 5:
        new_time += ":00"

    if all([original_name, original_date, new_name, new_date]):
        success = edit_attendance(original_name, original_date, new_name, new_date, new_time)
        if success:
            flash(f"✅ Attendance record updated for {new_name} on {new_date}.", "success")
        else:
            flash("⚠️ Could not update record — a record for that student/date may already exist.", "warning")

    return redirect(url_for("attendance") + "?tab=records")


# ── Export ────────────────────────────────────────────────────────────

@app.route("/export")
def export():
    csv_data = export_csv()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance.csv"}
    )


# ── Students ──────────────────────────────────────────────────────────

@app.route("/students")
def students():
    if "admin" not in session:
        return redirect(url_for("login"))
    return render_template("students.html", students=get_all_students())


@app.route("/edit_student/<student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        update_student(student_id, name)
        return redirect(url_for("students"))

    return render_template("edit_student.html", student_id=student_id)


@app.route("/delete_student/<student_id>")
def delete_student_route(student_id):
    if "admin" not in session:
        return redirect(url_for("login"))
    delete_student(student_id)
    return redirect(url_for("students"))


# ── Run ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)