from database.database import Base
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from datetime import datetime, timezone
from sqlalchemy.orm import relationship


class Car(Base):
    __tablename__ = "car"
    id = Column(String(100), primary_key=True, nullable=False)
    car_name = Column(String(100), nullable=False)
    car_rc = Column(String(100), nullable=False)
    car_picture = Column(String(100), nullable=True)
    car_capacity = Column(String(100), nullable=True)
    date = Column(String(100), nullable=True)
    car_detail = Column(String(150), nullable=True)
    car_rent = Column(String(100), nullable=False)
    is_booked = Column(Boolean, default=False, nullable=False)
    is_created = Column(DateTime, default=datetime.now, nullable=False)
    is_updated = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )
    is_deleted = Column(Boolean, default=False, nullable=False)

    bookings = relationship("Booking", back_populates="car")
