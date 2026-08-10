from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.ingestor.ingestor import UnknownEventType
from app.router.router import Router

router = APIRouter(prefix="/events", tags=["events"])


@router.post("")
async def ingest_event(payload: dict, request: Request, session: AsyncSession = Depends(get_session)):
    ingestor = request.app.state.ingestor
    engine = request.app.state.engine

    try:
        event = ingestor.process(payload)
    except (UnknownEventType, ValidationError) as e:
        raise HTTPException(status_code=422, detail=str(e))

    if event is None:
        return {"notifications": []}  # duplicate event, already processed

    notifications = engine.on_event(event)

    now = event.ts if request.app.state.now is None else max(request.app.state.now, event.ts)
    request.app.state.now = now
    notifications += engine.tick(now)

    dispatcher = Router(session=session)
    for n in notifications:
        await dispatcher.dispatch(n)

    return {"notifications": [n.message for n in notifications]}
