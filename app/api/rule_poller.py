import asyncio

from fastapi import FastAPI

from app.persistence.database import async_session
from app.persistence.loader import load_enabled_rules


async def refresh_rules_once(app: FastAPI) -> None:
    async with async_session() as session:
        rules = await load_enabled_rules(session)
    app.state.engine.set_rules(rules)


async def poll_rules(app: FastAPI, interval_sec: float) -> None:
    while True:
        await asyncio.sleep(interval_sec)
        await refresh_rules_once(app)
