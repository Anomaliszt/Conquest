from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from api.app.config import DATABASE_PATH
from api.app.models import Base

engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=False)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()