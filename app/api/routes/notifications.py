import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.api.schemas import NotificationOut, NotificationUpdate
from app.persistence.models import NotificationRow

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
async def list_notifications(resolved: bool = False, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(NotificationRow).where(NotificationRow.resolved == resolved).order_by(NotificationRow.sent_at.desc())
    )
    return result.scalars().all()


@router.patch("/{notification_id}", response_model=NotificationOut)
async def update_notification(
    notification_id: uuid.UUID, payload: NotificationUpdate, session: AsyncSession = Depends(get_session)
):
    row = await session.get(NotificationRow, notification_id)
    if row is None:
        raise HTTPException(status_code=404, detail="notification not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)

    await session.commit()
    await session.refresh(row)
    return row


@router.delete("/{notification_id}", status_code=204)
async def delete_notification(notification_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    row = await session.get(NotificationRow, notification_id)
    if row is None:
        raise HTTPException(status_code=404, detail="notification not found")
    await session.delete(row)
    await session.commit()
