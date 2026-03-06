import cv2
import os

def collect_faces(student_id):

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FACE_DIR = os.path.join(BASE_DIR, "data", "faces")
    CASCADE_PATH = os.path.join(BASE_DIR, "haarcascades", "haarcascade_frontalface_default.xml")

    os.makedirs(FACE_DIR, exist_ok=True)

    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    count = 0
    MAX_IMAGES = 150   # Increased from 100

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray, 1.2, 5)

        for (x, y, w, h) in faces:
            face_img = gray[y:y+h, x:x+w]

            # Improve contrast
            face_img = cv2.equalizeHist(face_img)

            # Resize for consistency
            face_img = cv2.resize(face_img, (200, 200))

            count += 1

            file_name = f"user.{student_id}.{count}.jpg"
            file_path = os.path.join(FACE_DIR, file_name)

            cv2.imwrite(file_path, face_img)

            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

        cv2.putText(frame, f"Images: {count}/150",
                    (20,40), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0,255,0), 2)

        cv2.imshow("Collecting Faces", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if count >= MAX_IMAGES:
            break

    cap.release()
    cv2.destroyAllWindows()