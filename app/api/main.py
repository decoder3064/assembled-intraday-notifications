import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import events, notifications, rules
from app.api.rule_poller import poll_rules
from app.engine.engine import Engine
from app.ingestor.ingestor import Ingestor
from app.persistence.database import async_session, engine as db_engine
from app.persistence.loader import load_enabled_rules
from app.persistence.models import Base

RULE_POLL_INTERVAL_SEC = 5.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        engine_rules = await load_enabled_rules(session)
    app.state.engine = Engine(rules=engine_rules)
    app.state.ingestor = Ingestor()
    app.state.now = None

    poller_task = asyncio.create_task(poll_rules(app, RULE_POLL_INTERVAL_SEC))
    yield
    poller_task.cancel()


app = FastAPI(title="Intraday Notification System", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5190"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(rules.router)
app.include_router(notifications.router)
app.include_router(events.router)
