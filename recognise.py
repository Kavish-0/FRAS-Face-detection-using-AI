import cv2
import os
import time
from database import mark_attendance, get_student_name, get_attendance_records
from datetime import date

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
CASCADE_PATH = os.path.join(BASE_DIR, "haarcascades", "haarcascade_frontalface_default.xml")
MODEL_PATH   = os.path.join(BASE_DIR, "data", "trainer.yml")

CONFIDENCE_THRESHOLD = 70
FACE_SIZE = (200, 200)
CAMERA_W  = 1280
CAMERA_H  = 720
WARMUP_FRAMES = 10   # discard first N frames so camera adjusts to lighting


def already_marked_today(student_id):
    """Returns True if student already has attendance marked for today."""
    today = date.today().strftime("%Y-%m-%d")
    records = get_attendance_records(date=today)
    for record in records:
        # record = (name, date, time) — we need to match by name
        # get the name for this student_id
        name = get_student_name(student_id)
        if record[0] == name:
            return True
    return False


def run_recognition():
    """
    Opens a fresh camera, runs silent recognition (no cv2.imshow on Mac),
    marks attendance once per day if a student is found,
    then fully releases the camera.
    Returns (name, status) tuple:
      - (name, 'marked')   — attendance marked successfully
      - (name, 'already')  — already marked today
      - (None, 'unknown')  — face detected but not recognized
      - (None, 'no_face')  — no face detected within timeout
      - (None, 'no_model') — model file missing
    """

    if not os.path.exists(MODEL_PATH):
        return None, 'no_model'

    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    recognizer   = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_PATH)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAMERA_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_H)

    # Warm up — discard first N frames so camera adjusts to lighting
    for _ in range(WARMUP_FRAMES):
        cap.read()

    start_time   = time.time()
    timeout      = 15
    result_name  = None
    result_status = 'no_face'

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.2, 5)

            for (x, y, w, h) in faces:
                face_img = gray[y:y+h, x:x+w]
                face_img = cv2.equalizeHist(face_img)
                face_img = cv2.resize(face_img, FACE_SIZE)

                student_id, confidence = recognizer.predict(face_img)

                if confidence < CONFIDENCE_THRESHOLD:
                    name = get_student_name(student_id)

                    if already_marked_today(student_id):
                        result_name   = name
                        result_status = 'already'
                    else:
                        mark_attendance(student_id)
                        result_name   = name
                        result_status = 'marked'

                    return result_name, result_status  # done — exit immediately

                else:
                    result_status = 'unknown'

            if time.time() - start_time > timeout:
                break

    finally:
        cap.release()

    return result_name, result_status