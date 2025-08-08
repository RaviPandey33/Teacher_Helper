import os
from dotenv import load_dotenv

load_dotenv()  # Load .env variables early

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
    RAZORPAY_SECRET = os.getenv("RAZORPAY_SECRET")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
