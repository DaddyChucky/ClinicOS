from __future__ import annotations

import re
from datetime import datetime, timezone

from app.models import db_models
from app.models.enums import DraftStatus
from app.models.schemas import (
    CaseSnapshotRead,
    CaseTaskRead,
    CaseTimelineEventRead,
    ClinicMemoryRead,
)


class CaseService:
    _PMS_SOFTWARE = ["dentrix", "eaglesoft", "opendental", "open dental", "athena", "eclinicalworks", "epic"]

    def build_case_snapshot(self, conversation: db_models.Conversation) -> CaseSnapshotRead:
        memory = self.build_clinic_memory(conversation)
        tasks = self._build_tasks(conversation, memory)
        timeline = self._build_timeline(conversation)
        intent_mix = [task.track for task in tasks if task.track in {"support", "sales", "marketing"}]
        case_status = self._case_status(conversation, tasks)

        title = conversation.title or self._derive_case_title(conversation)
        recommendations = self._recommend_next_actions(conversation, tasks, memory)

        return CaseSnapshotRead(
            conversation_id=conversation.id,
            case_id=f"CASE-{conversation.id:04d}",
            title=title,
            status=case_status,
            intent_mix=intent_mix,
            recommended_next_actions=recommendations,
            tasks=tasks,
            timeline=timeline,
            clinic_memory=memory,
        )

    def build_clinic_memory(self, conversation: db_models.Conversation) -> ClinicMemoryRead:
        user_messages = [m.content for m in conversation.messages if m.role == "user"]
        combined = " ".join(user_messages).lower()
        memory_updates = self._collect_memory_updates(conversation)
        profile_override = conversation.profile_override

        prospects = sorted(conversation.prospects, key=lambda item: item.updated_at, reverse=True)
        campaigns = sorted(conversation.campaign_drafts, key=lambda item: item.updated_at, reverse=True)
        latest_prospect = prospects[0] if prospects else None
        latest_campaign = campaigns[0] if campaigns else None

        clinic_name = self._preferred_value(
            profile_override.clinic_name if profile_override else None,
            memory_updates.get("clinic_name")
            or (latest_prospect.clinic_name if latest_prospect else None)
            or self._extract_clinic_name(user_messages),
        )
        practice_type = self._preferred_value(
            profile_override.practice_type if profile_override else None,
            memory_updates.get("practice_type")
            or (latest_prospect.specialty if latest_prospect and latest_prospect.specialty else None)
            or (latest_prospect.clinic_type if latest_prospect else None)
            or self._extract_practice_type(combined),
        )
        location = self._preferred_value(
            profile_override.location if profile_override else None,
            memory_updates.get("location")
            or (latest_prospect.location if latest_prospect else None)
            or self._extract_location(combined),
        )

        locations = self._preferred_value(
            profile_override.locations if profile_override else None,
            self._coerce_int(memory_updates.get("locations"))
            or self._extract_count(
            combined,
            patterns=[
                r"(\d+)\s+locations?",
                r"(\d+)\s+offices?",
            ],
        ),
        )
        if locations is None and "second location" in combined:
            locations = 2

        providers = self._preferred_value(
            profile_override.providers if profile_override else None,
            self._coerce_int(memory_updates.get("providers"))
            or self._extract_count(
            combined,
            patterns=[
                r"(\d+)\s+providers?",
                r"(\d+)\s+doctors?",
                r"(\d+)\s+clinicians?",
            ],
        ),
        )
        front_desk_staff_count = self._preferred_value(
            profile_override.front_desk_staff_count if profile_override else None,
            self._coerce_int(memory_updates.get("front_desk_staff_count"))
            or self._extract_count(
            combined,
            patterns=[
                r"(\d+)\s+front[-\s]?desk",
                r"(\d+)\s+reception",
            ],
        ),
        )

        pms_software = self._preferred_value(
            profile_override.pms_software if profile_override else None,
            memory_updates.get("pms_software") or self._extract_pms(combined),
        )
        insurance_billing_status = self._preferred_value(
            profile_override.insurance_billing_status if profile_override else None,
            memory_updates.get("insurance_billing_status") or self._extract_insurance_status(combined),
        )

        open_support_issues = self._dedupe(memory_updates["open_support_issues"] + self._open_support_issues(user_messages, conversation))[:4]
        growth_signals = self._dedupe(memory_updates["growth_signals"] + self._growth_signals(user_messages, conversation))[:4]
        prior_sales = self._dedupe(memory_updates["prior_sales_interactions"] + self._prior_sales_interactions(conversation))[:5]
        marketing_history = self._dedupe(
            memory_updates["marketing_engagement_history"] + self._marketing_history(conversation)
        )[:5]
        active_tasks = self._active_tasks(conversation)
        unresolved_blockers = self._dedupe(memory_updates["unresolved_blockers"] + self._unresolved_blockers(conversation))
        response_preferences = self._response_preferences(user_messages, memory_updates["response_preferences"])

        if latest_campaign and not marketing_history:
            marketing_history = [f"{latest_campaign.title} ({latest_campaign.status})"]

        known_profile_fields, missing_profile_fields = self._profile_field_state(
            clinic_name=clinic_name,
            practice_type=practice_type,
            location=location,
            providers=providers,
            front_desk_staff_count=front_desk_staff_count,
            pms_software=pms_software,
            insurance_billing_status=insurance_billing_status,
        )

        return ClinicMemoryRead(
            clinic_name=clinic_name,
            practice_type=practice_type,
            location=location,
            locations=locations,
            providers=providers,
            front_desk_staff_count=front_desk_staff_count,
            pms_software=pms_software,
            insurance_billing_status=insurance_billing_status,
            open_support_issues=open_support_issues,
            growth_signals=growth_signals,
            prior_sales_interactions=prior_sales,
            marketing_engagement_history=marketing_history,
            active_tasks=active_tasks,
            unresolved_blockers=unresolved_blockers,
            response_preferences=response_preferences,
            known_profile_fields=known_profile_fields,
            missing_profile_fields=missing_profile_fields,
            profile_completion_score=int(round((len(known_profile_fields) / 7) * 100)),
        )

    def _build_tasks(
        self,
        conversation: db_models.Conversation,
        memory: ClinicMemoryRead,
    ) -> list[CaseTaskRead]:
        tasks: list[CaseTaskRead] = []
        now = conversation.updated_at or datetime.now(timezone.utc)
        sorted_prospects = sorted(conversation.prospects, key=lambda item: item.updated_at, reverse=True)
        sorted_campaigns = sorted(conversation.campaign_drafts, key=lambda item: item.updated_at, reverse=True)

        support_runs = sorted(
            [run for run in conversation.runs if run.workflow == "support"],
            key=lambda item: item.created_at,
        )
        if support_runs or memory.open_support_issues:
            latest_support = support_runs[-1] if support_runs else None
            blocked_reason = None
            if conversation.escalation_recommended:
                blocked_reason = "Escalated for human review"
            elif memory.unresolved_blockers:
                blocked_reason = memory.unresolved_blockers[0]

            status = "completed"
            if blocked_reason:
                status = "blocked"
            elif conversation.active_workflow == "support":
                status = "in_progress"

            summary = (
                self._first_sentence(latest_support.output_text)
                if latest_support
                else "Support intake captured and waiting for additional context."
            )
            tasks.append(
                CaseTaskRead(
                    task_id=f"{conversation.id}-support",
                    track="support",
                    agent=latest_support.agent_name if latest_support else "support_agent",
                    status=status,
                    summary=summary,
                    needs_human_review=bool(blocked_reason),
                    blocked_reason=blocked_reason,
                    updated_at=latest_support.created_at if latest_support else now,
                )
            )

        sales_runs = sorted(
            [run for run in conversation.runs if run.workflow == "sales"],
            key=lambda item: item.created_at,
        )
        if sales_runs or conversation.prospects or conversation.outreach_drafts:
            latest_sales = sales_runs[-1] if sales_runs else None
            pending = any(d.status == DraftStatus.PENDING_REVIEW for d in conversation.outreach_drafts)
            status = "completed"
            if pending:
                status = "review_required"
            elif conversation.active_workflow == "sales":
                status = "in_progress"

            summary = (
                sorted_prospects[0].research_summary
                if sorted_prospects and sorted_prospects[0].research_summary
                else "Prospect profile and outreach positioning have been prepared."
            )
            tasks.append(
                CaseTaskRead(
                    task_id=f"{conversation.id}-sales",
                    track="sales",
                    agent=latest_sales.agent_name if latest_sales else "sales_research_agent",
                    status=status,
                    summary=self._truncate(summary, 190),
                    needs_human_review=pending,
                    blocked_reason=None,
                    updated_at=latest_sales.created_at if latest_sales else now,
                )
            )

        marketing_runs = sorted(
            [run for run in conversation.runs if run.workflow == "marketing"],
            key=lambda item: item.created_at,
        )
        if marketing_runs or conversation.campaign_drafts:
            latest_marketing = marketing_runs[-1] if marketing_runs else None
            pending = any(d.status == DraftStatus.PENDING_REVIEW for d in conversation.campaign_drafts)
            status = "completed"
            if pending:
                status = "review_required"
            elif conversation.active_workflow == "marketing":
                status = "in_progress"

            summary = (
                f"{sorted_campaigns[0].title}: {self._first_sentence(sorted_campaigns[0].brief)}"
                if sorted_campaigns
                else "Campaign planning is underway."
            )
            tasks.append(
                CaseTaskRead(
                    task_id=f"{conversation.id}-marketing",
                    track="marketing",
                    agent=latest_marketing.agent_name if latest_marketing else "marketing_content_agent",
                    status=status,
                    summary=self._truncate(summary, 190),
                    needs_human_review=pending,
                    blocked_reason=None,
                    updated_at=latest_marketing.created_at if latest_marketing else now,
                )
            )

        if not tasks:
            tasks.append(
                CaseTaskRead(
                    task_id=f"{conversation.id}-triage",
                    track="triage",
                    agent="triage_agent",
                    status="in_progress",
                    summary="ClinicOS AI is routing the request and preparing the next workstream.",
                    needs_human_review=False,
                    blocked_reason=None,
                    updated_at=now,
                )
            )
        return tasks

    def _build_timeline(self, conversation: db_models.Conversation) -> list[CaseTimelineEventRead]:
        events: list[CaseTimelineEventRead] = [
            CaseTimelineEventRead(
                event_id=f"{conversation.id}-start",
                stage="ClinicOS AI Triage Agent Started",
                detail="ClinicOS AI opened a new Practice Desk conversation and began routing the request.",
                status="live",
                timestamp=conversation.created_at,
            )
        ]

        for event in conversation.event_logs:
            events.append(
                CaseTimelineEventRead(
                    event_id=f"event-{event.id}",
                    stage=event.stage,
                    detail=event.detail,
                    status=event.status,
                    timestamp=event.created_at,
                )
            )

        for run in sorted(conversation.runs, key=lambda item: item.created_at):
            stage = f"{run.workflow.replace('_', ' ').title()} update"
            detail = f"{run.agent_name}: {self._truncate(self._first_sentence(run.output_text), 140)}"
            status = "offline" if run.escalation_recommended else "live"
            events.append(
                CaseTimelineEventRead(
                    event_id=f"run-{run.id}",
                    stage=stage,
                    detail=detail,
                    status=status,
                    timestamp=run.created_at,
                )
            )

        for draft in conversation.outreach_drafts:
            events.append(
                CaseTimelineEventRead(
                    event_id=f"outreach-{draft.id}",
                    stage="Sales task created",
                    detail=f"Outreach draft #{draft.id} is {draft.status}.",
                    status="live" if draft.review_required else "live",
                    timestamp=draft.updated_at,
                )
            )

        for draft in conversation.campaign_drafts:
            events.append(
                CaseTimelineEventRead(
                    event_id=f"campaign-{draft.id}",
                    stage="Marketing task created",
                    detail=f"Campaign draft #{draft.id} is {draft.status}.",
                    status="live" if draft.review_required else "live",
                    timestamp=draft.updated_at,
                )
            )

        for escalation in conversation.escalations:
            events.append(
                CaseTimelineEventRead(
                    event_id=f"escalation-{escalation.id}",
                    stage="Escalated for human review",
                    detail=escalation.reason,
                    status="offline",
                    timestamp=escalation.created_at,
                )
            )

        if conversation.unresolved_turn_count > 0 and not conversation.escalations:
            events.append(
                CaseTimelineEventRead(
                    event_id=f"{conversation.id}-unresolved",
                    stage="Waiting for more information",
                    detail="ClinicOS AI needs additional context to close one or more tasks.",
                    status="offline",
                    timestamp=conversation.updated_at,
                )
            )

        return sorted(events, key=lambda item: item.timestamp, reverse=True)

    def _derive_case_title(self, conversation: db_models.Conversation) -> str:
        first_user = next((msg.content for msg in conversation.messages if msg.role == "user"), "")
        if first_user:
            return self._truncate(first_user.strip(), 72)
        return f"Practice Desk Chat #{conversation.id}"

    def _case_status(self, conversation: db_models.Conversation, tasks: list[CaseTaskRead]) -> str:
        if any(task.status == "blocked" for task in tasks):
            return "blocked"
        if any(task.status == "review_required" for task in tasks):
            return "review_required"
        if conversation.active_workflow in {"support", "sales", "marketing", "triage"}:
            return "in_progress"
        return "open"

    def _recommend_next_actions(
        self,
        conversation: db_models.Conversation,
        tasks: list[CaseTaskRead],
        memory: ClinicMemoryRead,
    ) -> list[str]:
        actions: list[str] = []
        if any(task.status == "blocked" for task in tasks):
            actions.append("Assign a specialist to the blocked support chat.")
        if any(task.status == "review_required" for task in tasks):
            actions.append("Review pending sales/marketing drafts in the Review queue.")
        if memory.unresolved_blockers:
            actions.append("Share missing logs or screenshots to unblock troubleshooting.")
        if memory.missing_profile_fields:
            actions.append(
                f"Add {memory.missing_profile_fields[0].lower()} so ClinicOS AI can personalize the next recommendation."
            )
        if not actions:
            actions.append("Continue the Practice Desk chat to refine execution details.")
        return actions

    def _collect_memory_updates(self, conversation: db_models.Conversation) -> dict[str, list[str] | str | None]:
        memory: dict[str, list[str] | str | None] = {
            "clinic_name": None,
            "practice_type": None,
            "location": None,
            "locations": None,
            "providers": None,
            "front_desk_staff_count": None,
            "pms_software": None,
            "insurance_billing_status": None,
            "open_support_issues": [],
            "growth_signals": [],
            "prior_sales_interactions": [],
            "marketing_engagement_history": [],
            "unresolved_blockers": [],
            "response_preferences": [],
        }
        single_value_keys = {
            "clinic_name",
            "practice_type",
            "location",
            "locations",
            "providers",
            "front_desk_staff_count",
            "pms_software",
            "insurance_billing_status",
        }
        list_key_map = {
            "open_support_issue": "open_support_issues",
            "support_issue": "open_support_issues",
            "growth_signal": "growth_signals",
            "prior_sales_interaction": "prior_sales_interactions",
            "marketing_activity": "marketing_engagement_history",
            "unresolved_blocker": "unresolved_blockers",
            "response_preference": "response_preferences",
        }

        for message in sorted(conversation.messages, key=lambda item: item.created_at):
            if message.role != "assistant" or not message.meta_json:
                continue
            task_packets = message.meta_json.get("task_packets", [])
            if not isinstance(task_packets, list):
                continue
            for packet in task_packets:
                if not isinstance(packet, dict):
                    continue
                updates = packet.get("memory_updates", {})
                if not isinstance(updates, dict):
                    continue
                for key, value in updates.items():
                    normalized_key = str(key).strip()
                    if not normalized_key:
                        continue
                    if normalized_key in single_value_keys:
                        if value not in (None, ""):
                            memory[normalized_key] = str(value)
                        continue

                    list_key = normalized_key if normalized_key in memory else list_key_map.get(normalized_key)
                    if not list_key or not isinstance(memory.get(list_key), list):
                        continue
                    items = value if isinstance(value, list) else [value]
                    stored_items = memory[list_key]
                    assert isinstance(stored_items, list)
                    for item in items:
                        cleaned = str(item).strip()
                        if cleaned:
                            stored_items.append(cleaned)

        for key, value in memory.items():
            if isinstance(value, list):
                memory[key] = self._dedupe(value)
        return memory

    def _extract_practice_type(self, combined_text: str) -> str | None:
        mappings = {
            "orthodont": "Orthodontics",
            "dental": "General Dentistry",
            "dermatology": "Dermatology",
            "medical": "General Medical",
            "pediatric": "Pediatrics",
        }
        for keyword, label in mappings.items():
            if keyword in combined_text:
                return label
        return None

    def _extract_clinic_name(self, user_messages: list[str]) -> str | None:
        for message in user_messages:
            quoted = re.findall(r'"([^"]+)"', message)
            if quoted:
                return quoted[0]
            match = re.search(r"(?:for|at)\s+([A-Z][A-Za-z0-9\s&\-]{4,60})", message)
            if match:
                return match.group(1).strip()
        return None

    def _extract_location(self, combined_text: str) -> str | None:
        match = re.search(r"(?:in|near|around)\s+([A-Z][A-Za-z\s]{2,40})", combined_text, re.IGNORECASE)
        if match:
            return match.group(1).strip().title()
        return None

    def _extract_count(self, combined_text: str, patterns: list[str]) -> int | None:
        for pattern in patterns:
            match = re.search(pattern, combined_text)
            if match:
                return int(match.group(1))
        return None

    def _coerce_int(self, value: str | None) -> int | None:
        if value is None:
            return None
        match = re.search(r"\d+", str(value))
        if match:
            return int(match.group(0))
        return None

    def _preferred_value(self, override_value: object, fallback_value: object):
        if override_value not in (None, ""):
            return override_value
        return fallback_value

    def _extract_pms(self, combined_text: str) -> str | None:
        for value in self._PMS_SOFTWARE:
            if value in combined_text:
                return "OpenDental" if value == "open dental" else value.title()
        return None

    def _extract_insurance_status(self, combined_text: str) -> str | None:
        if "claim" in combined_text and any(word in combined_text for word in ("delay", "stuck", "sync", "failed")):
            return "Claims delayed / sync issue"
        if "billing" in combined_text and "stable" in combined_text:
            return "Billing stable"
        if "insurance" in combined_text:
            return "Insurance workflow active"
        return None

    def _open_support_issues(
        self,
        user_messages: list[str],
        conversation: db_models.Conversation,
    ) -> list[str]:
        issue_keywords = ("billing", "claim", "sync", "error", "integration", "invoice", "help", "login")
        issues = [
            self._truncate(message.strip(), 120)
            for message in user_messages
            if any(keyword in message.lower() for keyword in issue_keywords)
        ]
        if conversation.escalations:
            issues.append(conversation.escalations[0].reason)
        return self._dedupe(issues)[:4]

    def _growth_signals(
        self,
        user_messages: list[str],
        conversation: db_models.Conversation,
    ) -> list[str]:
        growth_keywords = ("second location", "new location", "fill", "campaign", "invisalign", "implants", "growth")
        signals = [
            self._truncate(message.strip(), 120)
            for message in user_messages
            if any(keyword in message.lower() for keyword in growth_keywords)
        ]
        for prospect in conversation.prospects:
            if prospect.research_summary:
                signals.append(self._truncate(prospect.research_summary, 120))
        return self._dedupe(signals)[:4]

    def _prior_sales_interactions(self, conversation: db_models.Conversation) -> list[str]:
        notes: list[str] = []
        for prospect in conversation.prospects:
            score = f"fit {int(prospect.fit_score)}/100" if prospect.fit_score is not None else "fit pending"
            notes.append(f"{prospect.clinic_name}: {score}")
        for draft in conversation.outreach_drafts:
            notes.append(f"Outreach #{draft.id} ({draft.status})")
        return self._dedupe(notes)[:5]

    def _marketing_history(self, conversation: db_models.Conversation) -> list[str]:
        history = [f"{draft.title} ({draft.status})" for draft in conversation.campaign_drafts]
        return self._dedupe(history)[:5]

    def _active_tasks(self, conversation: db_models.Conversation) -> list[str]:
        tasks: list[str] = [f"Current workflow: {conversation.active_workflow}"]
        if any(d.review_required for d in conversation.outreach_drafts):
            tasks.append("Sales outreach draft awaiting human review")
        if any(d.review_required for d in conversation.campaign_drafts):
            tasks.append("Marketing campaign draft awaiting human review")
        if conversation.escalation_recommended:
            tasks.append("Human escalation requested")
        return self._dedupe(tasks)

    def _unresolved_blockers(self, conversation: db_models.Conversation) -> list[str]:
        blockers = [escalation.reason for escalation in conversation.escalations]
        if conversation.unresolved_turn_count > 0:
            blockers.append(f"{conversation.unresolved_turn_count} unresolved support turn(s)")
        return self._dedupe(blockers)

    def _response_preferences(self, user_messages: list[str], stored_preferences: list[str]) -> list[str]:
        detected = list(stored_preferences)
        preference_patterns = {
            "more concise replies": ["concise", "shorter", "keep it brief"],
            "step-by-step guidance": ["step by step", "walk me through", "click path"],
            "more detailed reasoning": ["more detail", "more detailed", "show your reasoning"],
            "action-oriented recommendations": ["next steps", "action plan", "what should we do next"],
            "patient-facing messaging": ["patient-facing", "send to patients", "patient copy"],
        }
        combined = " ".join(user_messages).lower()
        for label, patterns in preference_patterns.items():
            if any(pattern in combined for pattern in patterns):
                detected.append(label)
        return self._dedupe(detected)[:4]

    def _profile_field_state(self, **values: object) -> tuple[list[str], list[str]]:
        fields = {
            "Clinic name": values.get("clinic_name"),
            "Practice type": values.get("practice_type"),
            "Location": values.get("location"),
            "Providers": values.get("providers"),
            "Front desk staff": values.get("front_desk_staff_count"),
            "PMS software": values.get("pms_software"),
            "Billing status": values.get("insurance_billing_status"),
        }
        known = [label for label, value in fields.items() if value not in (None, "", [])]
        missing = [label for label, value in fields.items() if value in (None, "", [])]
        return known, missing

    def _first_sentence(self, text: str) -> str:
        if not text:
            return ""
        parts = re.split(r"(?<=[.!?])\s+", text.strip())
        return parts[0].strip()

    def _truncate(self, value: str, length: int) -> str:
        cleaned = re.sub(r"\s+", " ", value.strip())
        if len(cleaned) <= length:
            return cleaned
        return f"{cleaned[: length - 3].rstrip()}..."

    def _dedupe(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            key = item.lower().strip()
            if not key or key in seen:
                continue
            seen.add(key)
            result.append(item)
        return result
