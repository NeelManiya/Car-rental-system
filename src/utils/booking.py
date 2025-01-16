from src.models.car_details import Car
from database.database import SessionLocal
from fastapi import HTTPException, status
import jwt
from config import SECRET_KEY, ALGORITHM
import random, uuid
from src.models.user import OTP, User
from src.models.booking import Booking
from datetime import date
from logs.log_config import logger  # Assuming logger is configured
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import SENDER_EMAIL, EMAIL_PASSWORD

db = SessionLocal()


def find_same_car_rc(car_rc: str):
    logger.info(f"Checking if car with RC: {car_rc} is already booked.")
    find_same_car_rc = db.query(Car).filter(Car.car_rc == car_rc).first()

    if find_same_car_rc:
        logger.error(f"Car with RC: {car_rc} is already booked.")
        raise HTTPException(status_code=409, detail="This car is already booked.")
    logger.info(f"Car with RC: {car_rc} is available for booking.")


def decode_token(token: str):
    logger.info("Decoding token.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        id = payload.get("id")
        name = payload.get("name")
        email = payload.get("email")
        phone_no = payload.get("phone_no")

        if not id or not name or not email or not phone_no:
            logger.error("Token is invalid: Missing required fields.")
            raise HTTPException(status_code=403, detail="Invalid token.")
        logger.info(f"Token decoded successfully for user ID: {id}.")
        return id, name, email, phone_no

    except jwt.ExpiredSignatureError:
        logger.error("Token has expired.")
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        raise HTTPException(status_code=403, detail="Invalid token.")


def gen_otp(email: str, bill_amount: str):
    logger.info(f"Generating OTP for email: {email}, bill amount: {bill_amount}.")
    find_user = db.query(User).filter(User.email == email).first()

    if not find_user:
        logger.error(f"User not found with email: {email}.")
        raise HTTPException(status_code=404, detail="User not found.")

    random_otp = random.randint(1000, 9999)
    logger.info(f"Generated OTP: {random_otp} for email: {email}.")

    new_otp = OTP(
        id=str(uuid.uuid4()),
        email=find_user.email,
        user_id=find_user.id,
        otp=random_otp,
    )

    send_email(
        find_user.email,
        "Payment OTP",
        f"Your bill amount is {bill_amount}. OTP: {random_otp}",
    )

    db.add(new_otp)
    db.commit()
    db.refresh(new_otp)
    logger.info(f"OTP stored in database for email: {email}.")
    return "OTP generated successfully."


def send_email(receiver, subject, body):
    logger.info(f"Sending email to: {receiver}, subject: {subject}.")
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = SENDER_EMAIL
    smtp_pass = EMAIL_PASSWORD

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(SENDER_EMAIL, receiver, msg.as_string())
        logger.info(f"Email sent successfully to: {receiver}.")
    except Exception as e:
        logger.error(f"Error sending email to {receiver}: {e}")


def validate_scheduled_time(start_date: str, end_date: str):
    logger.info(
        f"Validating scheduled time: start_date={start_date}, end_date={end_date}."
    )
    if start_date < date.today() and end_date < date.today():
        logger.error("Scheduled time is in the past.")
        raise HTTPException(
            status_code=400, detail="Scheduled time must be in the future."
        )
    if start_date >= end_date:
        logger.error("Invalid end date: End date is before start date.")
        raise HTTPException(status_code=400, detail="Please enter a valid end date.")
    logger.info("Scheduled time validated successfully.")
    return True
