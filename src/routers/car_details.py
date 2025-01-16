from fastapi import APIRouter, HTTPException, UploadFile, File
from database.database import SessionLocal
from src.models.car_details import Car
from src.schemas.car_details import (
    CarListingSchema,
    CarDataUpdateSchema,
    GetAllCarSchema,
)
from src.utils.car_details import find_same_car_rc
import uuid
import shutil
import os
from logs.log_config import logger

car_router = APIRouter()
db = SessionLocal()


@car_router.post("/car_listing")
def car_listing(car_details: CarListingSchema):
    logger.info(f"Attempting to list a new car: {car_details.car_name}")
    new_car = Car(
        id=str(uuid.uuid4()),
        car_name=car_details.car_name,
        car_rc=car_details.car_rc,
        car_rent=car_details.car_rent,
        car_capacity=car_details.car_capacity,
        car_detail=car_details.car_detail,
    )

    find_one_entry = db.query(Car).first()
    if find_one_entry:
        logger.info(f"Checking for duplicate car RC: {car_details.car_rc}")
        find_same_car_rc(car_details.car_rc)

    db.add(new_car)
    db.commit()
    db.refresh(new_car)
    logger.info(f"Car {car_details.car_name} listed successfully.")
    return {"message": "Car added successfully", "car": new_car}


UPLOAD_DIR = "photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@car_router.post("/upload-photo/")
async def upload_photo(id: str, file: UploadFile = File(...)):
    logger.info(f"Uploading photo for car ID: {id}")
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    get_car = db.query(Car).filter(Car.id == id).first()

    if not get_car:
        logger.error(f"Car with ID: {id} not found for photo upload.")
        raise HTTPException(status_code=404, detail="Car ID incorrect")

    get_car.car_picture = file_location

    db.commit()
    db.refresh(get_car)

    logger.info(f"Photo '{file.filename}' saved at '{file_location}' for car ID: {id}")
    return {"info": f"File '{file.filename}' saved at '{file_location}'"}


@car_router.patch("/update_car/{id}")
def update_car(id: str, car_update: CarDataUpdateSchema):
    logger.info(f"Updating car details for ID: {id}")
    find_car = db.query(Car).filter(Car.id == id).first()

    if not find_car:
        logger.error(f"Car with ID: {id} not found for update.")
        raise HTTPException(status_code=404, detail="Car not found")

    new_data = car_update.model_dump(exclude_none=True)

    for key, value in new_data.items():
        setattr(find_car, key, value)

    db.commit()
    db.refresh(find_car)

    logger.info(f"Car with ID: {id} updated successfully.")
    return {"message": "Car updated successfully", "car": find_car}


@car_router.get("/get_all_car", response_model=list[GetAllCarSchema])
def get_all_car():
    logger.info("Fetching all available cars.")
    find_car = db.query(Car).filter(Car.is_deleted == False).all()

    if not find_car:
        logger.error("No cars found.")
        raise HTTPException(status_code=404, detail="No cars available")

    logger.info(f"Found {len(find_car)} cars.")
    return find_car


@car_router.delete("/delete_car/{id}")
def delete_car(id: str):
    logger.info(f"Attempting to delete car with ID: {id}")
    find_car = db.query(Car).filter(Car.id == id, Car.is_booked == False).first()

    if not find_car:
        logger.error(f"Car with ID: {id} not found or is currently booked.")
        raise HTTPException(status_code=404, detail="Car not found or currently booked")

    if find_car.is_deleted:
        logger.warning(f"Car with ID: {id} is already marked as deleted.")
        raise HTTPException(status_code=400, detail="Car already deleted")

    find_car.is_deleted = True

    db.commit()
    db.refresh(find_car)

    logger.info(f"Car with ID: {id} deleted successfully.")
    return {"message": "Car deleted successfully", "data": find_car}
