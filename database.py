from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://fitpostgres_user:QH2RjwRykxepk4VkvwBJ8nsuXxwOgsV0@dpg-d2177u3uibrs73edmva0-a.oregon-postgres.render.com:5432/fitpostgres"


# engine = create_engine(
#     DATABASE_URL, connect_args={"check_same_thread": False}
# )
engine = create_engine(DATABASE_URL)



SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
