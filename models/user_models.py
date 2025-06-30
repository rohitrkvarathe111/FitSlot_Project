from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text, Float, BigInteger, Enum
from sqlalchemy.dialects.postgresql import ARRAY
import datetime




USER_TYPES = ("ADMIN", "INSTRUCTOR", "STUDENT")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)

    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    mobile_number = Column(String(13), nullable=True)  
    user_type = Column(
        Enum(*USER_TYPES, name="user_type_enum"),
        nullable=False
    )
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    update_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    creator = relationship("User", remote_side=[id], foreign_keys=[created_by], post_update=True, backref="created_users")
    updater = relationship("User", remote_side=[id], foreign_keys=[update_by], post_update=True, backref="updated_users")



class SessionToken(Base):
    __tablename__ = "session_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String, unique=True, index=True, nullable=False)
    encrypt_session_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime)

    user = relationship("User")



class FitClasses(Base):
    __tablename__ = "fit_classes"

    id = Column(Integer, primary_key=True, index=True)
    instructor_name = Column(String(100), nullable=False)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    class_name = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    allot_slot = Column(Integer, nullable=False)
    remaining_slot = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

    user = relationship("User", backref="fit_classes")


