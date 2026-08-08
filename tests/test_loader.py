import uuid

from app.engine.rules.queue_backlog import QueueBacklogRule
from app.persistence.loader import rule_from_row
from app.persistence.models import RuleRow


def test_rule_from_row_builds_correct_rule_instance():
    row = RuleRow(
        id=uuid.uuid4(), rule_type="queue_backlog", scope={"queue_id": "billing"},
        params={"threshold": 20}, recipient_id="lead_maria", description="...",
        severity=4, enabled=True,
    )

    rule = rule_from_row(row)

    assert isinstance(rule, QueueBacklogRule)
    assert rule.rule_id == str(row.id)
    assert rule.recipient_id == "lead_maria"
    assert rule.params["threshold"] == 20
