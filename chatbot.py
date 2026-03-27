import os
from langchain_google_genai import ChatGoogleGenerativeAI # type: ignore
from gym_buddy import get_response

# -------------------------------
# SET API KEY (use environment variable)
# -------------------------------
os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY"

# -------------------------------
# LOAD MODEL
# -------------------------------
llm = ChatGoogleGenerativeAI(
    model="models/gemini-flash-latest",
    temperature=0.7
)

# -------------------------------
# FITNESS FILTER
# -------------------------------
def is_fitness_query(query):
    keywords = [
        "diet","hello", "exercise", "gym", "workout", "fitness",
        "weight", "fat", "muscle", "protein", "calories",
        "nutrition", "health", "biceps", "abs", "training"
    ]
    
    return any(word in query.lower() for word in keywords)

# -------------------------------
# MAIN CHAT FUNCTION
# -------------------------------
def chat(query):

    if not is_fitness_query(query):
        return {
            "response": "⚠️ I am your AI Fitness Assistant. Ask about gym, diet, or workouts."
        }

    try:
        # AI response
        response = llm.invoke(query)
        answer = response.content[0]["text"]

        # Gym buddy message
        buddy_msg = get_response(query)

        final_response = f"{answer}\n\n🤖 Gym Buddy: {buddy_msg}"

        return {"response": final_response}

    except Exception as e:
        return {"response": f"❌ Error: {str(e)}"}