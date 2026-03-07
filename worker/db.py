from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    return Session()
