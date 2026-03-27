from fastapi import FastAPI # type: ignore
from chatbot import chat   # import simple chat function

app = FastAPI()

# Root check (optional but useful)
@app.get("/")
def home():
    return {"message": "Chatbot API is running 🚀"}

# Chat endpoint
@app.get("/chat")
def chat_api(query: str):
    try:
        response = chat(query)
        return response
    except Exception as e:
        return {"response": f"Error: {str(e)}"}