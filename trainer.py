
import cv2
import os
import numpy as np
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FACE_DIR = os.path.join(BASE_DIR, "data", "faces")
MODEL_PATH = os.path.join(BASE_DIR, "data", "trainer.yml")

FACE_SIZE = (200, 200)


def train_model():

    if not os.path.exists(FACE_DIR):
        logger.error("Face dataset not found")
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create(
        radius=1,
        neighbors=8,
        grid_x=8,
        grid_y=8
    )

    face_samples = []
    ids = []

    logger.info("Starting training...")

    for filename in os.listdir(FACE_DIR):

        if not filename.endswith(".jpg"):
            continue

        path = os.path.join(FACE_DIR, filename)

        img = Image.open(path).convert("L")
        img_numpy = np.array(img, "uint8")

        img_numpy = cv2.resize(img_numpy, FACE_SIZE)

        student_id = int(filename.split(".")[1])

        face_samples.append(img_numpy)
        ids.append(student_id)

    if len(face_samples) == 0:
        logger.error("No face images found for training")
        return

    recognizer.train(face_samples, np.array(ids))

    recognizer.write(MODEL_PATH)

    logger.info("Model training completed.")
    logger.info(f"Total images trained: {len(face_samples)}")

def train_model():

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FACE_DIR = os.path.join(BASE_DIR, "data", "faces")
    MODEL_PATH = os.path.join(BASE_DIR, "data", "trainer.yml")

    recognizer = cv2.face.LBPHFaceRecognizer_create(
        radius=1,
        neighbors=8,
        grid_x=8,
        grid_y=8
    )

    faces = []
    ids = []

    for file in os.listdir(FACE_DIR):
        if file.endswith(".jpg"):
            path = os.path.join(FACE_DIR, file)

            img = Image.open(path).convert("L")
            img_np = np.array(img, "uint8")

            id = int(file.split(".")[1])

            faces.append(img_np)
            ids.append(id)

    if len(faces) == 0:
        return

    recognizer.train(faces, np.array(ids))
    recognizer.save(MODEL_PATH)

    print("Model retrained successfully.")

