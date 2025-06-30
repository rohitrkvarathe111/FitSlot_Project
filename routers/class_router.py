from fastapi import APIRouter
from sqlalchemy.orm import Session
from database import SessionLocal
from models.user_models import User, SessionToken, FitClasses
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




@router.post("/book")
async def book_class(
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
    
    return session_data



