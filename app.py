import threading
import os
import glob
import cv2

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    jsonify,
    Response
)

from recognise import run_recognition
from collect_face import collect_faces
from trainer import train_model

from database import (
    add_student,
    delete_student,
    get_all_students,
    get_attendance_records,
    get_total_students,
    get_today_attendance,
    get_last_attendance,
    export_attendance_csv
)

app = Flask(__name__)

camera = cv2.VideoCapture(0)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break

        ret, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" +
               frame + b"\r\n")


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


lock = threading.Lock()

recognition_state = {
    "running": False,
    "result": None
}


@app.route("/")
def home():
    return render_template(
        "index.html",
        total_students=get_total_students(),
        today_attendance=get_today_attendance(),
        last_student=get_last_attendance()
    )


@app.route("/recognition")
def recognition():
    return render_template("recognition.html")


@app.route("/start", methods=["POST"])
def start():

    with lock:

        if recognition_state["running"]:
            return jsonify({"status": "already_running"})

        recognition_state["running"] = True
        recognition_state["result"] = None

    def run():

        name = run_recognition()

        recognition_state["result"] = name if name else "failed"
        recognition_state["running"] = False

    threading.Thread(target=run, daemon=True).start()

    return jsonify({"status": "started"})


@app.route("/start/status")
def start_status():
    return jsonify(recognition_state)


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


@app.route("/students")
def students():

    students = get_all_students()

    return render_template(
        "students.html",
        students=students
    )


@app.route("/delete/<student_id>")
def delete(student_id):

    delete_student(student_id)

    FACE_DIR = os.path.join("data", "faces")

    images = glob.glob(
        f"{FACE_DIR}/user.{student_id}.*.jpg"
    )

    for img in images:
        os.remove(img)

    train_model()

    return redirect(url_for("students"))


@app.route("/attendance")
def attendance():

    records = get_attendance_records()

    return render_template(
        "attendance.html",
        records=records
    )


@app.route("/export")
def export():

    csv_data = export_attendance_csv()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=attendance.csv"
        }
    )


@app.route("/logout")
def logout():
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)