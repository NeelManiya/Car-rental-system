import logging
from passlib.context import CryptContext
from database.database import SessionLocal
from src.models.user import User, OTP
from fastapi import HTTPException
import random, uuid

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SessionLocal()


# ----------------------------------------------------------------------------------------------------
# check for same email
def find_same_email(email: str):
    logger.info(f"Checking if email {email} exists")
    find_same_email = (
        db.query(User).filter(User.email == email and User.is_active == True).first()
    )

    if find_same_email:
        logger.warning(f"Email {email} already exists")
        if find_same_email.is_active == True:
            raise HTTPException(status_code=400, detail="Email already exists")
        if find_same_email.is_active == False:
            raise HTTPException(
                status_code=400,
                detail="Email already exists but this account is deleted, try with a different username",
            )


# ----------------------------------------------------------------------------------------------------
# OTP generation
def gen_otp(email):
    logger.info(f"Generating OTP for email {email}")
    find_user = (
        db.query(User)
        .filter(User.email == email, User.is_active == True, User.is_deleted == False)
        .first()
    )

    if not find_user:
        logger.error(f"User with email {email} not found")
        raise HTTPException(status_code=400, detail="User not found")

    random_otp = random.randint(1000, 9999)

    # store OTP in the database
    new_otp = OTP(
        id=str(uuid.uuid4()),
        email=find_user.email,
        user_id=find_user.id,
        otp=random_otp,
    )

    send_email(find_user.email, "Login Email", f"OTP is {random_otp}")

    db.add(new_otp)
    db.commit()
    db.refresh(new_otp)
    logger.info(f"OTP {random_otp} generated and sent to email {email}")
    return "OTP generated successfully"


# ----------------------------------------------------------------------------------------------------
# Email sender
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import SENDER_EMAIL, EMAIL_PASSWORD


def send_email(receiver, subject, body):
    logger.info(f"Sending email to {receiver} with subject {subject}")
    # SMTP Configuration (for Gmail)
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = SENDER_EMAIL
    smtp_pass = EMAIL_PASSWORD

    # Build the mail system to send someone
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Try to send the mail to receiver
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(SENDER_EMAIL, receiver, msg.as_string())
        logger.info(f"Email sent successfully to {receiver}")
    except Exception as e:
        logger.error(f"Error sending email to {receiver}: {e}")
        raise HTTPException(status_code=500, detail="Email sending failed")


# ----------------------------------------------------------------------------------------------------
# Password checker
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def pass_checker(user_pass, hash_pass):
    logger.info(f"Checking password for user")
    if pwd_context.verify(user_pass, hash_pass):
        logger.info("Password is correct")
        return True
    else:
        logger.warning("Password is incorrect")
        raise HTTPException(status_code=401, detail="Password is incorrect")


# ----------------------------------------------------------------------------------------------------
# Token handling
from config import SECRET_KEY, ALGORITHM
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException, status


def get_token(id: str, name: str, email: str, phone_no: str):
    logger.info(f"Generating token for user {email}")
    try:
        payload = {
            "id": id,
            "name": name,
            "email": email,
            "phone_no": phone_no,
            "exp": datetime.now(timezone.utc) + timedelta(days=7),
        }
        access_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        logger.info(f"Token generated for user {email}")
        return {"access_token": access_token}
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def decode_token(token: str):
    logger.info(f"Decoding token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        id = payload.get("id")
        name = payload.get("name")
        email = payload.get("email")
        phone_no = payload.get("phone_no")

        if not id or not name or not email or not phone_no:
            logger.warning("Invalid token, missing required fields")
            raise HTTPException(status_code=403, detail="Invalid token")
        logger.info(f"Token decoded successfully for user {email}")
        return id, name, email, phone_no

    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        raise HTTPException(status_code=403, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        raise HTTPException(status_code=403, detail="Invalid token")
