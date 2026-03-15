<<<<<<< HEAD
import cv2
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cascade_path = os.path.join(BASE_DIR, "haarcascades", "haarcascade_frontalface_default.xml")

face_cascade = cv2.CascadeClassifier(cascade_path)

if face_cascade.empty():
    print("❌ Cascade NOT loaded")
else:
=======
import cv2
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cascade_path = os.path.join(BASE_DIR, "haarcascades", "haarcascade_frontalface_default.xml")

face_cascade = cv2.CascadeClassifier(cascade_path)

if face_cascade.empty():
    print("❌ Cascade NOT loaded")
else:
>>>>>>> 94f5c06e7a69eeceeaa7353e178e1f24186bf456
    print("✅ Cascade loaded successfully")