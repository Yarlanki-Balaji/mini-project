from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.customer_agent import get_customer_insight
from app.services.planner import detect_category

router = APIRouter(prefix="/api")


@router.get("/detect-category")
def detect(idea: str):
    return detect_category(idea)


@router.get("/customer")
def customer(category: str, db: Session = Depends(get_db)):
    return get_customer_insight(db, category)
