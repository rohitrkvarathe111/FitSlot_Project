from enum import Enum
from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime





class UserTypeEnum(str, Enum):
    ADMIN = "ADMIN"
    INSTRUCTOR = "INSTRUCTOR"
    STUDENT = "STUDENT"


class UserCreate(BaseModel):
    # username: str
    email: EmailStr
    password: constr(min_length=8)
    first_name: str
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    time_zone: Optional[str] = None
    mobile_number: Optional[constr(max_length=13)] = None
    user_type: UserTypeEnum
    is_admin: Optional[bool] = False
    # is_active: Optional[bool] = True
    # created_by: Optional[int] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: constr(min_length=8)



class SessionTokenBase(BaseModel):
    user_id: int
    encrypt_session_data: str
    expires_at: Optional[datetime] = None



class Instructor(BaseModel):
    id: int
    username: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile_number: Optional[str] = None
    user_type: UserTypeEnum
    time_zone: str

    class Config:
        orm_mode = True
    

class CreateSession(BaseModel):
    instructor_id: int
    class_name: str
    start_date: datetime
    end_date: datetime
    allot_slot: int







