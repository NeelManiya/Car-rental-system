from fastapi import APIRouter, HTTPException
from database.database import SessionLocal
from src.schemas.booking import (
    Date_Capacity_Selection_Schema,
    Available_Car_Schema,
    Select_Car_Schema,
    Select_Car_Booked_Schema,
    Date_Capacity_Response_Schema,
)
from src.models.booking import Booking
import uuid
from src.models.car_details import Car
from src.utils.booking import decode_token, gen_otp, validate_scheduled_time
from src.models.user import OTP
from datetime import datetime
from logs.log_config import logger

booking_router = APIRouter()
db = SessionLocal()


@booking_router.post(
    "/select_date_capacity", response_model=Date_Capacity_Response_Schema
)
def select_date_capacity(token: str, details: Date_Capacity_Selection_Schema):
    logger.info("Starting date and capacity selection for booking.")
    user_details = decode_token(token)
    user_id, name, email, phone_no = user_details

    new_booking = Booking(
        booking_id=str(uuid.uuid4()),
        user_id=user_id,
        name=name,
        email=email,
        phone_no=phone_no,
        start_date=details.start_date,
        end_date=details.end_date,
        car_capacity=details.car_capacity,
    )

    validate_scheduled_time(details.start_date, details.end_date)
    if not details.start_date <= details.end_date:
        logger.error("End date is before start date.")
        raise HTTPException(
            status_code=400, detail="End date must be after start date."
        )

    find_car = db.query(Car).filter(Car.car_capacity == details.car_capacity).first()
    if not find_car:
        logger.error(f"No car found with capacity: {details.car_capacity}")
        raise HTTPException(
            status_code=404, detail="Car not found with the given capacity."
        )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    logger.info(f"Booking created successfully with ID: {new_booking.booking_id}")
    return new_booking


@booking_router.get("/get_available_cars", response_model=list[Available_Car_Schema])
def get_available_cars(booking_id: str):
    logger.info(f"Fetching available cars for booking ID: {booking_id}")
    find_booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()

    if not find_booking:
        logger.error(f"Booking not found for ID: {booking_id}")
        raise HTTPException(status_code=404, detail="Booking not found.")

    available_cars = (
        db.query(Car)
        .outerjoin(Booking, Booking.car_name == Car.car_name)
        .filter(
            (Booking.start_date > find_booking.end_date)
            | (Booking.end_date < find_booking.start_date)
            | (Booking.car_name == None),
            Car.car_capacity == find_booking.car_capacity,
        )
        .all()
    )

    if not available_cars:
        logger.warning("No cars available for the selected date range.")
        raise HTTPException(
            status_code=404, detail="No cars available for the selected date range."
        )

    logger.info(
        f"Found {len(available_cars)} available cars for booking ID: {booking_id}"
    )
    return available_cars


@booking_router.post(
    "/select_car/{booking_id}", response_model=Select_Car_Booked_Schema
)
def select_car(booking_id: str, details: Select_Car_Schema):
    logger.info(f"Selecting car for booking ID: {booking_id}")
    find_car = db.query(Car).filter(Car.car_name == details.car_name).first()

    if not find_car:
        logger.error(f"Car not found: {details.car_name}")
        raise HTTPException(status_code=404, detail="Car not found.")

    find_booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()

    if not find_booking:
        logger.error(f"Booking not found for ID: {booking_id}")
        raise HTTPException(status_code=404, detail="Invalid booking ID.")

    find_booking.car_name = find_car.car_name
    find_booking.car_rc = find_car.car_rc
    find_booking.car_picture = find_car.car_picture

    db.commit()
    db.refresh(find_car)
    db.refresh(find_booking)
    logger.info(
        f"Car {find_car.car_name} successfully assigned to booking ID: {booking_id}"
    )
    return find_car


@booking_router.post("/send_payment_otp")
def send_payment_otp(booking_id: str):
    logger.info(f"Generating payment OTP for booking ID: {booking_id}")
    find_booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()

    if not find_booking:
        logger.error(f"Booking not found for ID: {booking_id}")
        raise HTTPException(status_code=404, detail="Booking not found.")

    find_car = db.query(Car).filter(Car.car_name == find_booking.car_name).first()

    if not find_car:
        logger.error(f"Car not found for booking ID: {booking_id}")
        raise HTTPException(status_code=404, detail="Car not found.")

    rental_days = (find_booking.end_date - find_booking.start_date).days
    if rental_days <= 0:
        logger.error("Invalid rental period.")
        raise HTTPException(status_code=400, detail="Invalid rental period.")

    bill_amount = rental_days * int(find_car.car_rent)
    logger.info(f"Calculated bill amount: {bill_amount} for booking ID: {booking_id}")

    find_booking.car_rent = find_car.car_rent
    find_booking.bill_amount = bill_amount

    gen_otp(find_booking.email, bill_amount)
    db.commit()
    db.refresh(find_booking)
    logger.info(f"Payment OTP sent successfully to email: {find_booking.email}")
    return "Email sent successfully. Please complete payment."


@booking_router.get("/verify_payment_otp")
def verify_payment_otp(email: str, otp: str):
    logger.info(f"Verifying payment OTP for email: {email}")
    find_car_otp = (
        db.query(Booking)
        .filter(
            Booking.email == email,
            Booking.is_booked == False,
            Booking.in_process == True,
        )
        .first()
    )

    if not find_car_otp:
        logger.error(f"No booking in process for email: {email}")
        raise HTTPException(
            status_code=404, detail="No booking in process for this email."
        )

    find_otp = db.query(OTP).filter(OTP.email == email, OTP.otp == otp).first()

    if not find_otp:
        logger.error("Invalid email or OTP.")
        raise HTTPException(status_code=400, detail="Invalid email or OTP.")

    find_car_otp.is_booked = True
    find_car_otp.in_process = False
    find_car_otp.booked_at = datetime.now()

    db.delete(find_otp)
    db.commit()
    db.refresh(find_car_otp)
    logger.info(f"OTP verified successfully for email: {email}")
    return "OTP verified successfully."


@booking_router.post("/cancel_booking")
def cancel_booking(booking_id: str):
    logger.info(f"Attempting to cancel booking ID: {booking_id}")
    find_booking = (
        db.query(Booking)
        .filter(
            Booking.booking_id == booking_id,
            Booking.is_booked == True,
            Booking.is_cancelled == False,
        )
        .first()
    )

    if not find_booking:
        logger.error(f"Booking not found for ID: {booking_id}")
        raise HTTPException(status_code=404, detail="Booking not found.")

    if find_booking.is_booked == False:
        logger.warning(f"Booking already canceled for ID: {booking_id}")
        raise HTTPException(status_code=400, detail="Booking is already canceled.")

    find_booking.is_cancelled = True
    find_booking.is_booked = False
    find_booking.in_process = False
    find_booking.cancelled_at = datetime.now()

    db.commit()
    db.refresh(find_booking)
    logger.info(f"Booking ID: {booking_id} canceled successfully.")
    return "Booking canceled successfully."
