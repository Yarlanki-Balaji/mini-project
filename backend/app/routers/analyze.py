from fastapi import APIRouter

from app.services.planner import detect_category

router = APIRouter(prefix="/api")


@router.get("/detect-category")
def detect(idea: str):
    return detect_category(idea)
