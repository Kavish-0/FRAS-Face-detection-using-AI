import cv2
import os
import numpy as np
from PIL import Image

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