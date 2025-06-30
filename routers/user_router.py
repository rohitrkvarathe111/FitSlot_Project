from fastapi import APIRouter
from schemas.user_schemas import UserTypeEnum
from sqlalchemy.orm import Session
from database import SessionLocal
from models.user_models import User, SessionToken, FitClasses
from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from passlib.context import CryptContext
import secrets
import base64
import json
from sqlalchemy import or_
from datetime import datetime, timedelta
from typing import List, Optional
from database import get_db
from schemas.user_schemas import UserCreate, UserLogin, Instructor, CreateSession
import random
import string


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")




@router.post("/create_user")
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(
        (User.email == user.email)
    ).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    hashed_pw = pwd_context.hash(user.password)
    username = generate_username(user.user_type.value, user.first_name)
    new_user = User(
        username=username,
        email=user.email,
        hashed_password=hashed_pw,
        first_name=user.first_name,
        middle_name=user.middle_name,
        last_name=user.last_name,
        mobile_number=user.mobile_number,
        user_type=user.user_type.value,  
        is_admin=user.is_admin,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created", "user_id": new_user.id}




def generate_username(user_type: str, first_name: str) -> str:
    suffix_map = {
        "ADMIN": "AD",
        "INSTRUCTOR": "INST",
        "STUDENT": "STUD"
    }
    suffix = suffix_map.get(user_type.upper(), "")
    first_name_part = first_name[:3].upper()
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    username = f"{first_name_part}_{suffix}_{random_part}"
    return username





@router.post("/login_user")
async def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = secrets.token_urlsafe(32)
    session_data = {
        "user_id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "user_type": db_user.user_type,
        "login_time": datetime.utcnow().isoformat()
    }

    json_str = json.dumps(session_data)
    encrypt_session_data = base64.b64encode(json_str.encode()).decode()

    expires_at = datetime.utcnow() + timedelta(days=1)

    session_token = SessionToken(
        user_id=db_user.id,
        token=token,
        encrypt_session_data=encrypt_session_data,
        created_at=datetime.utcnow(),
        expires_at=expires_at
    )
    
    db.add(session_token)
    db.commit()
    db.refresh(session_token)

    return {
        "message": "Login successful",
        "user_id": db_user.id,
        "token": token,
        "username": db_user.username,
        "email": db_user.email,
        "user_type": db_user.user_type,
        "is_active": db_user.is_active,
        "expires_at": expires_at.isoformat()
    }



@router.get("/instructors", response_model=List[Instructor])
async def all_instructors(db: Session = Depends(get_db)):

    db_user = db.query(User).filter(User.user_type == "INSTRUCTOR").all()

    return db_user
    



@router.post("/create_session", status_code=status.HTTP_201_CREATED)
async def create_session(session: CreateSession, db: Session = Depends(get_db)):

    if session.end_date <= session.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date."
        )
    
    max_duration = timedelta(hours=2)
    duration = session.end_date - session.start_date
    if duration > max_duration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session duration cannot exceed 2 hours."
        )
    
    db_user = db.query(User).filter(User.id == session.instructor_id, User.user_type == "INSTRUCTOR").first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found"
        )
    
    existing_session = db.query(FitClasses).filter(
            FitClasses.instructor_id == session.instructor_id,
            or_(
                FitClasses.start_date.between(session.start_date, session.end_date),
                FitClasses.end_date.between(session.start_date, session.end_date)
            )
        ).first()
    if existing_session:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A session for this {db_user.first_name} is already scheduled at the given time range."
        )
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found"
        )
    
    create_session = FitClasses(
        instructor_name=f"{db_user.first_name} {db_user.last_name}",
        instructor_id=db_user.id,
        class_name=session.class_name,
        start_date=session.start_date,
        end_date=session.end_date,
        allot_slot=session.allot_slot,
        remaining_slot=session.allot_slot 
    )
    db.add(create_session)
    db.commit()
    db.refresh(create_session)

    return {
        "message": f"Instructor {db_user.first_name} {db_user.last_name} class '{session.class_name}' "
                   f"is created between {session.start_date} to "
                   f"{session.end_date} with {session.allot_slot} slots."
    }
    



@router.get("/session_data")
async def get_session_data(
    token: str = Query(..., description="Session token"),
    db: Session = Depends(get_db)
):
    db_session = db.query(SessionToken).filter(SessionToken.token == token).first()

    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session token not found"
        )

    if db_session.expires_at and db_session.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired"
        )

    try:
        decrypted_bytes = base64.b64decode(db_session.encrypt_session_data)
        session_data_json = decrypted_bytes.decode()
        session_data = json.loads(session_data_json)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to decrypt session data: {str(e)}"
        )

    return {
        "session_data": session_data
    }
