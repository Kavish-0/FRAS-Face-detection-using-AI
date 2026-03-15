import cv2
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cascade_path = os.path.join(BASE_DIR, "haarcascades", "haarcascade_frontalface_default.xml")

face_cascade = cv2.CascadeClassifier(cascade_path)

if face_cascade.empty():
    print("❌ Cascade NOT loaded")
else:
    print("✅ Cascade loaded successfully")