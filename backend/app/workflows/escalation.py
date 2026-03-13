from __future__ import annotations


def should_trigger_escalation(
    *,
    human_requested: bool,
    unresolved_turn_count: int,
    loop_count: int,
    confidence: float,
    frustration_score: float,
    agent_requested: bool,
    tool_conflict: bool = False,
) -> bool:
    if human_requested:
        return True
    if agent_requested:
        return True
    if unresolved_turn_count >= 3:
        return True
    if loop_count >= 2:
        return True
    if confidence < 0.5:
        return True
    if frustration_score >= 0.55:
        return True
    if tool_conflict:
        return True
    return False
