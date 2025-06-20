import os

class Config:
    SECRET_KEY = 'supersecretkey'  # Replace later with secure key
    SQLALCHEMY_DATABASE_URI = 'sqlite:///masterji.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
