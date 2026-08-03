from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

_engine = None
_SessionLocal = None


def _init():
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(get_settings().database_url, pool_pre_ping=True)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False)


def get_db():
    _init()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
