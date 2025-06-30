from fastapi import APIRouter
from sqlalchemy.orm import Session
from database import SessionLocal
from models.user_models import User, SessionToken, FitClasses
from models.class_models import FitBooking
from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from datetime import datetime, timedelta
from typing import List, Optional
from database import get_db
from schemas.classes_schemas import AllClasss
import base64, json



router = APIRouter(
    prefix="/class",
    tags=["Class"]
)


@router.get("/class", response_model=List[AllClasss])
async def get_class(db: Session = Depends(get_db)):
    classes = db.query(FitClasses).all()
    return classes



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

    return {
        "message": f"Your fitness class '{class_book.class_name}' has been successfully booked.",
        "booking_id": booking.id,
        "class_id": class_book.id,
        "class_name": class_book.class_name,
        "start_date": class_book.start_date.isoformat(),
        "end_date": class_book.end_date.isoformat(),
        "remaining_slots": class_book.remaining_slot
    }