from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.declarative import declarative_base
from app.settings import settings
from sqlalchemy.orm import declarative_base


engine = create_engine(settings.BUSINESS_DB_URL)    # , pool_pre_ping=True, connect_args={"connect_timeout": 10})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Dependency to get a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()