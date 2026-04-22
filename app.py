import streamlit as st
import cv2
import requests
import sys
import subprocess
from exercise import start_exercise_detection

# IMPORTANT: Ensure these custom modules exist in your directory, 
# otherwise comment them out to test the camera first.
try:
    from face_recognition import train_model
    from attendance import mark_attendance
    from gym_buddy import get_response, speak
except ImportError as e:
    st.warning(f"Missing custom module: {e}. Some features may not work.")

def launch_jarvis():
    try:
        subprocess.Popen([sys.executable, "jarvis.py"])
    except Exception as e:
        st.error(f"Jarvis error: {e}")

# -------------------------------
# CONFIG & SESSION STATE
# -------------------------------
st.set_page_config(page_title="AI Gym Assistant", page_icon="🏋️", layout="wide")

for key in ["chat_history", "buddy_chat", "buddy_open", "run_exercise"]:
    if key not in st.session_state:
        st.session_state[key] = [] if "chat" in key else False

# -------------------------------
# CSS
# -------------------------------
st.markdown("""
<style>
body { background-color: #0e1117; color: white; }
.user { background: linear-gradient(135deg,#2563eb,#1d4ed8); padding:10px; border-radius:18px; margin:6px; text-align:right; max-width:75%; margin-left:auto; }
.bot { background: rgba(31,41,55,0.9); padding:10px; border-radius:18px; margin:6px; max-width:75%; }
.title { text-align:center; font-size:42px; font-weight: bold;}
.subtitle { text-align:center; color:gray; }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# HEADER & SIDEBAR
# -------------------------------
st.markdown('<div class="title">🏋️ AI Gym Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your AI Fitness Coach 💪</div>', unsafe_allow_html=True)
st.markdown("---")

st.sidebar.title("⚙️ Settings")
mode = st.sidebar.radio("Choose Mode", ["Exercise Mode", "Face Recognition", "ChatBot"])

# -------------------------------
# EXERCISE MODE
# -------------------------------
if mode == "Exercise Mode":
    st.subheader("💪 Start Workout")

    col1, col2 = st.columns(2)
    with col1:
        user_name = st.text_input("Enter Your Name")
    with col2:
        exercise_type = st.selectbox("Choose Exercise", ["curl", "squat", "pushup"])

    target_reps = st.number_input("🎯 Target Reps", 5, 50, 10)

    # Control logic
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("🚀 Start Workout"):
            if not user_name:
                st.warning("⚠️ Please enter your name first!")
            else:
                st.session_state.run_exercise = True
                st.rerun()

    with btn_col2:
        if st.button("🛑 Stop Workout"):
            st.session_state.run_exercise = False
            st.rerun()

    if st.session_state.run_exercise:
        st.info("🏃 Workout in progress... Click 'Stop Workout' to end.")
        
        # Placeholders for UI updates
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        reps_placeholder = metric_col1.empty()
        stage_placeholder = metric_col2.empty()
        feedback_placeholder = metric_col3.empty()
        
        frame_window = st.empty() # Better to use st.empty() for videos

        try:
            # mark_attendance(user_name) # Uncomment if attendance.py is active
            start_exercise_detection(
                frame_window,
                exercise_type,
                reps_placeholder,
                stage_placeholder,
                feedback_placeholder,
                target_reps
            )
            # Once target is complete or loop breaks, turn off state
            st.session_state.run_exercise = False
        except Exception as e:
            st.error(f"Error during exercise: {e}")


