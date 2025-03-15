import os

class Config:
    # Read environment variables, with defaults or placeholders
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "CHANGE_THIS_SECRET")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_THIS_JWT_SECRET")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///my_database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Example: if you want to store additional config for PDF or others:
    # PDF_OUTPUT_DIR = os.getenv("PDF_OUTPUT_DIR", "/tmp/pdfs")
