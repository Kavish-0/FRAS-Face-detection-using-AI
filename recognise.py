import cv2
import os
import logging
from database import mark_attendance, get_student_name

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CASCADE_PATH = os.path.join(BASE_DIR, "haarcascades", "haarcascade_frontalface_default.xml")
MODEL_PATH = os.path.join(BASE_DIR, "data", "trainer.yml")

CONFIDENCE_THRESHOLD = 55
FACE_SIZE = (200, 200)

CAMERA_W = 1280
CAMERA_H = 720


def run_recognition():

    if not os.path.exists(MODEL_PATH):
        logger.error("Model file not found")
        return None

    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_PATH)

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        logger.error("Camera could not be opened")
        return None

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_H)

    attendance_marked = False
    confirmed_frames = 0
    detected_name = None

    while True:

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray, 1.2, 5)

        for (x, y, w, h) in faces:

            face_img = gray[y:y+h, x:x+w]
            face_img = cv2.equalizeHist(face_img)
            face_img = cv2.resize(face_img, FACE_SIZE)

            student_id, confidence = recognizer.predict(face_img)

            if confidence < CONFIDENCE_THRESHOLD:

                name = get_student_name(student_id)

                if detected_name == name:
                    confirmed_frames += 1
                else:
                    detected_name = name
                    confirmed_frames = 1

                if confirmed_frames >= 3 and not attendance_marked:
                    mark_attendance(student_id)
                    attendance_marked = True
                    cap.release()
                    cv2.destroyAllWindows()
                    return name

                label = name
                color = (0, 255, 0)

            else:
                confirmed_frames = 0
                detected_name = None
                label = "Unknown"
                color = (0, 0, 255)

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        cv2.imshow("Recognition", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    return None