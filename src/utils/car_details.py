from src.models.car_details import Car
from database.database import SessionLocal
from fastapi import HTTPException, status
from config import SECRET_KEY, ALGORITHM
import jwt
from logs.log_config import logger  # Assuming logger is configured

db = SessionLocal()


def find_same_car_rc(car_rc: str):
    logger.info(f"Checking for duplicate car RC: {car_rc}")
    find_same_car_rc = db.query(Car).filter(Car.car_rc == car_rc).first()

    if find_same_car_rc:
        logger.error(f"Duplicate car RC found: {car_rc}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Car RC already exists"
        )
    logger.info(f"No duplicate found for car RC: {car_rc}")


def decode_token(token: str):
    logger.info("Decoding token for user authentication.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id = payload.get("id")
        email = payload.get("email")
        username = payload.get("username")

        if not id or not username or not email:
            logger.error("Token decoding failed: Missing required fields.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token: Missing required fields",
            )
        logger.info(f"Token decoded successfully for user: {username}")
        return id, username, email

    except jwt.ExpiredSignatureError:
        logger.error("Token decoding failed: Token has expired.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token has expired. Please login again.",
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Token decoding failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token. Please provide a valid token.",
        )
