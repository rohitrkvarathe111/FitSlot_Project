from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from fastapi import FastAPI, Depends, HTTPException, status
from models.user_models import User
from models.class_models import FitBooking
from routers import user_router, class_router


Base.metadata.create_all(bind=engine)


# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


app = FastAPI(debug=True)

app.include_router(user_router.router)
app.include_router(class_router.router)



# @app.get("/api")
# def base_root():
#     return {"message": "hello world"}
