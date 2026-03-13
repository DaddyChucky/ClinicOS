"use client";

import { type FormEvent, type ReactNode, useEffect, useMemo, useRef, useState } from "react";

import { AdminPageSkeleton } from "@/components/admin/AdminPageSkeleton";
import { MessageList } from "@/components/chat/MessageList";
import { PmsInfoButton } from "@/components/profile/PmsInfoButton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { InfoIcon, QueueIcon, SendIcon } from "@/components/ui/icons";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { CaseSnapshot, Conversation, HumanSupportQueueItem } from "@/lib/types";
import { formatDate } from "@/lib/utils";

function categoryVariant(category: string): "default" | "success" | "warning" | "info" {
  if (category === "Marketing") return "warning";
  if (category === "Sales & Outreach") return "success";
  return "info";
}

function stageVariant(stage: string): "warning" | "info" | "success" {
  if (stage === "live_chat") return "success";
  if (stage === "reviewing") return "info";
  return "warning";
}

function stageLabel(stage: string, queuePosition?: number | null) {
  if (stage === "live_chat") return "Live Chat";
  if (stage === "reviewing") return "Agent Reviewing";
  return `Queue #${queuePosition ?? 1}`;
}

function topStatusCopy(item: HumanSupportQueueItem) {
  if (item.handoff_stage === "live_chat") {
    return "A human support agent is connected and chatting with this clinic live right now.";
  }
  if (item.handoff_stage === "reviewing") {
    return "A human support agent is currently reviewing this chat, is now in charge, and will respond promptly.";
  }
  return "ClinicOS AI handed this chat into the human queue and it is still awaiting takeover.";
}

function summaryPoints(item: HumanSupportQueueItem) {
  if (item.summary_points.length > 0) {
    return item.summary_points;
  }
  return [item.summary];
}

function profileValue(value: string | number | null | undefined, emptyLabel = "Not captured yet") {
  if (value === null || value === undefined || value === "") {
    return <span className="text-slate-400">{emptyLabel}</span>;
  }
  return <span className="text-ink">{String(value)}</span>;
}

function ProfileField({
  label,
  value,
  emptyLabel,
  action,
}: {
  label: string;
  value: string | number | null | undefined;
  emptyLabel?: string;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-[22px] border border-slate-200/85 bg-slate-50/75 p-4">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">{label}</p>
        {action}
      </div>
      <p className="mt-2 text-sm font-medium leading-6">{profileValue(value, emptyLabel)}</p>
    </div>
  );
}

export function SupportWorkspace() {
  const [queueItems, setQueueItems] = useState<HumanSupportQueueItem[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [caseSnapshot, setCaseSnapshot] = useState<CaseSnapshot | null>(null);
  const [reply, setReply] = useState("");
  const [guideOpen, setGuideOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [takingOver, setTakingOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const transcriptViewportRef = useRef<HTMLDivElement | null>(null);
  const shouldStickToBottomRef = useRef(true);

  async function loadWorkspace(preferredConversationId?: number | null) {
    const queue = await api.listHumanSupportQueue();
    setQueueItems(queue);

    const nextConversationId =
      preferredConversationId && queue.some((item) => item.conversation_id === preferredConversationId)
        ? preferredConversationId
        : queue[0]?.conversation_id ?? null;

    if (!nextConversationId) {
      setSelectedConversationId(null);
      setConversation(null);
      setCaseSnapshot(null);
      setReply("");
      return;
    }

    const [nextConversation, nextSnapshot] = await Promise.all([
      api.getConversation(nextConversationId),
      api.getCaseSnapshot(nextConversationId),
    ]);
    setSelectedConversationId(nextConversationId);
    setConversation(nextConversation);
    setCaseSnapshot(nextSnapshot);
    if (nextConversationId !== selectedConversationId) {
      setReply("");
    }
  }

  const selectedQueueItem = useMemo(
    () => queueItems.find((item) => item.conversation_id === selectedConversationId) ?? null,
    [queueItems, selectedConversationId]
  );

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      try {
        setLoading(true);
        await loadWorkspace();
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Failed to load the human review queue");
      } finally {
        if (active) setLoading(false);
      }
    }

    bootstrap();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const viewport = transcriptViewportRef.current;
    if (!viewport) return undefined;

    function handleScroll() {
      const node = transcriptViewportRef.current;
      if (!node) return;
      const distanceFromBottom = node.scrollHeight - node.scrollTop - node.clientHeight;
      shouldStickToBottomRef.current = distanceFromBottom < 80;
    }

    handleScroll();
    viewport.addEventListener("scroll", handleScroll, { passive: true });
    return () => {
      viewport.removeEventListener("scroll", handleScroll);
    };
  }, [selectedConversationId]);

  useEffect(() => {
    if (!selectedConversationId) return undefined;
    const interval = window.setInterval(() => {
      loadWorkspace(selectedConversationId).catch(() => null);
    }, 8000);
    return () => {
      window.clearInterval(interval);
    };
  }, [selectedConversationId]);

  useEffect(() => {
    const node = transcriptViewportRef.current;
    if (!node || !shouldStickToBottomRef.current) return;
    node.scrollTo({ top: node.scrollHeight, behavior: "smooth" });
  }, [conversation?.messages.length, sending, selectedQueueItem?.handoff_stage]);

  async function openChat(conversationId: number) {
    if (conversationId === selectedConversationId) return;
    setLoading(true);
    setError(null);
    try {
      await loadWorkspace(conversationId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to open the selected chat");
    } finally {
      setLoading(false);
    }
  }

  async function takeOverChat() {
    if (!selectedConversationId || takingOver) return;
    setTakingOver(true);
    setError(null);
    try {
      await api.takeOverHumanSupport(selectedConversationId);
      await loadWorkspace(selectedConversationId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to take over the selected chat");
    } finally {
      setTakingOver(false);
    }
  }

  async function sendReply(event: FormEvent) {
    event.preventDefault();
    if (!selectedConversationId || !reply.trim()) return;

    setSending(true);
    setError(null);
    try {
      await api.replyToHumanSupport(selectedConversationId, reply.trim(), "Human Support");
      setReply("");
      await loadWorkspace(selectedConversationId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send the human support reply");
    } finally {
      setSending(false);
    }
  }

  if (loading) {
    return <AdminPageSkeleton />;
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[320px_minmax(0,1fr)]">
      <aside className="space-y-4">
        <Card className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Review Queue</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-ink">Human Takeover Queue</h2>
              </div>
              <Badge variant="info">{queueItems.length} Waiting</Badge>
            </div>
            <div className="space-y-3">
              <p className="text-sm leading-6 text-slate-700">
                Practice Desk chats appear here only after a clinic explicitly asks for human support.
              </p>
              <Button variant="secondary" className="w-full sm:w-auto" onClick={() => setGuideOpen(true)}>
                <InfoIcon className="h-4 w-4" />
                How To Use This View
              </Button>
            </div>
          </div>

          <div className="max-h-[560px] space-y-2 overflow-y-auto pr-1">
            {queueItems.length === 0 ? (
              <div className="rounded-[22px] border border-dashed border-slate-200 bg-slate-50/80 p-4 text-sm leading-6 text-slate-500">
                No human takeover requests are waiting right now. New entries only come from Practice Desk after a clinic
                asks to speak with a person.
              </div>
            ) : (
              queueItems.map((item) => {
                const active = item.conversation_id === selectedConversationId;
                return (
                  <button
                    key={item.escalation_id}
                    type="button"
                    onClick={() => openChat(item.conversation_id)}
                    className={`w-full rounded-[22px] border p-4 text-left transition ${
                      active
                        ? "border-emerald-200 bg-[linear-gradient(180deg,rgba(237,252,248,0.98),rgba(255,255,255,0.98))] shadow-[0_18px_40px_rgba(13,118,104,0.12)]"
                        : "border-slate-200/85 bg-white/92 hover:border-slate-300 hover:bg-white"
                    }`}
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant={categoryVariant(item.category)}>{item.category}</Badge>
                      <Badge variant={stageVariant(item.handoff_stage)}>
                        {stageLabel(item.handoff_stage, item.queue_position)}
                      </Badge>
                    </div>
                    <p className="mt-3 line-clamp-2 text-sm font-semibold leading-6 text-ink">{item.chat_title}</p>
                    <p className="line-clamp-2 text-sm leading-6 text-slate-700">
                      {item.latest_message_preview ?? item.summary}
                    </p>
                    <p className="mt-2 text-[11px] uppercase tracking-[0.14em] text-muted">
                      {item.clinic_name ?? item.practice_type ?? "Practice Desk Chat"} • {formatDate(item.requested_at)}
                    </p>
                  </button>
                );
              })
            )}
          </div>
        </Card>
      </aside>

      <section className="space-y-4">
        {selectedQueueItem && conversation && caseSnapshot ? (
          <>
            <Card className="space-y-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={categoryVariant(selectedQueueItem.category)}>{selectedQueueItem.category}</Badge>
                    <Badge variant={stageVariant(selectedQueueItem.handoff_stage)}>
                      {stageLabel(selectedQueueItem.handoff_stage, selectedQueueItem.queue_position)}
                    </Badge>
                  </div>
                  <h2 className="mt-3 text-2xl font-semibold tracking-[-0.03em] text-ink">{selectedQueueItem.chat_title}</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-700">{topStatusCopy(selectedQueueItem)}</p>
                </div>
                <div className="flex min-w-[168px] flex-col items-stretch gap-2 rounded-[22px] border border-slate-200/85 bg-slate-50/75 px-4 py-3">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">Requested</p>
                  <p className="mt-2 text-sm font-semibold text-ink">{formatDate(selectedQueueItem.requested_at)}</p>
                  <p className="mt-1 text-xs text-slate-600">
                    {selectedQueueItem.handoff_stage === "queued"
                      ? `Queue Position #${selectedQueueItem.queue_position ?? 1}`
                      : selectedQueueItem.handoff_stage === "reviewing"
                        ? "Agent is reviewing and in charge."
                        : "Agent is connected and chatting live."}
                  </p>
                  {selectedQueueItem.handoff_stage === "queued" ? (
                    <Button variant="primary" onClick={takeOverChat} disabled={takingOver}>
                      <QueueIcon className="h-4 w-4" />
                      {takingOver ? "Taking Over..." : "Take Over Chat"}
                    </Button>
                  ) : (
                    <Button variant="secondary" disabled>
                      {selectedQueueItem.handoff_stage === "reviewing" ? "Agent Reviewing" : "Live Chat Active"}
                    </Button>
                  )}
                </div>
              </div>
              <div className="rounded-[22px] border border-slate-200/85 bg-slate-50/75 p-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">Escalation Summary</p>
                <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-700">
                  {summaryPoints(selectedQueueItem).map((point) => (
                    <li key={point} className="flex gap-2">
                      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </Card>

            <div className="grid gap-4 2xl:grid-cols-[340px_minmax(0,1fr)]">
              <div className="space-y-4">
                <Card className="space-y-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Practice Profile</p>
                      <h3 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-ink">Chat Context</h3>
                    </div>
                    <div className="rounded-full border border-white/80 bg-white/90 px-3 py-2 text-center shadow-[0_12px_24px_rgba(15,23,42,0.06)]">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">Completion</p>
                      <p className="mt-1 text-lg font-semibold text-ink">{caseSnapshot.clinic_memory.profile_completion_score}%</p>
                    </div>
                  </div>

                  <div className="grid gap-3">
                    <ProfileField label="Clinic Name" value={caseSnapshot.clinic_memory.clinic_name} emptyLabel="Not captured yet" />
                    <ProfileField label="Practice Type" value={caseSnapshot.clinic_memory.practice_type} emptyLabel="Not captured yet" />
                    <ProfileField label="Location" value={caseSnapshot.clinic_memory.location} emptyLabel="Not captured yet" />
                    <ProfileField label="Providers" value={caseSnapshot.clinic_memory.providers} emptyLabel="Not captured yet" />
                    <ProfileField
                      label="Front Desk Staff"
                      value={caseSnapshot.clinic_memory.front_desk_staff_count}
                      emptyLabel="Not captured yet"
                    />
                    <ProfileField
                      label="PMS / EHR"
                      value={caseSnapshot.clinic_memory.pms_software}
                      emptyLabel="Not captured yet"
                      action={<PmsInfoButton />}
                    />
                    <ProfileField
                      label="Billing Status"
                      value={caseSnapshot.clinic_memory.insurance_billing_status}
                      emptyLabel="No billing issue captured"
                    />
                  </div>
                </Card>

                <Card className="space-y-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Audit Trail</p>
                    <h3 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-ink">Practice Desk Log</h3>
                  </div>
                  <div className="max-h-[420px] space-y-3 overflow-y-auto pr-1">
                    {caseSnapshot.timeline.map((event) => (
                      <div key={event.event_id} className="rounded-[20px] border border-slate-200/85 bg-slate-50/75 p-4">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <p className="text-sm font-semibold text-ink">{event.stage}</p>
                          <Badge variant={event.status === "offline" ? "danger" : "success"}>
                            {event.status === "offline" ? "Offline" : "Live"}
                          </Badge>
                        </div>
                        <p className="mt-2 text-sm leading-6 text-slate-700">{event.detail}</p>
                        <p className="mt-2 text-[11px] uppercase tracking-[0.14em] text-muted">{formatDate(event.timestamp)}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>

              <Card className="space-y-4">
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Transcript</p>
                  <h3 className="text-xl font-semibold tracking-[-0.03em] text-ink">Live Human Support Chat</h3>
                  <p className="text-sm leading-6 text-slate-700">
                    You are replying directly into the Practice Desk conversation. System notices, ClinicOS AI replies, and
                    human support replies stay visually distinct in the transcript.
                  </p>
                </div>

                <div
                  ref={transcriptViewportRef}
                  className="max-h-[620px] overflow-y-auto rounded-[28px] border border-slate-200/85 bg-[linear-gradient(180deg,rgba(248,250,252,0.96),rgba(239,244,248,0.9))] p-3 md:p-4"
                >
                  {conversation.messages.length > 0 ? (
                    <MessageList messages={conversation.messages} showAgentMeta={false} assistantLabel="ClinicOS AI" viewer="admin" />
                  ) : (
                    <div className="rounded-[22px] border border-dashed border-slate-200 bg-white/80 p-4 text-sm leading-6 text-slate-500">
                      No chat messages have been captured yet for this escalation.
                    </div>
                  )}
                </div>

                <form className="space-y-3" onSubmit={sendReply}>
                  <Textarea
                    rows={4}
                    value={reply}
                    onChange={(event) => setReply(event.target.value)}
                    disabled={sending}
                    placeholder="Reply as human support. The clinic will receive this in Practice Desk."
                  />
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="text-xs text-slate-500">
                      Human replies appear live in the same Practice Desk chat for the clinic, and sending one automatically
                      marks the chat as taken over if it was still waiting.
                    </p>
                    <Button type="submit" disabled={sending || !reply.trim()}>
                      <SendIcon className="h-4 w-4" />
                      {sending ? "Sending..." : "Send Human Reply"}
                    </Button>
                  </div>
                </form>
              </Card>
            </div>
          </>
        ) : (
          <Card>
            <p className="text-sm leading-6 text-muted">
              Select a queued chat to review the practice profile, audit trail, transcript, and human takeover composer.
            </p>
          </Card>
        )}

        {error ? <p className="text-sm text-danger">{error}</p> : null}
      </section>

      <Dialog open={guideOpen} onClose={() => setGuideOpen(false)} className="max-w-2xl">
        <div className="space-y-5">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Review Queue</p>
              <h3 className="text-2xl font-semibold tracking-[-0.03em] text-ink">How To Use This View</h3>
            </div>
            <Button variant="ghost" className="px-3 py-2 text-xs" onClick={() => setGuideOpen(false)}>
              Close
            </Button>
          </div>

          <div className="space-y-4 text-sm leading-7 text-slate-700">
            <p>
              Start with the next queued Practice Desk chat, skim the escalation bullets, and confirm the clinic context in
              the Practice Profile before you step into the transcript.
            </p>
            <p>
              Use <strong>Take Over Chat</strong> when you want the clinic to know a human agent is reviewing and in charge.
              If you reply directly from here, that takeover happens automatically.
            </p>
            <p>
              The transcript keeps system notices, ClinicOS AI replies, and human support replies visually separate so you
              can quickly understand where the handoff happened and what the clinic sees in Practice Desk.
            </p>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
