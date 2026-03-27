import streamlit as st
import cv2
import cv2.data
import requests
from exercise import start_exercise_detection
from face_recognition import train_model
from attendance import mark_attendance
from gym_buddy import get_response, speak

# -------------------------------
# CONFIG
# -------------------------------
st.set_page_config(
    page_title="AI Gym Assistant",
    page_icon="🏋️",
    layout="wide"
)

# -------------------------------
# SESSION STATE
# -------------------------------
for key in ["chat_history", "buddy_chat", "buddy_open", "run_exercise"]:
    if key not in st.session_state:
        st.session_state[key] = [] if "chat" in key else False

# -------------------------------
# PREMIUM CSS (ULTIMATE UI)
# -------------------------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: white;
}

/* Chat bubbles */
.user {
    background: linear-gradient(135deg,#2563eb,#1d4ed8);
    padding:10px;
    border-radius:18px;
    margin:6px;
    text-align:right;
    max-width:75%;
    margin-left:auto;
}
.bot {
    background: rgba(31,41,55,0.9);
    padding:10px;
    border-radius:18px;
    margin:6px;
    max-width:75%;
}

/* Floating Buddy */
.buddy-box {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 320px;
    height: 420px;
    background: rgba(17, 24, 39, 0.85);
    backdrop-filter: blur(12px);
    border-radius: 15px;
    padding: 10px;
    overflow-y: auto;
    box-shadow: 0 0 25px rgba(34,197,94,0.6);
    z-index: 9999;
}

/* Header */
.title {
    text-align:center;
    font-size:42px;
}
.subtitle {
    text-align:center;
    color:gray;
}

/* Floating Button */
.float-btn {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 9999;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# HEADER
# -------------------------------
st.markdown('<div class="title">🏋️ AI Gym Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your AI Fitness Coach 💪</div>', unsafe_allow_html=True)
st.markdown("---")

# -------------------------------
# SIDEBAR
# -------------------------------
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

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 Start Workout"):
            st.session_state.run_exercise = True

    with col2:
        if st.button("🛑 Stop Workout"):
            st.session_state.run_exercise = False

    if st.session_state.run_exercise:
        st.info("🏃 Workout in progress...")
    else:
        st.warning("⚠️ Press Start Workout")

    frame_window = st.image([])

    col1, col2, col3 = st.columns(3)
    reps_placeholder = col1.empty()
    stage_placeholder = col2.empty()
    feedback_placeholder = col3.empty()

    if st.session_state.run_exercise and user_name:

        mark_attendance(user_name)

        start_exercise_detection(
            frame_window,
            exercise_type,
            reps_placeholder,
            stage_placeholder,
            feedback_placeholder,
            target_reps
        )

# -------------------------------
# CHATBOT MODE
# -------------------------------
elif mode == "ChatBot":

    st.subheader("🤖 AI Diet ChatBot")

    for chat in st.session_state.chat_history:
        cls = "user" if chat["role"] == "user" else "bot"
        st.markdown(f"<div class='{cls}'>{chat['message']}</div>", unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4,1])

        with col1:
            query = st.text_input("Type message...", label_visibility="collapsed")

        with col2:
            send = st.form_submit_button("➤")

    if send and query:
        st.session_state.chat_history.append({"role":"user","message":query})

        try:
            res = requests.get("http://127.0.0.1:8000/chat", params={"query": query})
            reply = res.json()["response"]
            st.session_state.chat_history.append({"role":"ai","message":reply})
        except:
            st.error("Chatbot server not running!")

        st.rerun()

# -------------------------------
# FACE MODE
# -------------------------------
elif mode == "Face Recognition":

    st.subheader("📸 Face Recognition Attendance")

    recognizer, label_map = train_model("known_faces")

    run = st.toggle("📷 Start Camera")
    frame_window = st.image([])

    cap = cv2.VideoCapture(0)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    while run:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray,1.3,5)

        for (x,y,w,h) in faces:
            face = cv2.resize(gray[y:y+h,x:x+w],(200,200))
            label, conf = recognizer.predict(face)

            name = label_map[label] if conf < 60 else "Unknown"

            if conf < 60:
                mark_attendance(name)

            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
            cv2.putText(frame,name,(x,y-10),cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),2)

        frame_window.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    cap.release()

# -------------------------------
# 🤖 JARVIS GYM BUDDY
# -------------------------------

col1, col2, col3 = st.columns([9,1,1])
with col3:
    if st.button("🤖"):
        st.session_state.buddy_open = not st.session_state.buddy_open

if st.session_state.buddy_open:

    st.markdown("<div class='buddy-box'>", unsafe_allow_html=True)

    st.markdown("### 🤖 Gym Buddy")

    if len(st.session_state.buddy_chat) == 0:
        st.session_state.buddy_chat.append(("bot","Hey champ 💪 Ready to train?"))

    for role,msg in st.session_state.buddy_chat:
        cls = "user" if role=="user" else "bot"
        st.markdown(f"<div class='{cls}'>{msg}</div>", unsafe_allow_html=True)

    with st.form("buddy_form", clear_on_submit=True):
        user_msg = st.text_input("Type...", label_visibility="collapsed")
        send = st.form_submit_button("Send")

    if send and user_msg:
        with st.spinner("🤖 Thinking..."):
            reply = get_response(user_msg)

        st.session_state.buddy_chat.append(("user", user_msg))
        st.session_state.buddy_chat.append(("bot", reply))

        speak(reply)
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)