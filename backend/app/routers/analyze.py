import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.customer_agent import get_customer_insight
from app.services.llm import build_prompt, stream_strategy
from app.services.planner import detect_category

router = APIRouter(prefix="/api")


@router.get("/detect-category")
def detect(idea: str):
    return detect_category(idea)


@router.get("/customer")
def customer(category: str, db: Session = Depends(get_db)):
    return get_customer_insight(db, category)


def _sse(token: str) -> str:
    return f"data: {json.dumps({'t': token})}\n\n"


DONE = "event: done\ndata: {}\n\n"


@router.get("/strategy/stream")
def strategy_stream(idea: str, db: Session = Depends(get_db)):
    det = detect_category(idea)

    if det["category"] is None:
        msg = (
            f"We don't support that category deeply yet. Closest supported "
            f"category: {det['closest']}. Try rephrasing your idea toward it."
        )

        def oos():
            yield _sse(msg)
            yield DONE

        return StreamingResponse(oos(), media_type="text/event-stream")

    try:
        payload = get_customer_insight(db, det["category"])
    except HTTPException:
        # matched category, but its offline precompute hasn't run yet --
        # stream a friendly message instead of a 404 EventSource can't read.
        # Caught here, before the generator is constructed: once
        # StreamingResponse starts iterating a generator the 200 headers
        # have already been sent, so an HTTPException raised inside the
        # generator can never become a clean 404 -- it would just break the
        # stream mid-flight.
        msg = (
            f"Insights for '{det['category']}' have not been computed yet. "
            f"Try a food or grocery idea for the full demo."
        )

        def missing():
            yield _sse(msg)
            yield DONE

        return StreamingResponse(missing(), media_type="text/event-stream")

    prompt = build_prompt(idea, det["category"], [payload])

    def gen():
        for token in stream_strategy(prompt):
            yield _sse(token)
        yield DONE

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
