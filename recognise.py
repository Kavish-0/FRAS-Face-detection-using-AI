import cv2
import os
import logging
from database import mark_attendance, get_student_name

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CASCADE_PATH = os.path.join(BASE_DIR, "haarcascades", "haarcascade_frontalface_default.xml")
MODEL_PATH = os.path.join(BASE_DIR, "data", "trainer.yml")

CONFIDENCE_THRESHOLD = 60
FACE_SIZE = (200, 200)

CAMERA_W = 1280
CAMERA_H = 720


def run_recognition() -> str | None:

    if not os.path.exists(MODEL_PATH):
        logger.error("Model file not found. Train the model first.")
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

    logger.info("Starting face recognition...")

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

            logger.info(f"Prediction ID={student_id} Confidence={confidence}")

            if confidence < CONFIDENCE_THRESHOLD:

                name = get_student_name(student_id)

                mark_attendance(student_id)

                cap.release()
                cv2.destroyAllWindows()

                logger.info(f"Attendance marked for {name}")

                return name

            else:

                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,0,255), 2)
                cv2.putText(
                    frame,
                    "Unknown",
                    (x,y-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0,0,255),
                    2
                )

        cv2.imshow("Face Recognition", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    return None