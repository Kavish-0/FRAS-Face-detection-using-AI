import cv2
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
FACE_DIR     = os.path.join(BASE_DIR, "data", "faces")
CASCADE_PATH = os.path.join(BASE_DIR, "haarcascades", "haarcascade_frontalface_default.xml")

MAX_IMAGES   = 150
FACE_SIZE    = (200, 200)
CAMERA_W     = 1280
CAMERA_H     = 720
WARMUP_FRAMES = 10  # discard first N frames so camera adjusts to lighting


def collect_faces(student_id):
    """
    Opens camera index 0, captures MAX_IMAGES face samples silently
    (no cv2.imshow — compatible with Mac/Flask), saves them to data/faces/,
    then fully releases the camera.
    Must be called only when no other code is holding the camera.
    """

    os.makedirs(FACE_DIR, exist_ok=True)

    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        logger.error("Camera could not be opened during face collection")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAMERA_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_H)

    # Warm up — discard first N frames so camera adjusts to lighting
    for _ in range(WARMUP_FRAMES):
        cap.read()

    count = 0

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

                count += 1

                file_name = f"user.{student_id}.{count}.jpg"
                file_path = os.path.join(FACE_DIR, file_name)
                cv2.imwrite(file_path, face_img)

                logger.info(f"Captured image {count}/{MAX_IMAGES} for student {student_id}")

            if count >= MAX_IMAGES:
                break

    finally:
        cap.release()
        logger.info(f"Face collection done. {count} images saved for student {student_id}")