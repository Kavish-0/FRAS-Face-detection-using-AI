import cv2
import os
from database import mark_attendance, get_student_name

def run_recognition():

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    cascade_path = os.path.join(BASE_DIR, "haarcascades", "haarcascade_frontalface_default.xml")
    model_path = os.path.join(BASE_DIR, "data", "trainer.yml")

    face_cascade = cv2.CascadeClassifier(cascade_path)

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(model_path)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    attendance_marked = False
    confirmed_frames = 0
    detected_name = None

    CONFIDENCE_THRESHOLD = 55   # Stricter (was 70)

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
            face_img = cv2.resize(face_img, (200, 200))

            id, confidence = recognizer.predict(face_img)

            # Debug print (optional remove later)
            print("ID:", id, "Confidence:", confidence)

            if confidence < CONFIDENCE_THRESHOLD:

                name = get_student_name(id)

                if detected_name == name:
                    confirmed_frames += 1
                else:
                    detected_name = name
                    confirmed_frames = 1

                if confirmed_frames >= 3 and not attendance_marked:
                    mark_attendance(id)
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

            cv2.rectangle(frame, (x,y), (x+w,y+h), color, 2)
            cv2.putText(frame, label, (x,y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        cv2.imshow("Recognition", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None