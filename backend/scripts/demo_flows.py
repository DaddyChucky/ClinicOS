from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import SessionLocal, init_db
from app.workflows.orchestrator import WorkflowOrchestrator


async def run_demo() -> None:
    init_db()
    db = SessionLocal()
    orchestrator = WorkflowOrchestrator(db)

    conversation = await orchestrator.start_conversation(
        user_name="Demo Operator",
        user_email="demo-operator@clinicos.app",
    )

    flow_messages = [
        "Why was I billed twice and how do I upgrade?",
        "Actually we are not a customer yet and evaluating software for our dental office",
        "Use those pain points to generate a marketing nurture campaign",
        "This still is not helping, I need a human",
    ]

    for message in flow_messages:
        response = await orchestrator.process_message(conversation.id, message)
        print("\n---")
        print(f"User: {message}")
        print(f"Agent: {response.active_agent}")
        print(f"Workflow: {response.active_workflow}")
        print(f"Assistant: {response.assistant_message[:300]}")
        print(f"Escalation: {response.escalation_recommended}")
        print(f"Drafts: {len(response.drafts_created)}")

    db.close()


if __name__ == "__main__":
    asyncio.run(run_demo())
