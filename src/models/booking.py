from database.database import Base
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, Date
from datetime import datetime, timezone
from sqlalchemy.orm import relationship


class Booking(Base):
    __tablename__ = "booking"
    booking_id = Column(String(100), primary_key=True, nullable=False)
    user_id = Column(String(100), ForeignKey("users.id"), nullable=True)
    car_id = Column(String(100), ForeignKey("car.id"), nullable=True)
    car_rc = Column(String(100), nullable=True)
    name = Column(String(100), nullable=False)
    phone_no = Column(String(10), nullable=False)
    email = Column(String(100), nullable=False)
    car_name = Column(String(100), default="NA", nullable=True)
    car_capacity = Column(String(100), nullable=False)
    car_picture = Column(String(100), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    car_rent = Column(String(100), default=0, nullable=False)
    bill_amount = Column(String(100), nullable=True)
    in_process = Column(Boolean, default=True, nullable=False)
    is_booked = Column(Boolean, default=False, nullable=False)
    is_cancelled = Column(Boolean, default=False, nullable=False)
    booked_at = Column(DateTime, default=None, nullable=True)
    cancelled_at = Column(DateTime, default=None, nullable=True)

    user = relationship("User", back_populates="bookings")
    car = relationship("Car", back_populates="bookings")
