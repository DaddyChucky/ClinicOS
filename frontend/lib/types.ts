export type DraftStatus = "pending_review" | "approved" | "rejected";

export interface Message {
  id: number;
  role: "user" | "assistant" | "system";
  content: string;
  agent_name?: string | null;
  workflow?: string | null;
  confidence?: number | null;
  meta_json?: Record<string, unknown> | null;
  created_at: string;
}

export interface Conversation {
  id: number;
  user_id?: number | null;
  title?: string | null;
  status: string;
  active_workflow: string;
  active_agent: string;
  loop_count: number;
  unresolved_turn_count: number;
  escalation_recommended: boolean;
  human_requested: boolean;
  messages: Message[];
}

export interface ConversationSummary {
  id: number;
  title?: string | null;
  updated_at: string;
  last_message_preview?: string | null;
}

export interface DraftRef {
  id: number;
  type: "outreach" | "campaign";
  status: DraftStatus;
}

export interface ChatResponse {
  conversation_id: number;
  assistant_message: string;
  active_workflow: string;
  active_agent: string;
  intent: string;
  confidence: number;
  handoff?: {
    from_agent: string;
    to_agent: string;
    reason: string;
  } | null;
  escalation_recommended: boolean;
  human_requested: boolean;
  escalation_id?: number | null;
  escalation_summary?: string | null;
  review_required: boolean;
  drafts_created: DraftRef[];
  loop_count: number;
  unresolved_turn_count: number;
}

export interface Escalation {
  id: number;
  conversation_id: number;
  summary: string;
  reason: string;
  status: string;
  queue_position?: number | null;
  created_by_agent?: string | null;
  created_at: string;
}

export interface HumanSupportQueueItem {
  escalation_id: number;
  conversation_id: number;
  chat_title: string;
  category: string;
  status: string;
  handoff_stage: "queued" | "reviewing" | "live_chat" | string;
  queue_position?: number | null;
  summary: string;
  summary_points: string[];
  latest_message_preview?: string | null;
  clinic_name?: string | null;
  practice_type?: string | null;
  requested_at: string;
  updated_at: string;
}

export interface Prospect {
  id: number;
  clinic_name: string;
  clinic_type: string;
  specialty?: string | null;
  size_estimate?: string | null;
  location?: string | null;
  existing_lead: boolean;
  fit_score?: number | null;
  pain_points_json?: string[] | null;
  research_summary?: string | null;
}

export interface OutreachDraft {
  id: number;
  prospect_id: number;
  conversation_id?: number | null;
  subject: string;
  body: string;
  tone: string;
  personalization_notes?: string | null;
  status: DraftStatus;
  review_required: boolean;
  created_at: string;
  updated_at: string;
}

export interface SalesResearchResponse {
  prospect: Prospect;
  fit_score: number;
  fit_reasons: string[];
  summary: string;
  outreach_draft: OutreachDraft;
}

export interface SalesResearchHistoryItem {
  id: number;
  clinic_name: string;
  clinic_type: string;
  specialty?: string | null;
  size_estimate?: string | null;
  location?: string | null;
  existing_lead: boolean;
  fit_score?: number | null;
  pain_points_json?: string[] | null;
  research_summary?: string | null;
  outreach_subject: string;
  outreach_body: string;
  personalization_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CampaignDraft {
  id: number;
  conversation_id?: number | null;
  title: string;
  audience: string;
  channel: string;
  brief: string;
  nurture_sequence_json?: Array<Record<string, unknown>> | null;
  status: DraftStatus;
  review_required: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReviewQueueItem {
  entity_type: "outreach" | "campaign";
  draft_id: number;
  conversation_id?: number | null;
  title: string;
  status: DraftStatus;
  review_required: boolean;
  created_at: string;
}

export interface DeleteResult {
  id: number;
  deleted: boolean;
}

export interface ClinicMemory {
  clinic_name?: string | null;
  practice_type?: string | null;
  location?: string | null;
  locations?: number | null;
  providers?: number | null;
  front_desk_staff_count?: number | null;
  pms_software?: string | null;
  insurance_billing_status?: string | null;
  open_support_issues: string[];
  growth_signals: string[];
  prior_sales_interactions: string[];
  marketing_engagement_history: string[];
  active_tasks: string[];
  unresolved_blockers: string[];
  response_preferences: string[];
  known_profile_fields: string[];
  missing_profile_fields: string[];
  profile_completion_score: number;
}

export interface CaseTask {
  task_id: string;
  track: "support" | "sales" | "marketing" | "triage" | string;
  agent: string;
  status: "in_progress" | "review_required" | "blocked" | "completed" | string;
  summary: string;
  needs_human_review: boolean;
  blocked_reason?: string | null;
  updated_at: string;
}

export interface CaseTimelineEvent {
  event_id: string;
  stage: string;
  detail: string;
  status: "completed" | "in_progress" | "blocked" | "review_required" | string;
  timestamp: string;
}

export interface ConversationControls {
  active_chat_enabled: boolean;
  global_agent_enabled: boolean;
  workspace_available: boolean;
  admin_message?: string | null;
  updated_at?: string | null;
  global_updated_at?: string | null;
}

export interface CaseSnapshot {
  conversation_id: number;
  case_id: string;
  title: string;
  status: "in_progress" | "blocked" | "review_required" | "open" | string;
  intent_mix: string[];
  recommended_next_actions: string[];
  tasks: CaseTask[];
  timeline: CaseTimelineEvent[];
  clinic_memory: ClinicMemory;
  controls?: ConversationControls | null;
}

export interface ConversationDeletion {
  id: number;
  conversation_id: number;
  title?: string | null;
  deleted_by: string;
  summary: string;
  snapshot_json?: Record<string, unknown> | null;
  created_at: string;
}

export interface OpenAIHealth {
  status: string;
  sdk_available: boolean;
  api_key_loaded: boolean;
  model: string;
  live_mode_ready: boolean;
  test_call_success: boolean;
  runtime_mode: "live_ai" | "fallback" | string;
  detail?: string | null;
}
