from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date
from sqlalchemy import Date


class Date_Capacity_Response_Schema(BaseModel):
    booking_id: str
    user_id: str
    name: str
    email: EmailStr
    phone_no: str
    start_date: date
    end_date: date
    car_capacity: str


class Date_Capacity_Selection_Schema(BaseModel):
    start_date: date
    end_date: date
    car_capacity: str


class Available_Car_Schema(BaseModel):
    car_name: str
    car_capacity: str
    car_rent: str
    car_picture: str
    car_detail: str


class Select_Car_Schema(BaseModel):
    car_name: str
    # car_capacity: str
    # start_date: date
    # end_date: date
    # car_picture: str


class Select_Car_Booked_Schema(BaseModel):
    car_name: str
    car_capacity: str
    # car_detail: str
    car_rent: str
