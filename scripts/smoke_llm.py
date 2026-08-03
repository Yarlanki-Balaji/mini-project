"""Proves both LLM providers work with the keys in backend/.env. Run manually."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.config import get_settings  # noqa: E402

s = get_settings()

from langchain_google_genai import ChatGoogleGenerativeAI  # noqa: E402
from langchain_groq import ChatGroq  # noqa: E402

gemini = ChatGoogleGenerativeAI(model="gemini-flash-latest", google_api_key=s.gemini_api_key)
print("GEMINI:", gemini.invoke("Say OK").content[:40])

groq = ChatGroq(model="llama-3.3-70b-versatile", api_key=s.groq_api_key)
print("GROQ:", groq.invoke("Say OK").content[:40])
