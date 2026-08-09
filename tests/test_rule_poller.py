from types import SimpleNamespace

from app.api.rule_poller import refresh_rules_once
from app.engine.engine import Engine
from app.persistence.models import RuleRow


def _fake_app(engine):
    return SimpleNamespace(state=SimpleNamespace(engine=engine))


async def test_refresh_picks_up_a_rule_created_after_the_engine_started(db_session):
    engine = Engine(rules=[])
    app = _fake_app(engine)
    assert engine.rules == []

    row = RuleRow(
        rule_type="queue_backlog", scope={"queue_id": "billing"}, params={"threshold": 20},
        recipient_id="lead_maria", description="Notify me when billing backs up past 20", severity=4,
    )
    db_session.add(row)
    await db_session.commit()

    await refresh_rules_once(app)

    assert len(engine.rules) == 1
    assert engine.rules[0].rule_type == "queue_backlog"
    assert engine.rules[0].params["threshold"] == 20


async def test_refresh_drops_a_rule_that_gets_disabled(db_session):
    row = RuleRow(
        rule_type="queue_backlog", scope={"queue_id": "billing"}, params={"threshold": 20},
        recipient_id="lead_maria", description="...", severity=4, enabled=True,
    )
    db_session.add(row)
    await db_session.commit()

    engine = Engine(rules=[])
    app = _fake_app(engine)
    await refresh_rules_once(app)
    assert len(engine.rules) == 1

    row.enabled = False
    await db_session.commit()

    await refresh_rules_once(app)
    assert engine.rules == []
