import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe
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
    
    if not cap.isOpened():
        feedback_ui.error("Camera not found or blocked by another app!")
        return

    # Use try...finally to ENSURE the camera is released when Streamlit stops the script
    try:
        with mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0, # Use 0 for faster processing, 1 for better accuracy
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as pose:

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # Convert to RGB for Mediapipe
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = pose.process(image)

                # Convert back to BGR for OpenCV drawing
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                feedback = "Analyzing..."

                # Better practice: Check if landmarks exist instead of try/except
                if results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark

                    if exercise == "curl":
                        counter, stage, feedback = bicep_curl(landmarks, counter, stage)
                    elif exercise == "squat":
                        counter, stage, feedback = squat(landmarks, counter, stage)
                    elif exercise == "pushup":
                        counter, stage, feedback = pushup(landmarks, counter, stage)

                    # Draw landmarks on the body
                    mp_drawing.draw_landmarks(
                        image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                        mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
                    )

                # Update Streamlit UI components
                reps_ui.metric("Reps", f"{counter} / {target_reps}")
                stage_ui.metric("Stage", stage if stage else "-")
                feedback_ui.metric("Feedback", feedback)

                # Draw status on the actual camera frame
                cv2.rectangle(image, (0,0), (250, 120), (245, 117, 16), -1)
                cv2.putText(image, f'REPS: {counter}', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(image, f'STAGE: {stage}', (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                # Render to Streamlit
                frame_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                frame_window.image(frame_rgb)

                if counter >= target_reps:
                    feedback_ui.success("🎉 Target Completed!")
                    break
                
                # Necessary for OpenCV buffering
                cv2.waitKey(1)
                
    finally:
        cap.release()
