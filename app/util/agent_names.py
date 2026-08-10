def format_agent_name(agent_id: str) -> str:
    """Turns a raw agent id into a readable name, e.g. "a_88" -> "Agent 88"."""
    number = agent_id.strip().removeprefix("a_").lstrip("0") or "0"
    return f"Agent {number}"
