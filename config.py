import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://Umaiyaswaran:Password_7585@cluster0.x706nl9.mongodb.net/ticket_booking?retryWrites=true&w=majority")

# OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

# Evolution API (WhatsApp)
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "https://evolution-api-production-c931.up.railway.app")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "myticket123")

# Razorpay
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

# App
APP_NAME = os.getenv("APP_NAME", "TicketHub")
