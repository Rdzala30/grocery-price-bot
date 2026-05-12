import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Validate that required variables are present
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set in the environment variables. Please check your .env file.")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in the environment variables. Please check your .env file.")
