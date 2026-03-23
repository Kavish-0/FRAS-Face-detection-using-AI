import cv2
import os
import time
from database import mark_attendance, get_student_name

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
CASCADE_PATH = os.path.join(BASE_DIR, "haarcascades", "haarcascade_frontalface_default.xml")
MODEL_PATH   = os.path.join(BASE_DIR, "data", "trainer.yml")

CONFIDENCE_THRESHOLD = 70
FACE_SIZE = (200, 200)
CAMERA_W  = 1280
CAMERA_H  = 720


def run_recognition():
    """
    Opens a fresh camera, runs recognition for up to 15 seconds,
    marks attendance if a student is found, then fully releases
    the camera so it can be reused next time.
    """

    if not os.path.exists(MODEL_PATH):
        return None

    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    recognizer   = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_PATH)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAMERA_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_H)

    start_time = time.time()
    timeout    = 15
    result     = None

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

                    # Always insert — allows multiple markings per day
                    mark_attendance(student_id)

                    label = f"{name} ({round(100 - confidence, 2)}%)"
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    cv2.imshow("Recognition", frame)
                    cv2.waitKey(1500)

                    result = name
                    break   # attendance marked — exit face loop

                else:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    cv2.putText(frame, "Unknown", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

            cv2.imshow("Recognition", frame)

            if result:
                break

            if time.time() - start_time > timeout:
                break

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        # Always release — allows camera restart next time
        cap.release()
        cv2.destroyAllWindows()

    return result
