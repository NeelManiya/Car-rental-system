from fastapi import FastAPI
from src.routers.user import user_router
from src.routers.car_details import car_router
from src.routers.booking import booking_router


app = FastAPI()

app.include_router(user_router)
app.include_router(car_router)
app.include_router(booking_router)
