from __future__ import annotations

import re


def issue_fingerprint(text: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    tokens = [token for token in normalized.split() if token not in {"the", "a", "an", "and", "to", "for"}]
    return " ".join(tokens[:8])


def update_loop_state(
    *,
    user_message: str,
    last_issue_fingerprint: str | None,
    current_loop_count: int,
    unresolved_turn_count: int,
    resolved: bool,
) -> dict:
    fingerprint = issue_fingerprint(user_message)

    if last_issue_fingerprint and fingerprint == last_issue_fingerprint:
        loop_count = current_loop_count + 1
    else:
        loop_count = max(0, current_loop_count - 1)

    if resolved:
        next_unresolved = 0
    else:
        next_unresolved = unresolved_turn_count + 1

    return {
        "last_issue_fingerprint": fingerprint,
        "loop_count": loop_count,
        "unresolved_turn_count": next_unresolved,
    }
