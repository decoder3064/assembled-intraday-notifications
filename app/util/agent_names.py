def format_agent_name(agent_id: str) -> str:
    """"a_88" -> "Agent 88" — a raw id reads as code, not the subject of a
    sentence; notification messages should read like English."""
    number = agent_id.strip().removeprefix("a_").lstrip("0") or "0"
    return f"Agent {number}"
