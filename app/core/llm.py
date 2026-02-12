from langchain_google_genai import ChatGoogleGenerativeAI
from config import GEMINI_API_KEY

def get_llm():
    return ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0,
    google_api_key=GEMINI_API_KEY
)