from pydantic import BaseModel
from typing import Optional


class CarListingSchema(BaseModel):
    car_name: str
    car_rc: str
    car_rent: str
    car_capacity: str
    car_detail: str


class CarDataUpdateSchema(BaseModel):
    car_rent: Optional[str] = None


class GetAllCarSchema(BaseModel):
    id: str
    car_name: str
    car_rc: str
    car_rent: str
    car_capacity: str
