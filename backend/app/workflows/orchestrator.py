from __future__ import annotations

from dataclasses import asdict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.copilot_response_agent import run_copilot_response
from app.agents.sales_outreach_agent import run_sales_outreach
from app.agents.sales_research_agent import run_sales_research
from app.agents.support_agent import run_support
from app.agents.triage_agent import run_triage
from app.config import get_settings
from app.models import db_models
from app.models.enums import AgentType, IntentType, MessageRole, WorkflowType
from app.models.schemas import ChatMessageResponse, DraftRef, HandoffInfo
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.draft_repository import DraftRepository
from app.repositories.prospect_repository import ProspectRepository
from app.services.case_service import CaseService
from app.services.conversation_control_service import ConversationControlService
from app.services.escalation_service import EscalationService
from app.services.telemetry_service import log_agent_event
from app.services.trace_service import RunTrace
from app.tools.shared_tools import detect_frustration, explicit_human_request
from app.workflows.escalation import should_trigger_escalation
from app.workflows.routing import decide_routing
from app.workflows.state_manager import update_loop_state

settings = get_settings()


class WorkflowOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.conversation_repo = ConversationRepository(db)
        self.prospect_repo = ProspectRepository(db)
        self.draft_repo = DraftRepository(db)
        self.escalation_service = EscalationService(db)
        self.control_service = ConversationControlService(db)
        self.case_service = CaseService()

    async def start_conversation(self, user_name: str, user_email: str, opening_message: str | None = None):
        user = self.conversation_repo.get_or_create_user(email=user_email, name=user_name)
        conversation = self.conversation_repo.create_conversation(user_id=user.id, title="ClinicOS AI Chat")
        self.control_service.get_or_create_control(conversation.id)
        self.control_service.get_or_create_system_control()
        self.control_service.get_or_create_profile_override(conversation.id)

        if opening_message:
            await self.process_message(conversation.id, opening_message)
            conversation = self.conversation_repo.get_conversation(conversation.id)
        return conversation

    async def _run_sales_pipeline(
        self,
        *,
        user_message: str,
        conversation_id: int,
        clinic_memory: dict,
        trace: RunTrace,
    ) -> dict:
        research = await run_sales_research(
            user_message=user_message,
            clinic_memory=clinic_memory,
        )
        prospect = self.prospect_repo.create_or_update(
            clinic_name=research.profile["clinic_name"],
            clinic_type=research.profile["clinic_type"],
            conversation_id=conversation_id,
            specialty=research.profile.get("specialty"),
            size_estimate=research.profile.get("size_estimate"),
            location=research.profile.get("location"),
            existing_lead=research.profile.get("existing_lead", False),
            fit_score=research.fit_score,
            pain_points=research.profile.get("pain_points", []),
            research_summary=research.summary,
        )

        outreach = await run_sales_outreach(research.profile, research.fit_score, research.fit_reasons)
        draft = self.draft_repo.create_outreach_draft(
            prospect_id=prospect.id,
            conversation_id=conversation_id,
            subject=outreach.subject,
            body=outreach.body,
            tone=outreach.tone,
            personalization_notes=outreach.personalization_notes,
        )

        trace.add(
            "sales_pipeline",
            {"message": user_message},
            {
                "prospect_id": prospect.id,
                "fit_score": research.fit_score,
                "outreach_draft_id": draft.id,
            },
        )

        return {
            "research": research,
            "outreach": outreach,
            "prospect": prospect,
            "draft": draft,
        }

    async def _run_marketing_pipeline(
        self,
        *,
        user_message: str,
        conversation_id: int,
        clinic_memory: dict,
        trace: RunTrace,
    ) -> dict | None:
        if not settings.enable_marketing:
            return None

        from app.agents.marketing_content_agent import run_marketing_content
        from app.agents.marketing_strategist_agent import run_marketing_strategist

        pain_points = clinic_memory.get("open_support_issues") or clinic_memory.get("growth_signals") or [
            "manual reminder workflows",
            "billing follow-up delays",
        ]

        strategist = await run_marketing_strategist(
            user_message=user_message,
            audience="clinic managers and front desk leads",
            pain_points=[point[:120] for point in pain_points][:3],
        )

        content = await run_marketing_content(
            audience="clinic managers and front desk leads",
            objective="Increase appointment utilization and qualified clinic growth demand",
            pain_points=[point[:120] for point in pain_points][:3],
        )

        campaign_draft = self.draft_repo.create_campaign_draft(
            conversation_id=conversation_id,
            title=content.title,
            audience=content.audience,
            channel=content.channel,
            brief=f"{content.brief}\n\nStrategy note: {strategist.recommendation}",
            nurture_sequence=content.nurture_sequence,
        )

        trace.add(
            "marketing_pipeline",
            {"pain_points": pain_points[:3]},
            {"campaign_draft_id": campaign_draft.id},
        )

        return {
            "strategist": strategist,
            "content": content,
            "campaign_draft": campaign_draft,
        }

    def _build_task_packet(
        self,
        *,
        track: str,
        agent_name: str,
        summary: str,
        assumptions: list[str],
        unresolved_info: list[str],
        escalation_recommended: bool,
        memory_updates: dict,
    ) -> dict:
        return {
            "track": track,
            "agent": agent_name,
            "summary": summary,
            "assumptions": assumptions,
            "unresolved_info": unresolved_info,
            "escalation_recommended": escalation_recommended,
            "memory_updates": memory_updates,
        }

    async def process_message(self, conversation_id: int, user_message: str) -> ChatMessageResponse:
        conversation = self.conversation_repo.get_conversation_with_context(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        control = self.control_service.get_or_create_control(conversation_id)
        system_control = self.control_service.get_or_create_system_control()
        if not self.control_service.to_read(control, system_control).workspace_available:
            raise HTTPException(
                status_code=423,
                detail=self.control_service.workspace_message(control, system_control)
                or "Practice Desk is temporarily unavailable right now.",
            )

        self.conversation_repo.add_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=user_message,
        )

        conversation = self.conversation_repo.get_conversation_with_context(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        active_escalation = self.escalation_service.get_active_escalation(conversation_id)
        if active_escalation:
            self.conversation_repo.update_conversation_state(
                conversation,
                status="escalated",
                active_workflow=str(WorkflowType.HUMAN_ESCALATION),
                active_agent="human_support_queue" if active_escalation.status == "open" else "human_support_agent",
                human_requested=True,
                escalation_recommended=True,
                updated_at=db_models.utc_now(),
            )
            return ChatMessageResponse(
                conversation_id=conversation_id,
                assistant_message="",
                active_workflow=WorkflowType.HUMAN_ESCALATION,
                active_agent="human_support_queue" if active_escalation.status == "open" else "human_support_agent",
                intent=IntentType.HUMAN_ESCALATION,
                confidence=1.0,
                handoff=None,
                escalation_recommended=True,
                human_requested=True,
                escalation_id=active_escalation.id,
                escalation_summary=active_escalation.summary,
                review_required=False,
                drafts_created=[],
                loop_count=conversation.loop_count,
                unresolved_turn_count=conversation.unresolved_turn_count,
            )

        clinic_memory = self.case_service.build_clinic_memory(conversation).model_dump()
        human_requested = explicit_human_request(user_message)
        frustration = detect_frustration(user_message)

        triage = await run_triage(
            user_message=user_message,
            active_workflow=conversation.active_workflow,
            unresolved_turn_count=conversation.unresolved_turn_count,
            loop_count=conversation.loop_count,
        )
        decision = decide_routing(triage, conversation.active_workflow, human_requested)

        active_workflow = decision.workflow
        active_agent = decision.agent
        response_text = ""
        confidence = decision.confidence
        resolved = True
        agent_requested_escalation = False
        escalation_reason = None
        review_required = False
        handoff: HandoffInfo | None = None
        drafts_created: list[DraftRef] = []
        escalation_id: int | None = None
        escalation_summary: str | None = None
        task_packets: list[dict] = []

        trace = RunTrace(agent_name=str(active_agent), workflow=str(active_workflow))

        if decision.agent == AgentType.HUMAN_ESCALATION:
            escalation_reason = (
                "User requested human support"
                if human_requested
                else "Frustration detected and human support recommended"
            )
            escalation_summary = self.escalation_service.create_summary(conversation_id, escalation_reason)
            escalation = self.escalation_service.create_escalation(
                conversation_id=conversation_id,
                reason=escalation_reason,
                summary=escalation_summary,
                created_by_agent=AgentType.TRIAGE,
            )
            escalation_id = escalation.id
            resolved = False
            agent_requested_escalation = True
            confidence = 0.99
            trace.add("create_escalation", {"reason": escalation_reason}, {"escalation_id": escalation_id})
            task_packets.append(
                self._build_task_packet(
                    track="support",
                    agent_name=str(AgentType.HUMAN_ESCALATION),
                    summary="A human support escalation has been created with the current clinic context and unresolved issue summary.",
                    assumptions=[],
                    unresolved_info=["Human specialist review required."],
                    escalation_recommended=True,
                    memory_updates={},
                )
            )

        else:
            support = await run_support(
                user_message=user_message,
                unresolved_turn_count=conversation.unresolved_turn_count,
                clinic_memory=clinic_memory,
            )
            confidence = support.confidence
            resolved = support.resolved
            agent_requested_escalation = support.escalation_recommended
            escalation_reason = support.escalation_reason

            trace.add(
                "support_response",
                {"message": user_message},
                {
                    "confidence": support.confidence,
                    "resolved": support.resolved,
                },
            )

            task_packets.append(
                self._build_task_packet(
                    track="support",
                    agent_name=str(AgentType.SUPPORT),
                    summary=support.answer,
                    assumptions=support.assumptions,
                    unresolved_info=support.unresolved_info,
                    escalation_recommended=support.escalation_recommended,
                    memory_updates=support.memory_updates,
                )
            )

        loop_state = update_loop_state(
            user_message=user_message,
            last_issue_fingerprint=conversation.last_issue_fingerprint,
            current_loop_count=conversation.loop_count,
            unresolved_turn_count=conversation.unresolved_turn_count,
            resolved=resolved,
        )

        escalation_recommended = should_trigger_escalation(
            human_requested=human_requested,
            unresolved_turn_count=loop_state["unresolved_turn_count"],
            loop_count=loop_state["loop_count"],
            confidence=confidence,
            frustration_score=frustration["frustration_score"],
            agent_requested=agent_requested_escalation,
            tool_conflict=False,
        )

        if human_requested and escalation_recommended and escalation_id is None and (
            active_workflow == WorkflowType.SUPPORT or "support" in triage.detected_tracks
        ):
            escalation_reason = escalation_reason or "Support flow unresolved or low confidence"
            escalation_summary = self.escalation_service.create_summary(conversation_id, escalation_reason)
            escalation = self.escalation_service.create_escalation(
                conversation_id=conversation_id,
                reason=escalation_reason,
                summary=escalation_summary,
                created_by_agent=str(active_agent),
            )
            escalation_id = escalation.id
            active_workflow = WorkflowType.HUMAN_ESCALATION
            active_agent = AgentType.HUMAN_ESCALATION

        response_result = await run_copilot_response(
            user_message=user_message,
            conversation_messages=conversation.messages,
            clinic_memory=clinic_memory,
            task_packets=task_packets,
            review_required=review_required,
            drafts_created=drafts_created,
            escalation_recommended=escalation_recommended,
            escalation_reason=escalation_reason,
            escalation_summary=escalation_summary,
            human_requested=human_requested,
            active_workflow=str(active_workflow),
            active_agent=str(active_agent),
            confidence=confidence,
            loop_count=loop_state["loop_count"],
            unresolved_turn_count=loop_state["unresolved_turn_count"],
        )
        response_text = response_result.response
        trace.add(
            "copilot_response",
            {
                "task_count": len(task_packets),
                "review_required": review_required,
                "escalation_recommended": escalation_recommended,
            },
            {"mode": response_result.mode},
        )

        conversation_title = conversation.title
        if not conversation_title or conversation_title.strip() in {"ClinicOS AI Conversation", "ClinicOS AI Chat"}:
            first_line = user_message.strip().splitlines()[0] if user_message.strip() else ""
            conversation_title = first_line[:72] if first_line else "ClinicOS AI Chat"

        self.conversation_repo.add_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=response_text,
            agent_name=str(active_agent),
            workflow=str(active_workflow),
            confidence=confidence,
            meta_json={
                "handoff": asdict(handoff) if handoff else None,
                "review_required": review_required,
                "escalation_recommended": escalation_recommended,
                "detected_tracks": triage.detected_tracks,
                "task_packets": task_packets,
                "response_mode": response_result.mode,
                "sender_type": "ai",
            },
        )

        self.conversation_repo.add_run_log(
            conversation_id=conversation_id,
            agent_name=str(active_agent),
            workflow=str(active_workflow),
            input_text=user_message,
            output_text=response_text,
            confidence=confidence,
            handoff_to=handoff.to_agent if handoff else None,
            escalation_recommended=escalation_recommended,
            tool_trace_json=trace.as_json(),
        )

        self.conversation_repo.update_conversation_state(
            conversation,
            title=conversation_title,
            active_workflow=str(active_workflow),
            active_agent=str(active_agent),
            loop_count=loop_state["loop_count"],
            unresolved_turn_count=loop_state["unresolved_turn_count"],
            escalation_recommended=escalation_recommended,
            human_requested=human_requested,
            last_issue_fingerprint=loop_state["last_issue_fingerprint"],
            last_agent_confidence=confidence,
        )

        log_agent_event(
            agent=str(active_agent),
            workflow=str(active_workflow),
            mode="orchestrated",
            detail={
                "conversation_id": conversation_id,
                "intent": str(decision.intent),
                "confidence": confidence,
                "review_required": review_required,
                "escalation_recommended": escalation_recommended,
            },
        )

        return ChatMessageResponse(
            conversation_id=conversation_id,
            assistant_message=response_text,
            active_workflow=active_workflow,
            active_agent=active_agent,
            intent=decision.intent,
            confidence=confidence,
            handoff=handoff,
            escalation_recommended=escalation_recommended,
            human_requested=human_requested,
            escalation_id=escalation_id,
            escalation_summary=escalation_summary,
            review_required=review_required,
            drafts_created=drafts_created,
            loop_count=loop_state["loop_count"],
            unresolved_turn_count=loop_state["unresolved_turn_count"],
        )
