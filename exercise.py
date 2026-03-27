import cv2
import streamlit as st
import mediapipe as mp
import numpy as np
from gym_buddy import coach_feedback

# -------------------------------
# Initialize MediaPipe
# -------------------------------
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# -------------------------------
# Angle Calculation
# -------------------------------
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - \
              np.arctan2(a[1]-b[1], a[0]-b[0])

    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180:
        angle = 360 - angle

    return angle

# -------------------------------
# EXERCISE LOGIC
# -------------------------------

def bicep_curl(landmarks, counter, stage):
    shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
    elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
             landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
    wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
             landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

    angle = calculate_angle(shoulder, elbow, wrist)

    feedback = ""

    if angle > 160:
        stage = "down"
        feedback = "Lower your arm"

    if angle < 50 and stage == "down":
        stage = "up"
        counter += 1
        feedback = "Good rep!"

    return counter, stage, feedback


def squat(landmarks, counter, stage):
    hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
           landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
    knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
            landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
    ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
             landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

    angle = calculate_angle(hip, knee, ankle)

    feedback = ""

    if angle > 160:
        stage = "up"
        feedback = "Stand straight"

    if angle < 90 and stage == "up":
        stage = "down"
        counter += 1
        feedback = "Nice squat!"

    return counter, stage, feedback


def pushup(landmarks, counter, stage):
    shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
    elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
             landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
    wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
             landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

    angle = calculate_angle(shoulder, elbow, wrist)

    feedback = ""

    if angle > 160:
        stage = "up"
        feedback = "Go down"

    if angle < 90 and stage == "up":
        stage = "down"
        counter += 1
        feedback = "Good push-up!"

    return counter, stage, feedback


# -------------------------------
# MAIN FUNCTION
# -------------------------------
def start_exercise_detection(frame_window, exercise, reps_ui, stage_ui, feedback_ui, target_reps):

    counter = 0
    stage = None

    cap = cv2.VideoCapture(0)

    with mp_pose.Pose(min_detection_confidence=0.5,
                      min_tracking_confidence=0.5) as pose:

        while cap.isOpened() and st.session_state.get("run_exercise", False):

            ret, frame = cap.read()
            if not ret:
                break

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            feedback = ""

            try:
                landmarks = results.pose_landmarks.landmark

                # Exercise selection
                if exercise == "curl":
                    counter, stage, feedback = bicep_curl(landmarks, counter, stage)

                elif exercise == "squat":
                    counter, stage, feedback = squat(landmarks, counter, stage)

                elif exercise == "pushup":
                    counter, stage, feedback = pushup(landmarks, counter, stage)

                else:
                    feedback = "Invalid Exercise"

                # -------------------------------
                # UI UPDATE
                # -------------------------------
                reps_ui.metric("Reps", counter)
                stage_ui.metric("Stage", stage if stage else "-")
                feedback_ui.metric("Feedback", feedback)

                # -------------------------------
                # 🤖 GYM BUDDY COACH
                # -------------------------------
                status = coach_feedback(counter, target_reps)

                if status == "done":
                    st.success("🎉 Target Completed!")
                    cap.release()
                    break

                # Draw text on frame
                cv2.putText(image, f'Reps: {counter}', (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                cv2.putText(image, f'Stage: {stage}', (10, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                cv2.putText(image, f'{feedback}', (10, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            except:
                pass

            # Draw landmarks
            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # Show in Streamlit
            frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            frame_window.image(frame)

        cap.release()
