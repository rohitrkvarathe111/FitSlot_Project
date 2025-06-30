from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text, Float, BigInteger, Enum
from sqlalchemy.dialects.postgresql import ARRAY
import datetime

from models.user_models import FitClasses, User


class FitBooking(Base):
    __tablename__ = "fit_booking"
    

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("fit_classes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    booked_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)

    fitness_class = relationship("FitClasses", backref="bookings")
    user = relationship("User", backref="bookings")



