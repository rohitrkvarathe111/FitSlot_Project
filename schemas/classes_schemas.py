from enum import Enum
from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime



class AllClasss(BaseModel):
    id: int
    instructor_name: str
    instructor_id: int
    class_name: str
    start_date: datetime
    end_date: datetime
    # allot_slot: int
    remaining_slot: int
    is_active: bool

    class Config:
        orm_mode = True



class AllBooking(BaseModel):
    id: int
    class_id: int
    user_id: int
    start_date: datetime
    end_date: datetime
    booked_at: datetime

    class Config:
        orm_mode = True