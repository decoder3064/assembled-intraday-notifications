import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.api.schemas import RuleCreate, RuleOut, RuleUpdate
from app.engine.rules import RULE_REGISTRY
from app.persistence.models import RuleRow

router = APIRouter(prefix="/rules", tags=["rules"])


def _validate_params(params: dict) -> None:
    for key, value in params.items():
        if isinstance(value, (int, float)) and value < 0:
            raise HTTPException(status_code=422, detail=f"{key!r} cannot be negative")


@router.post("", response_model=RuleOut, status_code=201)
async def create_rule(payload: RuleCreate, session: AsyncSession = Depends(get_session)):
    if payload.rule_type not in RULE_REGISTRY:
        raise HTTPException(status_code=422, detail=f"unrecognized rule type: {payload.rule_type!r}")
    _validate_params(payload.params)

    row = RuleRow(**payload.model_dump())
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


@router.get("", response_model=list[RuleOut])
async def list_rules(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(RuleRow))
    return result.scalars().all()


@router.patch("/{rule_id}", response_model=RuleOut)
async def update_rule(rule_id: uuid.UUID, payload: RuleUpdate, session: AsyncSession = Depends(get_session)):
    row = await session.get(RuleRow, rule_id)
    if row is None:
        raise HTTPException(status_code=404, detail="rule not found")
    if payload.params is not None:
        _validate_params(payload.params)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)

    await session.commit()
    await session.refresh(row)
    return row


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    row = await session.get(RuleRow, rule_id)
    if row is None:
        raise HTTPException(status_code=404, detail="rule not found")

    # The database handles cleanup on delete: rule_state rows (unused today)
    # cascade away, notification rows survive with rule_id set to NULL, so
    # notification history is preserved even after the rule is gone.
    await session.delete(row)
    await session.commit()
