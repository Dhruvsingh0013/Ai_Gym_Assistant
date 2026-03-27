import cv2
import cv2.data
import cv2.face
import os
import numpy as np

def train_model(known_faces):

    faces = []
    labels = []
    label_map = {}
    label_id = 0

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    for person in os.listdir(known_faces):

        person_path = os.path.join(known_faces, person)
        if not os.path.isdir(person_path):
            continue

        for img_name in os.listdir(person_path):

            img_path = os.path.join(person_path, img_name)
            img = cv2.imread(img_path)
        

            if img is None:
                continue

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            faces_detected = face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x,y,w,h) in faces_detected:
                face = gray[y:y+h, x:x+w]
                face = cv2.resize(face, (200,200))

                faces.append(face)
                labels.append(label_id)

        label_map[label_id] = person
        label_id += 1

    recognizer = cv2.face.LBPHFaceRecognizer_create()  # type: ignore
    recognizer.train(faces, np.array(labels))

    return recognizer, label_map