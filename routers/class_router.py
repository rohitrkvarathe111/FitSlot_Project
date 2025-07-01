from fastapi import APIRouter
from sqlalchemy.orm import Session
from database import SessionLocal
from models.user_models import User, SessionToken, FitClasses
from models.class_models import FitBooking
from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from database import get_db
from schemas.classes_schemas import AllClasss
import base64, json
import pytz



router = APIRouter(
    prefix="/class",
    tags=["Class"]
)


@router.get("/class", response_model=List[AllClasss])
async def get_class(
    token: str = Query(..., description="Session token"),
    db: Session = Depends(get_db)):

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
        session_data = json.loads(decrypted_bytes.decode())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to decrypt session data: {str(e)}"
        )
    
    time_zone = session_data.get("time_zone")

    classes = db.query(FitClasses).order_by(FitClasses.id.desc()).all()
    converted_classes = []
    for cls in classes:
        converted_start = convert_utc_to_local(cls.start_date, time_zone)
        converted_end = convert_utc_to_local(cls.end_date, time_zone)

        converted_classes.append(AllClasss(
            id=cls.id,
            instructor_name=cls.instructor_name,
            instructor_id=cls.instructor_id,
            class_name=cls.class_name,
            start_date=converted_start,
            end_date=converted_end,
            remaining_slot=cls.remaining_slot,
            is_active=cls.is_active
        ))
    
    return converted_classes
    # return classes




def convert_utc_to_local(utc_dt, target_timezone_str):

    if utc_dt.tzinfo is None:
        utc_dt = pytz.UTC.localize(utc_dt)
    local_tz = pytz.timezone(target_timezone_str)
    local_dt = utc_dt.astimezone(local_tz)
    return local_dt




@router.post("/book", status_code=status.HTTP_201_CREATED)
async def book_class(
    token: str = Query(..., description="Session token"),
    class_id: int = Query(..., description="ID of the fitness class to book"),
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
        session_data = json.loads(decrypted_bytes.decode())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to decrypt session data: {str(e)}"
        )
        

    class_book = db.query(FitClasses).filter(
        FitClasses.id == class_id,
        FitClasses.is_active == True
    ).first()

    if not class_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fitness class not found"
        )

    if class_book.remaining_slot <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This class is fully booked"
        )
    
    start_date = class_book.start_date
    start_date = start_date.replace(tzinfo=timezone.utc)
    if start_date < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot book this class because the start date has already passed."
        )

    booking = FitBooking(
        class_id=class_id,
        user_id=session_data.get("user_id"),
        start_date=class_book.start_date,
        end_date=class_book.end_date,
        booked_at=datetime.utcnow(),
    )

    class_book.remaining_slot -= 1
    db.add(booking)
    db.commit()
    db.refresh(booking)

    c_start = convert_utc_to_local(class_book.start_date, session_data.get("time_zone"))
    c_end = convert_utc_to_local(class_book.end_date, session_data.get("time_zone"))
    print(c_start, c_end)
    return {
        "message": f"Your fitness class '{class_book.class_name}' has been successfully booked.",
        "booking_id": booking.id,
        "class_id": class_book.id,
        "class_name": class_book.class_name,
        "start_date": c_start,
        "end_date": c_end,
        "remaining_slots": class_book.remaining_slot
    }