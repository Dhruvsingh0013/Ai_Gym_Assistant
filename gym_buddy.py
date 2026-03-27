import random
from textblob import TextBlob # type: ignore
import pyttsx3 # type: ignore

engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()
    
def coach_feedback(counter, target):

    # Speak every rep
    speak(f"{counter}")

    # Motivation
    if counter % 5 == 0:
        speak("Great job! Keep going 💪")

    # Stop when target reached
    if counter == target:
        speak("Workout complete! Well done 🎉")
        return "done"

    return "continue"

def analyze_emotion(text):
    polarity = TextBlob(text).sentiment.polarity

    if polarity > 0.2:
        return "positive"
    elif polarity < -0.2:
        return "negative"
    else:
        return "neutral"

def get_response(user_text):

    emotion = analyze_emotion(user_text)

    if emotion == "negative":
        msg = random.choice([
            "Don't worry, you are doing great 💪",
            "Stay strong, every step counts!",
            "You got this, keep pushing!"
        ])

    elif emotion == "positive":
        msg = random.choice([
            "Amazing energy! Keep it up 🔥",
            "You're doing fantastic!",
            "That’s the spirit 💯"
        ])

    else:
        msg = random.choice([
            "Keep going!",
            "Stay focused!",
            "Nice work!"
        ])

    speak(msg)  # 🔊 voice output
    return msg