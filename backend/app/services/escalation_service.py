from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import db_models
from app.models.enums import ConversationStatus, EscalationStatus, MessageRole
from app.models.schemas import HumanSupportQueueItemRead
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.escalation_repository import EscalationRepository
from app.services.case_service import CaseService


class EscalationService:
    def __init__(self, db: Session):
        self.db = db
        self.escalation_repo = EscalationRepository(db)
        self.conversation_repo = ConversationRepository(db)
        self.case_service = CaseService()

    def create_summary(self, conversation_id: int, reason: str) -> str:
        conversation = self.conversation_repo.get_conversation(conversation_id)
        if not conversation:
            return "Conversation not found."

        recent_user = [m.content for m in conversation.messages if m.role == "user"][-3:]
        recent_assistant = [
            m.content for m in conversation.messages if m.role == "assistant" and (m.meta_json or {}).get("sender_type") != "human"
        ][-3:]

        user_context = " | ".join(recent_user) if recent_user else "No user history."
        assistant_context = " | ".join(recent_assistant) if recent_assistant else "No assistant attempts."

        return (
            f"Escalation reason: {reason}. "
            f"Customer context: {user_context}. "
            f"Prior assistant responses: {assistant_context}."
        )

    def get_active_escalation(self, conversation_id: int):
        for escalation in self._latest_queue_escalations():
            if escalation.conversation_id == conversation_id:
                return escalation
        return None

    def list_queue_items(self) -> list[HumanSupportQueueItemRead]:
        active = self._latest_queue_escalations()
        open_ids = [item.id for item in active if item.status == EscalationStatus.OPEN]
        open_positions = {escalation_id: index + 1 for index, escalation_id in enumerate(open_ids)}
        items: list[HumanSupportQueueItemRead] = []

        for escalation in active:
            item = self._build_queue_item(escalation, open_positions.get(escalation.id))
            if item:
                items.append(item)

        return sorted(
            items,
            key=lambda item: (
                0 if item.status == EscalationStatus.OPEN else 1,
                item.queue_position or 999,
                -item.updated_at.timestamp(),
            ),
        )

    def get_queue_item(self, conversation_id: int) -> HumanSupportQueueItemRead | None:
        for item in self.list_queue_items():
            if item.conversation_id == conversation_id:
                return item
        return None

    def human_reply(
        self,
        *,
        conversation_id: int,
        message: str,
        responder_name: str,
    ):
        conversation = self.conversation_repo.get_conversation_with_context(conversation_id)
        if not conversation:
            raise ValueError("Conversation not found")

        escalation = self.escalation_repo.get_active_for_conversation(conversation_id)
        if not escalation:
            raise ValueError("No active human support request exists for this chat")

        chat_title = self._chat_title(conversation)
        if escalation.status == EscalationStatus.OPEN:
            self.take_over(conversation_id=conversation_id, responder_name=responder_name)
            escalation = self.escalation_repo.get_active_for_conversation(conversation_id)
            if not escalation:
                raise ValueError("No active human support request exists for this chat")

        if not self._has_human_reply(conversation):
            self.conversation_repo.add_message(
                conversation_id=conversation_id,
                role=MessageRole.SYSTEM,
                content="A human support agent is connected and chatting with you live in this chat.",
                agent_name="ClinicOS System",
                workflow="human_escalation",
                meta_json={
                    "sender_type": "system",
                    "event": "human_support_live_chat",
                },
            )
            self.conversation_repo.add_event_log(
                conversation_id=conversation_id,
                stage="Human Support Live Chat",
                detail=f"{responder_name} is now Live in {chat_title}. The clinic can chat with the agent in real time.",
                status="live",
                meta_json={
                    "scope": "human_support",
                    "power_state": "live",
                },
            )

        reply = self.conversation_repo.add_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=message,
            agent_name=responder_name,
            workflow="human_escalation",
            meta_json={
                "sender_type": "human",
            },
        )
        self.conversation_repo.add_event_log(
            conversation_id=conversation_id,
            stage="Human Support Reply",
            detail=f"{responder_name} replied in {chat_title}. Human support is Live for this chat.",
            status="live",
            meta_json={
                "scope": "human_support",
                "power_state": "live",
                "responder_name": responder_name,
            },
        )
        self.conversation_repo.update_conversation_state(
            conversation,
            status=ConversationStatus.ESCALATED,
            active_workflow="human_escalation",
            active_agent="human_support_agent",
            human_requested=True,
            escalation_recommended=True,
            updated_at=db_models.utc_now(),
        )
        return reply

    def take_over(
        self,
        *,
        conversation_id: int,
        responder_name: str = "Human Support",
    ) -> HumanSupportQueueItemRead:
        conversation = self.conversation_repo.get_conversation_with_context(conversation_id)
        if not conversation:
            raise ValueError("Conversation not found")

        escalation = self.escalation_repo.get_active_for_conversation(conversation_id)
        if not escalation:
            raise ValueError("No active human support request exists for this chat")

        chat_title = self._chat_title(conversation)
        if escalation.status == EscalationStatus.OPEN:
            self.escalation_repo.update_status(escalation, EscalationStatus.IN_PROGRESS)
            self.conversation_repo.add_message(
                conversation_id=conversation_id,
                role=MessageRole.SYSTEM,
                content=(
                    "A human support agent is currently reviewing this chat and is now in charge. "
                    "ClinicOS AI remains disconnected and the agent will respond promptly."
                ),
                agent_name="ClinicOS System",
                workflow="human_escalation",
                meta_json={
                    "sender_type": "system",
                    "event": "human_support_reviewing",
                },
            )
            self.conversation_repo.add_event_log(
                conversation_id=conversation_id,
                stage="Human Support Took Over",
                detail=f"{responder_name} is reviewing {chat_title}. ClinicOS AI remains Offline while human support takes over.",
                status="live",
                meta_json={
                    "scope": "human_support",
                    "power_state": "reviewing",
                    "responder_name": responder_name,
                },
            )
            self.conversation_repo.update_conversation_state(
                conversation,
                status=ConversationStatus.ESCALATED,
                active_workflow="human_escalation",
                active_agent="human_support_agent",
                human_requested=True,
                escalation_recommended=True,
                updated_at=db_models.utc_now(),
            )

        item = self.get_queue_item(conversation_id)
        if not item:
            raise ValueError("No active human support request exists for this chat")
        return item

    def create_escalation(
        self,
        conversation_id: int,
        reason: str,
        summary: str | None = None,
        created_by_agent: str | None = None,
    ):
        existing = self.escalation_repo.get_active_for_conversation(conversation_id)
        if existing and (
            self._is_user_requested_handoff(existing.reason) or not self._is_user_requested_handoff(reason)
        ):
            return existing

        if summary is None:
            summary = self.create_summary(conversation_id, reason)

        escalation = self.escalation_repo.create(
            conversation_id=conversation_id,
            summary=summary,
            reason=reason,
            created_by_agent=created_by_agent,
        )

        conversation = self.conversation_repo.get_conversation_with_context(conversation_id)
        if conversation:
            queue_position = self._queue_position(escalation)
            chat_title = self._chat_title(conversation)
            self.conversation_repo.add_message(
                conversation_id=conversation_id,
                role=MessageRole.SYSTEM,
                content=(
                    "ClinicOS AI Agent has disconnected from this chat. A human support specialist will assist you shortly. "
                    f"You're #{queue_position} in line while we route the request."
                ),
                agent_name="ClinicOS System",
                workflow="human_escalation",
                meta_json={
                    "sender_type": "system",
                    "event": "human_handoff_requested",
                    "queue_position": queue_position,
                },
            )
            self.conversation_repo.add_event_log(
                conversation_id=conversation_id,
                stage="ClinicOS AI Agent Handoff",
                detail=(
                    f"{chat_title} moved into the human review queue. ClinicOS AI is Offline for this chat. "
                    f"Current queue position: #{queue_position}."
                ),
                status="offline",
                meta_json={
                    "scope": "human_support",
                    "power_state": "offline",
                    "queue_position": queue_position,
                },
            )
            self.conversation_repo.update_conversation_state(
                conversation,
                status=ConversationStatus.ESCALATED,
                active_workflow="human_escalation",
                active_agent="human_support_queue",
                escalation_recommended=True,
                human_requested=True,
                updated_at=db_models.utc_now(),
            )

        return escalation

    def _latest_queue_escalations(self) -> list[db_models.Escalation]:
        latest_by_conversation: dict[int, db_models.Escalation] = {}
        for escalation in self.escalation_repo.list_active():
            if not self._is_user_requested_handoff(escalation.reason):
                continue

            current = latest_by_conversation.get(escalation.conversation_id)
            if current is None or escalation.updated_at >= current.updated_at:
                latest_by_conversation[escalation.conversation_id] = escalation

        return sorted(latest_by_conversation.values(), key=lambda item: item.created_at)

    def _queue_position(self, escalation: db_models.Escalation) -> int:
        open_items = [item for item in self.escalation_repo.list_active() if item.status == EscalationStatus.OPEN]
        for index, item in enumerate(open_items, start=1):
            if item.id == escalation.id:
                return index
        return 1

    def _build_queue_item(
        self,
        escalation: db_models.Escalation,
        queue_position: int | None,
    ) -> HumanSupportQueueItemRead | None:
        conversation = self.conversation_repo.get_conversation_with_context(escalation.conversation_id)
        if not conversation:
            return None

        snapshot = self.case_service.build_case_snapshot(conversation)
        category = self._category_label(conversation, snapshot.intent_mix)
        if category != "Customer Support":
            return None

        return HumanSupportQueueItemRead(
            escalation_id=escalation.id,
            conversation_id=conversation.id,
            chat_title=self._chat_title(conversation),
            category=category,
            status=escalation.status,
            handoff_stage=self._handoff_stage(conversation, escalation),
            queue_position=queue_position if escalation.status == EscalationStatus.OPEN else None,
            summary=escalation.summary,
            summary_points=self._summary_points(escalation.summary),
            latest_message_preview=self._latest_preview(conversation),
            clinic_name=snapshot.clinic_memory.clinic_name,
            practice_type=snapshot.clinic_memory.practice_type,
            requested_at=escalation.created_at,
            updated_at=conversation.updated_at,
        )

    def _chat_title(self, conversation: db_models.Conversation) -> str:
        if conversation.title and conversation.title.strip():
            return conversation.title
        return f"Practice Desk Chat #{conversation.id}"

    def _latest_preview(self, conversation: db_models.Conversation) -> str | None:
        non_system_messages = [message for message in conversation.messages if message.role != MessageRole.SYSTEM]
        target = non_system_messages[-1] if non_system_messages else (conversation.messages[-1] if conversation.messages else None)
        if not target:
            return None
        preview = " ".join(target.content.strip().split())
        return f"{preview[:137]}..." if len(preview) > 140 else preview

    def _category_label(self, conversation: db_models.Conversation, intent_mix: list[str]) -> str:
        latest_workflow = next(
            (
                run.workflow
                for run in sorted(conversation.runs, key=lambda item: item.created_at, reverse=True)
                if run.workflow in {"support", "sales", "marketing"}
            ),
            None,
        )
        if latest_workflow == "marketing" or ("marketing" in intent_mix and "sales" not in intent_mix):
            return "Marketing"
        if latest_workflow == "sales" or ("sales" in intent_mix and "marketing" not in intent_mix):
            return "Sales & Outreach"
        return "Customer Support"

    def _handoff_stage(self, conversation: db_models.Conversation, escalation: db_models.Escalation) -> str:
        if escalation.status == EscalationStatus.OPEN:
            return "queued"
        if self._has_human_reply(conversation):
            return "live_chat"
        return "reviewing"

    def _has_human_reply(self, conversation: db_models.Conversation) -> bool:
        return any((message.meta_json or {}).get("sender_type") == "human" for message in conversation.messages)

    def _summary_points(self, summary: str) -> list[str]:
        parts = []
        for raw in summary.split(". "):
            cleaned = raw.strip().rstrip(".")
            if not cleaned:
                continue
            cleaned = cleaned.replace("Escalation reason:", "Reason:").replace("Customer context:", "Clinic Context:").replace(
                "Prior assistant responses:",
                "ClinicOS AI Tried:",
            )
            parts.append(cleaned)
        return parts[:3]

    def _is_user_requested_handoff(self, reason: str | None) -> bool:
        if not reason:
            return False
        return "user requested human support" in reason.lower()
