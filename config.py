from dotenv import load_dotenv
import os

load_dotenv()

DB_URL=os.environ.get("DB_URL")
ALGORITHM=os.environ.get("ALGORITHM")
SECRET_KEY=os.environ.get("SECRET_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
