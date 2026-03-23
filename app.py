import threading
import cv2
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    Response
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
    export_csv
)

app = Flask(__name__)
app.secret_key = "fras_secret"

# ── Recognition state ─────────────────────────────────────────────────
recognition_state = {
    "running": False,
    "result": None
}


# ── Camera: re-open if needed so the feed works after recognition ─────
def get_camera():
    cap = cv2.VideoCapture(0)
    return cap


def generate_frames():
    cap = get_camera()
    while True:
        success, frame = cap.read()
        if not success:
            # Try to reopen if camera dropped
            cap.release()
            cap = get_camera()
            continue
        ret, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame +
            b"\r\n"
        )


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

    week_labels, week_data   = get_weekly_attendance()
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
    """
    Runs face recognition in a background thread.
    Can be triggered multiple times — each call spawns a fresh thread
    as long as the previous one has finished.
    """
    if "admin" not in session:
        return redirect(url_for("login"))

    if not recognition_state["running"]:
        recognition_state["running"] = True
        recognition_state["result"] = None

        def _run():
            result = run_recognition()
            recognition_state["result"] = result
            recognition_state["running"] = False

        t = threading.Thread(target=_run, daemon=True)
        t.start()

    return redirect(url_for("attendance"))


# ── Reset today's attendance ──────────────────────────────────────────

@app.route("/reset_attendance")
def reset_attendance():
    if "admin" not in session:
        return redirect(url_for("login"))
    reset_today_attendance()
    return redirect(url_for("home"))


# ── Register ──────────────────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        student_id = request.form["student_id"]
        name = request.form["name"]
        add_student(student_id, name)
        collect_faces(student_id)
        train_model()
        return redirect(url_for("students"))

    return render_template("register.html")


# ── Attendance ────────────────────────────────────────────────────────

@app.route("/attendance")
def attendance():
    if "admin" not in session:
        return redirect(url_for("login"))

    name = request.args.get("name")
    date = request.args.get("date")
    records = get_attendance_records(name, date)
    return render_template("attendance.html", records=records)


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
    app.run(debug=True)
