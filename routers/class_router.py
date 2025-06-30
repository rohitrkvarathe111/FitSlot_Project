from fastapi import APIRouter
from sqlalchemy.orm import Session
from database import SessionLocal
from models.user_models import User, SessionToken, FitClasses
from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from datetime import datetime, timedelta
from typing import List, Optional
from database import get_db
from schemas.classes_schemas import AllClasss



router = APIRouter(
    prefix="/class",
    tags=["Class"]
)


@router.get("/class", response_model=List[AllClasss])
def get_class(db: Session = Depends(get_db)):
    classes = db.query(FitClasses).all()
    return classes


