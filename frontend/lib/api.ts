import {
  CaseSnapshot,
  CampaignDraft,
  ChatResponse,
  Conversation,
  ConversationDeletion,
  ConversationSummary,
  DeleteResult,
  Escalation,
  HumanSupportQueueItem,
  OpenAIHealth,
  OutreachDraft,
  ReviewQueueItem,
  SalesResearchHistoryItem,
  SalesResearchResponse
} from "@/lib/types";
import { getApiBaseUrl } from "@/lib/env";

const API_BASE = getApiBaseUrl();

function buildApiUrl(path: string) {
  return API_BASE ? `${API_BASE}${path}` : path;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${body}`);
  }

  return (await response.json()) as T;
}

export const api = {
  startConversation(options?: { openingMessage?: string; userName?: string; userEmail?: string }) {
    return request<Conversation>("/api/chat/start", {
      method: "POST",
      body: JSON.stringify({
        user_name: options?.userName ?? "Practice Manager",
        user_email: options?.userEmail ?? "manager@clinicos.app",
        opening_message: options?.openingMessage ?? null
      })
    });
  },
  listConversations(userEmail = "manager@clinicos.app", limit = 25) {
    const params = new URLSearchParams({
      user_email: userEmail,
      limit: String(limit)
    });
    return request<ConversationSummary[]>(`/api/chat/conversations?${params.toString()}`);
  },
  sendMessage(conversationId: number, message: string) {
    return request<ChatResponse>("/api/chat/message", {
      method: "POST",
      body: JSON.stringify({ conversation_id: conversationId, message })
    });
  },
  getConversation(conversationId: number) {
    return request<Conversation>(`/api/chat/${conversationId}`);
  },
  getCaseSnapshot(conversationId: number) {
    return request<CaseSnapshot>(`/api/chat/${conversationId}/case`);
  },
  updateConversationControls(conversationId: number, payload: { active_chat_enabled?: boolean; global_agent_enabled?: boolean }) {
    return request<{
      active_chat_enabled: boolean;
      global_agent_enabled: boolean;
      workspace_available: boolean;
      admin_message?: string | null;
      updated_at?: string | null;
      global_updated_at?: string | null;
    }>(
      `/api/chat/${conversationId}/controls`,
      {
        method: "PUT",
        body: JSON.stringify(payload)
      }
    );
  },
  updatePracticeProfile(
    conversationId: number,
    payload: {
      clinic_name?: string | null;
      practice_type?: string | null;
      location?: string | null;
      providers?: number | null;
      front_desk_staff_count?: number | null;
      pms_software?: string | null;
      insurance_billing_status?: string | null;
    }
  ) {
    return request<CaseSnapshot>(`/api/chat/${conversationId}/profile`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },
  deleteConversation(conversationId: number, deletedBy: "user" | "admin") {
    const params = new URLSearchParams({ deleted_by: deletedBy });
    return request<ConversationDeletion>(`/api/chat/${conversationId}?${params.toString()}`, {
      method: "DELETE"
    });
  },
  listDeletedConversationArchive(limit = 50) {
    const params = new URLSearchParams({ limit: String(limit) });
    return request<ConversationDeletion[]>(`/api/chat/deleted/archive?${params.toString()}`);
  },
  getOpenAIHealth() {
    return request<OpenAIHealth>("/api/health/openai");
  },
  talkToHuman(conversationId: number) {
    return request<Escalation>(`/api/support/${conversationId}/talk-to-human`, { method: "POST" });
  },
  getHumanSupportStatus(conversationId: number) {
    return request<HumanSupportQueueItem>(`/api/support/${conversationId}/status`);
  },
  listHumanSupportQueue() {
    return request<HumanSupportQueueItem[]>("/api/support/queue");
  },
  takeOverHumanSupport(conversationId: number) {
    return request<HumanSupportQueueItem>(`/api/support/${conversationId}/take-over`, {
      method: "POST"
    });
  },
  replyToHumanSupport(conversationId: number, message: string, responderName = "Human Support") {
    return request<Conversation["messages"][number]>(`/api/support/${conversationId}/reply`, {
      method: "POST",
      body: JSON.stringify({
        message,
        responder_name: responderName
      })
    });
  },
  listEscalations() {
    return request<Escalation[]>("/api/escalations");
  },
  salesResearch(clinicName: string, location?: string) {
    return request<SalesResearchResponse>("/api/sales/research", {
      method: "POST",
      body: JSON.stringify({ clinic_name: clinicName, location })
    });
  },
  listSalesResearchHistory() {
    return request<SalesResearchHistoryItem[]>("/api/sales/history");
  },
  deleteSalesResearchHistory(id: number) {
    return request<DeleteResult>(`/api/sales/history/${id}`, {
      method: "DELETE"
    });
  },
  listOutreachDrafts() {
    return request<OutreachDraft[]>("/api/sales/drafts");
  },
  approveOutreach(id: number, reviewer = "Ops Reviewer", notes?: string) {
    return request<OutreachDraft>(`/api/sales/drafts/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ reviewer_name: reviewer, notes })
    });
  },
  rejectOutreach(id: number, reviewer = "Ops Reviewer", notes?: string) {
    return request<OutreachDraft>(`/api/sales/drafts/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ reviewer_name: reviewer, notes })
    });
  },
  generateMarketing(audience: string, objective: string, segmentNotes?: string) {
    return request<CampaignDraft>("/api/marketing/generate", {
      method: "POST",
      body: JSON.stringify({
        audience,
        objective,
        segment_notes: segmentNotes
      })
    });
  },
  listCampaignDrafts() {
    return request<CampaignDraft[]>("/api/marketing/drafts");
  },
  deleteMarketingPlan(id: number) {
    return request<DeleteResult>(`/api/marketing/plans/${id}`, {
      method: "DELETE"
    });
  },
  approveCampaign(id: number, reviewer = "Marketing Lead", notes?: string) {
    return request<CampaignDraft>(`/api/marketing/drafts/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ reviewer_name: reviewer, notes })
    });
  },
  rejectCampaign(id: number, reviewer = "Marketing Lead", notes?: string) {
    return request<CampaignDraft>(`/api/marketing/drafts/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ reviewer_name: reviewer, notes })
    });
  },
  getReviewQueue() {
    return request<ReviewQueueItem[]>("/api/review/queue");
  }
};
