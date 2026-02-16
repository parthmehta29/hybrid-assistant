import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    # Using 'gemini-1.5-flash' as it is the current cost-efficient, fast model
    GEMINI_MODEL = "gemini-1.5-flash"
    EMBEDDING_MODEL = "models/text-embedding-004"
    CHROMA_PERSIST_DIR = "./data/chroma_db"

settings = Settings()
