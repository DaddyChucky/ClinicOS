"use client";

import { type ReactNode, startTransition, useEffect, useMemo, useRef, useState } from "react";

import { PmsInfoButton } from "@/components/profile/PmsInfoButton";
import { Dialog } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { InfoIcon, PlusIcon, QueueIcon, RefreshIcon, SendIcon, TrashIcon } from "@/components/ui/icons";
import { Textarea } from "@/components/ui/textarea";
import { MessageList } from "@/components/chat/MessageList";
import { api } from "@/lib/api";
import { CaseSnapshot, Conversation, ConversationSummary, HumanSupportQueueItem, Message, OpenAIHealth } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const WORKSPACE_USER = {
  name: "Practice Manager",
  email: "manager@clinicos.app",
};

const SCENARIOS: Array<{ category: string; text: string }> = [
  { category: "Software Support", text: "Our Dentrix claim batches stopped posting after yesterday's close and the billing team needs help troubleshooting the sync." },
  { category: "Billing FAQ", text: "We changed card details for autopay, but the practice still sees a billing failure banner and wants to know the next step." },
  { category: "Software Support", text: "Front-desk staff at our dermatology clinic cannot close the day because payment posting is out of sync with appointments." },
  { category: "Software Support", text: "Our pediatric practice is getting duplicate reminder sends after check-in and patients are calling the office confused." },
  { category: "Software Support", text: "Insurance verification is lagging for tomorrow's schedule and the team needs a quick support checklist." },
  { category: "Software Support", text: "We need help troubleshooting why text reminders are not reaching patients for one of our satellite locations." },
  { category: "Billing FAQ", text: "Where can I confirm whether billing date alignment is available on our current subscription?" },
  { category: "Upgrade Guidance", text: "We need to know which upgrade includes better billing automation and claims workflow support for our office." },
  { category: "Software Support", text: "The office cannot post payments after lunch because the ledger view is not matching the appointment schedule." },
  { category: "Software Support", text: "Our recall reminder queue looks stuck and the front desk wants to know what to check first." },
  { category: "Billing FAQ", text: "A clinic manager is asking how refunds and failed payments are handled, and what requires a human billing specialist." },
  { category: "Upgrade Guidance", text: "We are considering an upgrade and want to know whether multi-location reporting is included." },
  { category: "Software Support", text: "Claims are stuck in pending and the team needs exact next-step guidance before the end of the day." },
  { category: "Software Support", text: "The check-in screen is freezing for one location and the front desk wants a quick recovery path." },
  { category: "Billing FAQ", text: "We need clarification on what billing workflows are included versus what a specialist has to change for us." },
  { category: "Escalation Routing", text: "This looks account-specific and I need to know whether I should talk to a human support specialist now." },
  { category: "Software Support", text: "Our appointment reminders sent twice this morning and the practice wants troubleshooting steps before tomorrow's schedule." },
  { category: "Upgrade Guidance", text: "What upgrade path should we review if the office needs stronger claims visibility and billing dashboards?" },
  { category: "Software Support", text: "The billing team says claim follow-up status is missing after the nightly sync and they need help right away." },
  { category: "Escalation Routing", text: "We have repeated support issues in this same workflow and want to know when a human handoff is appropriate." },
];

function pickScenarioSet(previousTexts: string[] = []) {
  const previous = new Set(previousTexts);
  for (let attempt = 0; attempt < 6; attempt += 1) {
    const shuffled = [...SCENARIOS].sort(() => Math.random() - 0.5).slice(0, 4);
    if (shuffled.some((item) => !previous.has(item.text))) {
      return shuffled;
    }
  }
  return [...SCENARIOS].sort(() => Math.random() - 0.5).slice(0, 4);
}

function friendlyChatTitle(item: ConversationSummary) {
  if (item.title && !["ClinicOS AI Conversation", "ClinicOS AI Chat"].includes(item.title)) {
    return item.title;
  }
  if (item.last_message_preview) {
    return item.last_message_preview.slice(0, 62);
  }
  return `Chat #${item.id}`;
}

function profileValue(value: string | number | null | undefined, emptyLabel = "Still learning") {
  if (value === null || value === undefined || value === "") {
    return <span className="text-slate-400">{emptyLabel}</span>;
  }
  return <span className="text-ink">{String(value)}</span>;
}

function pendingMessage(id: number, content: string): Message {
  return {
    id,
    role: "user",
    content,
    created_at: new Date().toISOString(),
  };
}

function ProfileField({
  label,
  value,
  emptyLabel,
  labelAction,
}: {
  label: string;
  value: string | number | null | undefined;
  emptyLabel?: string;
  labelAction?: ReactNode;
}) {
  return (
    <div className="rounded-[22px] border border-slate-200/80 bg-slate-50/70 p-4">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">{label}</p>
        {labelAction}
      </div>
      <p className="mt-2 text-sm font-medium leading-6">{profileValue(value, emptyLabel)}</p>
    </div>
  );
}

function LoadingReply() {
  return (
    <div className="mr-auto mt-3 max-w-[86%] animate-fade-rise">
      <div className="rounded-[28px] rounded-bl-[10px] border border-slate-200/90 bg-white/95 px-4 py-4 shadow-[0_18px_45px_rgba(15,23,42,0.08)]">
        <div className="mb-3 flex items-center gap-2">
          <span className="pulse-dot h-2.5 w-2.5 rounded-full bg-rose-500" />
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">ClinicOS AI is thinking</p>
        </div>
        <div className="space-y-2">
          <div className="shimmer-line h-2.5 w-40 rounded-full" />
          <div className="shimmer-line h-2.5 w-full rounded-full" />
          <div className="shimmer-line h-2.5 w-5/6 rounded-full" />
        </div>
      </div>
    </div>
  );
}

function HumanSupportQueueNotice({ supportStatus }: { supportStatus: HumanSupportQueueItem }) {
  const queued = supportStatus.handoff_stage === "queued";
  const reviewing = supportStatus.handoff_stage === "reviewing";
  const liveChat = supportStatus.handoff_stage === "live_chat";
  const cardClass = queued
    ? "border-amber-200/90 bg-[linear-gradient(180deg,rgba(255,251,235,0.98),rgba(255,255,255,0.96))]"
    : liveChat
      ? "border-emerald-200/90 bg-[linear-gradient(180deg,rgba(236,253,245,0.98),rgba(255,255,255,0.96))]"
      : "border-lime-200/90 bg-[linear-gradient(180deg,rgba(247,254,231,0.98),rgba(255,255,255,0.96))]";
  const dotClass = queued ? "pulse-dot bg-amber-500" : reviewing ? "bg-lime-500" : "bg-emerald-500";
  const labelClass = queued ? "text-amber-800" : reviewing ? "text-lime-800" : "text-emerald-800";
  const badgeVariant = queued ? "warning" : liveChat ? "success" : "info";
  const heading = queued
    ? "ClinicOS AI Agent is disconnected for this chat."
    : reviewing
      ? "A human support agent is now reviewing and in charge."
      : "A human support agent is connected and chatting with you live.";
  const body = queued
    ? `A human specialist will take over shortly. You're #${supportStatus.queue_position ?? 1} in line and any new messages you send here will stay in this chat for the support queue.`
    : reviewing
      ? "ClinicOS AI remains offline while the human support agent reviews your conversation and prepares the next reply."
      : "ClinicOS AI remains offline while the human support agent continues the conversation with you here in real time.";

  return (
    <div className={`rounded-[26px] border p-4 shadow-[0_18px_45px_rgba(15,23,42,0.08)] ${cardClass}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${dotClass}`} />
            <p className={`text-[11px] font-semibold uppercase tracking-[0.16em] ${labelClass}`}>
              {queued ? "Awaiting Human Support" : reviewing ? "Agent Reviewing" : "Human Support Is Live"}
            </p>
          </div>
          <h4 className="text-lg font-semibold tracking-[-0.02em] text-ink">{heading}</h4>
          <p className="text-sm leading-6 text-slate-700">{body}</p>
        </div>
        <Badge variant={badgeVariant}>
          {queued ? `Queue #${supportStatus.queue_position ?? 1}` : reviewing ? "Reviewing" : "Live Chat"}
        </Badge>
      </div>
    </div>
  );
}

export function ChatShell() {
  const [threads, setThreads] = useState<ConversationSummary[]>([]);
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [caseSnapshot, setCaseSnapshot] = useState<CaseSnapshot | null>(null);
  const [supportStatus, setSupportStatus] = useState<HumanSupportQueueItem | null>(null);
  const [aiHealth, setAiHealth] = useState<OpenAIHealth | null>(null);
  const [scenarioSet, setScenarioSet] = useState(() => pickScenarioSet());
  const [composer, setComposer] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [pendingDeleteChat, setPendingDeleteChat] = useState<ConversationSummary | null>(null);
  const [guideOpen, setGuideOpen] = useState(false);
  const [handoffBannerOpen, setHandoffBannerOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chatViewportRef = useRef<HTMLDivElement | null>(null);
  const shouldStickToBottomRef = useRef(true);

  async function loadThread(conversationId: number) {
    const [thread, snapshot, nextSupportStatus] = await Promise.all([
      api.getConversation(conversationId),
      api.getCaseSnapshot(conversationId),
      api.getHumanSupportStatus(conversationId).catch(() => null),
    ]);
    startTransition(() => {
      setConversation(thread);
      setCaseSnapshot(snapshot);
      setSupportStatus(nextSupportStatus);
    });
  }

  async function refreshThreads() {
    const items = await api.listConversations(WORKSPACE_USER.email);
    startTransition(() => {
      setThreads(items);
    });
  }

  async function createThread(openingMessage?: string) {
    const started = await api.startConversation({
      openingMessage,
      userName: WORKSPACE_USER.name,
      userEmail: WORKSPACE_USER.email,
    });
    await Promise.all([loadThread(started.id), refreshThreads()]);
    return started;
  }

  async function createQuickThread() {
    setLoading(true);
    setError(null);
    try {
      await createThread();
      setComposer("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start a new chat");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      try {
        setLoading(true);
        const [health, existingThreads] = await Promise.all([
          api.getOpenAIHealth().catch(() => null),
          api.listConversations(WORKSPACE_USER.email).catch(() => []),
        ]);
        if (!active) return;

        startTransition(() => {
          setAiHealth(health);
          setThreads(existingThreads);
        });

        if (existingThreads.length > 0) {
          await loadThread(existingThreads[0].id);
        } else {
          await createThread();
        }
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Failed to load Practice Desk");
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
    const viewport = chatViewportRef.current;
    if (!viewport) return undefined;

    function handleScroll() {
      const node = chatViewportRef.current;
      if (!node) return;
      const distanceFromBottom = node.scrollHeight - node.scrollTop - node.clientHeight;
      shouldStickToBottomRef.current = distanceFromBottom < 80;
    }

    handleScroll();
    viewport.addEventListener("scroll", handleScroll, { passive: true });
    return () => {
      viewport.removeEventListener("scroll", handleScroll);
    };
  }, [conversation?.id]);

  useEffect(() => {
    const node = chatViewportRef.current;
    if (!node || !shouldStickToBottomRef.current) return;
    node.scrollTo({ top: node.scrollHeight, behavior: "smooth" });
  }, [conversation?.messages.length, sending, supportStatus?.handoff_stage]);

  useEffect(() => {
    if (!conversation) return;
    const interval = window.setInterval(() => {
      loadThread(conversation.id).catch(() => null);
    }, supportStatus ? 6000 : 12000);
    return () => {
      window.clearInterval(interval);
    };
  }, [conversation?.id, supportStatus]);

  useEffect(() => {
    if (!handoffBannerOpen) return undefined;
    const timeout = window.setTimeout(() => {
      setHandoffBannerOpen(false);
    }, 5200);
    return () => {
      window.clearTimeout(timeout);
    };
  }, [handoffBannerOpen]);

  async function sendMessage(rawText?: string) {
    if (!conversation || sending) return;
    if (caseSnapshot?.controls && !caseSnapshot.controls.workspace_available) return;
    const text = (rawText ?? composer).trim();
    if (!text) return;

    const previousConversation = conversation;
    setSending(true);
    setError(null);
    setComposer("");
    startTransition(() => {
      setConversation((current) =>
        current
          ? {
              ...current,
              messages: [...current.messages, pendingMessage(-Date.now(), text)],
            }
          : current
      );
    });

    try {
      await api.sendMessage(conversation.id, text);
      await Promise.all([loadThread(conversation.id), refreshThreads()]);
    } catch (err) {
      startTransition(() => {
        setConversation(previousConversation);
      });
      setComposer(text);
      setError(err instanceof Error ? err.message : "Failed to send message");
    } finally {
      setSending(false);
    }
  }

  async function requestHumanSupport() {
    if (!conversation || sending) return;
    setSending(true);
    setError(null);
    try {
      await api.talkToHuman(conversation.id);
      await Promise.all([loadThread(conversation.id), refreshThreads()]);
      setHandoffBannerOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create escalation");
    } finally {
      setSending(false);
    }
  }

  async function openThread(id: number) {
    if (conversation?.id === id) return;
    setLoading(true);
    setError(null);
    try {
      await loadThread(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to open conversation");
    } finally {
      setLoading(false);
    }
  }

  function queueDeleteChat(target: ConversationSummary) {
    setPendingDeleteChat(target);
    setDeleteConfirmOpen(true);
  }

  async function deleteActiveChat() {
    const target = pendingDeleteChat;
    if (!target || deleting) return;

    setDeleting(true);
    setError(null);

    try {
      await api.deleteConversation(target.id, "user");
      const remainingThreads = await api.listConversations(WORKSPACE_USER.email);
      startTransition(() => {
        setThreads(remainingThreads);
      });

      if (conversation?.id === target.id && remainingThreads.length > 0) {
        await loadThread(remainingThreads[0].id);
      } else if (conversation?.id === target.id) {
        await createThread();
      } else {
        await refreshThreads();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete chat");
    } finally {
      setDeleting(false);
      setDeleteConfirmOpen(false);
      setPendingDeleteChat(null);
    }
  }

  const liveMode = aiHealth?.runtime_mode === "live_ai";
  const profile = caseSnapshot?.clinic_memory;
  const workspaceAvailable = caseSnapshot?.controls?.workspace_available ?? true;
  const talkToHumanVisible = Boolean(
    conversation &&
      !supportStatus &&
      (conversation.human_requested ||
        conversation.escalation_recommended ||
        conversation.active_workflow === "human_escalation" ||
        conversation.unresolved_turn_count >= 2 ||
        conversation.loop_count >= 2)
  );

  const chatCountLabel = useMemo(() => `${threads.length} ${threads.length === 1 ? "Chat" : "Chats"}`, [threads.length]);

  if (loading && !conversation) {
    return (
      <Card className="space-y-4">
        <div className="shimmer-line h-3 w-40 rounded-full" />
        <div className="shimmer-line h-16 w-full rounded-[24px]" />
        <div className="shimmer-line h-16 w-full rounded-[24px]" />
      </Card>
    );
  }

  if (!conversation) {
    return <p className="text-sm text-danger">Practice Desk is unavailable right now.</p>;
  }

  const activeChatTitle = friendlyChatTitle({
    id: conversation.id,
    title: conversation.title,
    updated_at: new Date().toISOString(),
    last_message_preview: conversation.messages[conversation.messages.length - 1]?.content ?? null,
  });
  const activeChatSummary: ConversationSummary = {
    id: conversation.id,
    title: conversation.title,
    updated_at: conversation.messages[conversation.messages.length - 1]?.created_at ?? new Date().toISOString(),
    last_message_preview: conversation.messages[conversation.messages.length - 1]?.content ?? null,
  };
  const activeChatEngaged = conversation.messages.length > 0;

  return (
    <>
      {handoffBannerOpen ? (
        <div className="mb-5 animate-fade-rise rounded-[24px] border border-emerald-200/90 bg-[linear-gradient(120deg,rgba(236,253,245,0.98),rgba(255,255,255,0.96))] p-4 shadow-[0_18px_45px_rgba(5,150,105,0.08)]">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-700">Escalation Confirmed</p>
              <p className="mt-1 text-sm leading-6 text-slate-700">
                Your request has been escalated. A human support specialist will assist you shortly in this same chat.
              </p>
            </div>
            <Badge variant="success">Queued</Badge>
          </div>
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[320px_minmax(0,1.45fr)_340px]">
        <aside className="space-y-5">
            <Card className="overflow-hidden bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(241,248,246,0.92))]">
              <div className="space-y-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-2">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">ClinicOS AI</p>
                    <h2 className="text-2xl font-semibold tracking-[-0.03em] text-ink">One copilot for clinic support</h2>
                    <p className="text-sm leading-6 text-slate-700">
                      Get help with software questions, upgrade guidance, billing FAQs, and escalation routing. ClinicOS AI
                      keeps track of the support context your team has already shared so the next step stays clear.
                    </p>
                  </div>

                  <div className="rounded-full border border-rose-100 bg-white/85 px-3 py-2 shadow-[0_12px_24px_rgba(15,23,42,0.06)]">
                    {liveMode ? (
                      <div className="flex items-center gap-2 text-sm font-semibold text-ink">
                        <span className="pulse-dot h-2.5 w-2.5 rounded-full bg-rose-500" />
                        Live
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-sm font-semibold text-rose-700">
                        <span className="h-2.5 w-2.5 rounded-full bg-rose-500" />
                        Offline
                      </div>
                    )}
                  </div>
                </div>

                <div className="grid gap-3">
                  <div className="rounded-[22px] border border-white/80 bg-white/90 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Coverage</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Badge variant="info">Software Support</Badge>
                      <Badge variant="success">Upgrade Guidance</Badge>
                      <Badge variant="warning">Billing FAQs</Badge>
                      <Badge variant="default">Escalation Routing</Badge>
                    </div>
                  </div>
                  <div className="rounded-[22px] border border-white/80 bg-white/90 p-4 text-sm leading-6 text-slate-700">
                    {aiHealth?.detail ?? "ClinicOS AI is ready to help with common clinic software support questions."}
                  </div>
                </div>
              </div>
            </Card>

            <Card className="space-y-4">
              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Guidance</p>
                <h3 className="text-lg font-semibold tracking-[-0.02em] text-ink">How It Works</h3>
                <p className="text-sm leading-6 text-slate-700">
                  Practice Desk is built for support only. Ask about clinic software workflows, upgrades, billing FAQs, or
                  when it makes sense to bring in a human specialist.
                </p>
              </div>
              <Button variant="secondary" className="w-full" onClick={() => setGuideOpen(true)}>
                <InfoIcon className="h-4 w-4" />
                How ClinicOS AI works
              </Button>
            </Card>

            <Card className="space-y-4">
              <div className="flex items-center justify-between gap-2">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Recent Chats</p>
                  <p className="mt-1 text-sm text-slate-600">{chatCountLabel}</p>
                </div>
              </div>

              <div className="max-h-[292px] space-y-2 overflow-y-auto pr-1">
                {threads.length === 0 ? (
                  <div className="rounded-[22px] border border-dashed border-slate-200 bg-slate-50/80 p-4 text-sm text-slate-500">
                    Your recent ClinicOS AI support chats will appear here.
                  </div>
                ) : (
                  threads.map((item) => {
                    const active = conversation.id === item.id;
                    const canDeleteChat = Boolean(item.last_message_preview?.trim());
                    return (
                      <div
                        key={item.id}
                        className={`w-full rounded-[22px] border p-4 text-left transition ${
                          active
                            ? "border-emerald-200 bg-[linear-gradient(180deg,rgba(237,252,248,0.98),rgba(255,255,255,0.98))] shadow-[0_18px_40px_rgba(13,118,104,0.12)]"
                            : "border-slate-200/85 bg-white/92 hover:border-slate-300 hover:bg-white"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <button type="button" onClick={() => openThread(item.id)} className="min-w-0 flex-1 text-left">
                            <p className="line-clamp-2 text-sm font-semibold leading-6 text-ink">{friendlyChatTitle(item)}</p>
                            <p className="mt-2 text-[11px] uppercase tracking-[0.14em] text-muted">{formatDate(item.updated_at)}</p>
                          </button>
                          {canDeleteChat ? (
                            <button
                              type="button"
                              aria-label={`Delete ${friendlyChatTitle(item)}`}
                              onClick={() => queueDeleteChat(item)}
                              className="rounded-full border border-slate-200/85 bg-white/92 p-2 text-slate-500 transition hover:border-rose-200 hover:bg-rose-50 hover:text-rose-700"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          ) : null}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </Card>
        </aside>

        <section className="space-y-5">
            <Card className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Active Chat</p>
                  <h3 className="text-2xl font-semibold tracking-[-0.03em] text-ink">{activeChatTitle}</h3>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Button variant="secondary" onClick={createQuickThread} disabled={loading || deleting || sending}>
                    <PlusIcon className="h-4 w-4" />
                    New Chat
                  </Button>
                  {activeChatEngaged ? (
                    <Button
                      variant="secondary"
                      className="border-rose-200/90 bg-rose-50/70 text-rose-700 hover:border-rose-300 hover:bg-rose-50"
                      onClick={() => queueDeleteChat(activeChatSummary)}
                      disabled={deleting || sending}
                    >
                      <TrashIcon className="h-4 w-4" />
                      Delete Chat
                    </Button>
                  ) : null}
                  {conversation.escalation_recommended ? <Badge variant="warning">Needs Attention</Badge> : null}
                  <Badge variant="default">{formatDate(conversation.messages[conversation.messages.length - 1]?.created_at ?? new Date().toISOString())}</Badge>
                </div>
              </div>

              {supportStatus ? <HumanSupportQueueNotice supportStatus={supportStatus} /> : null}

              <div
                ref={chatViewportRef}
                className="max-h-[560px] overflow-y-auto rounded-[28px] border border-slate-200/85 bg-[linear-gradient(180deg,rgba(248,250,252,0.96),rgba(239,244,248,0.9))] p-3 md:p-4"
              >
                {conversation.messages.length > 0 ? (
                  <>
                    <MessageList messages={conversation.messages} showAgentMeta={false} assistantLabel="ClinicOS AI" viewer="workspace" />
                    {sending && !supportStatus ? <LoadingReply /> : null}
                  </>
                ) : (
                  <div className="rounded-[22px] border border-dashed border-slate-200 bg-white/80 p-4 text-sm leading-6 text-slate-500">
                    Ask ClinicOS AI about software issues, billing questions, upgrade options, or whether this support case
                    should be routed to a human specialist.
                  </div>
                )}
              </div>

              <div className="space-y-3">
                {!workspaceAvailable ? (
                  <div className="rounded-[22px] border border-slate-200 bg-slate-100/90 p-4 text-sm leading-6 text-slate-500">
                    {caseSnapshot?.controls?.admin_message ?? "Practice Desk is temporarily unavailable because an admin suspended this chat."}
                  </div>
                ) : null}
                <Textarea
                  value={composer}
                  onChange={(event) => setComposer(event.target.value)}
                  rows={4}
                  disabled={!workspaceAvailable}
                  placeholder={
                    supportStatus
                      ? "Add any extra details the human support specialist should see in this chat."
                      : "Example: Claims are delayed after the nightly sync and our billing team needs the next troubleshooting step."
                  }
                />
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="text-xs text-slate-500">
                    {supportStatus
                      ? supportStatus.handoff_stage === "queued"
                        ? "This chat is in the human support queue. Your updates stay here until the specialist picks it up."
                        : supportStatus.handoff_stage === "reviewing"
                          ? "A human support agent is reviewing your chat now and will respond promptly from this conversation."
                          : "A human support agent is connected and chatting with you live from this conversation."
                      : "ClinicOS AI can guide software support, billing FAQs, upgrade questions, and human escalation routing from this chat."}
                  </p>
                  <div className="flex flex-wrap items-center gap-2">
                    {talkToHumanVisible ? (
                      <Button variant="secondary" onClick={requestHumanSupport} disabled={sending}>
                        <QueueIcon className="h-4 w-4" />
                        Talk to Human
                      </Button>
                    ) : null}
                    <Button variant="primary" onClick={() => sendMessage()} disabled={sending || !composer.trim() || !workspaceAvailable}>
                      <SendIcon className="h-4 w-4" />
                      {sending ? (supportStatus ? "Sending..." : "Working...") : supportStatus ? "Send Update" : "Send"}
                    </Button>
                  </div>
                </div>
              </div>

              {error ? <p className="text-sm text-danger">{error}</p> : null}
            </Card>
        </section>

        <aside className="space-y-5">
            <Card className="space-y-4">
              <div className="flex items-center justify-between gap-2">
                <div>
                  <h3 className="text-lg font-semibold tracking-[-0.02em] text-ink">Suggested Support Scenarios</h3>
                  <p className="text-sm text-slate-600">Jump into realistic software support, billing, upgrade, and escalation questions.</p>
                </div>
                <Button
                  variant="ghost"
                  className="px-3 py-2 text-xs"
                  onClick={() => setScenarioSet((current) => pickScenarioSet(current.map((item) => item.text)))}
                >
                  <RefreshIcon className="h-4 w-4" />
                  Refresh
                </Button>
              </div>

              <div className="grid gap-3">
                {scenarioSet.map((scenario) => (
                  <button
                    key={scenario.text}
                    type="button"
                    onClick={() => sendMessage(scenario.text)}
                    disabled={sending || !workspaceAvailable}
                    className="rounded-[24px] border border-slate-200/85 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(247,250,252,0.95))] p-4 text-left transition hover:-translate-y-0.5 hover:border-emerald-200 hover:shadow-[0_20px_45px_rgba(15,23,42,0.08)] disabled:cursor-not-allowed disabled:opacity-55"
                  >
                    <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">{scenario.category}</p>
                    <p className="mt-2 text-sm leading-6 text-slate-700">{scenario.text}</p>
                  </button>
                ))}
              </div>
            </Card>

            <Card className="space-y-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Practice profile</p>
                  <h3 className="text-2xl font-semibold tracking-[-0.03em] text-ink">Context ClinicOS AI is using</h3>
                </div>
                <div className="min-w-[140px] rounded-full border border-white/80 bg-white/90 px-3 py-2 text-center shadow-[0_12px_24px_rgba(15,23,42,0.06)]">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">Completion</p>
                  <p className="mt-1 text-lg font-semibold text-ink">{profile?.profile_completion_score ?? 0}%</p>
                </div>
              </div>

              <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-[linear-gradient(90deg,#0d7668,#5bb7b4)] transition-all"
                  style={{ width: `${profile?.profile_completion_score ?? 0}%` }}
                />
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <ProfileField label="Clinic name" value={profile?.clinic_name} emptyLabel="Share the practice name" />
                <ProfileField label="Practice type" value={profile?.practice_type} emptyLabel="Still learning the specialty" />
                <ProfileField label="Location" value={profile?.location} emptyLabel="No market shared yet" />
                <ProfileField label="Providers" value={profile?.providers} emptyLabel="Provider count not shared yet" />
                <ProfileField
                  label="Front desk staff"
                  value={profile?.front_desk_staff_count}
                  emptyLabel="Front-desk team size not known yet"
                />
                <ProfileField
                  label="PMS / EHR"
                  value={profile?.pms_software}
                  emptyLabel="System not shared yet"
                  labelAction={<PmsInfoButton />}
                />
                <ProfileField
                  label="Billing status"
                  value={profile?.insurance_billing_status}
                  emptyLabel="No billing signal captured yet"
                />
              </div>

              {profile?.missing_profile_fields?.length ? (
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Still helpful to learn</p>
                  <div className="flex flex-wrap gap-2">
                    {profile.missing_profile_fields.slice(0, 4).map((field) => (
                      <span key={field} className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-600">
                        {field}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}
            </Card>
        </aside>
      </div>

      <Dialog open={guideOpen} onClose={() => setGuideOpen(false)}>
        <div className="space-y-5">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">ClinicOS AI</p>
              <h3 className="text-2xl font-semibold tracking-[-0.03em] text-ink">How ClinicOS AI works</h3>
            </div>
            <Button variant="ghost" className="px-3 py-2 text-xs" onClick={() => setGuideOpen(false)}>
              Close
            </Button>
          </div>

          <div className="space-y-4 text-sm leading-7 text-slate-700">
            <p>
              Practice Desk is the support surface for existing clinics. Use it for software troubleshooting, upgrade guidance,
              billing FAQs, and knowing when to route the case to a human specialist.
            </p>
            <p>
              For the strongest answers, include the practice type, your systems, the exact workflow that is blocked, and any
              error details the team is seeing. If key context is missing, ClinicOS AI will ask short follow-up questions instead of guessing.
            </p>
            <p>
              If you need sales, outreach, or marketing planning, use the specialist tools in Operations Console. Practice Desk
              stays focused on support so the answers stay operational and reliable for common clinic inquiries.
            </p>
            <p>
              Human escalation becomes available when the issue looks unresolved, account-specific, high-risk, or when your team
              directly asks for a person to step in.
            </p>
          </div>
        </div>
      </Dialog>

      <Dialog
        open={deleteConfirmOpen}
        onClose={() => {
          setDeleteConfirmOpen(false);
          setPendingDeleteChat(null);
        }}
        className="max-w-lg"
      >
        <div className="space-y-5">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Delete Chat</p>
            <h3 className="text-2xl font-semibold tracking-[-0.03em] text-ink">Remove this chat from Practice Desk?</h3>
            <p className="text-sm leading-7 text-slate-700">
              {pendingDeleteChat
                ? `This will remove "${friendlyChatTitle(pendingDeleteChat)}" from Practice Desk. The chat will still remain archived in Operations Console for admin review.`
                : "This chat will disappear from Practice Desk, but it will stay archived in Operations Console for admin review."}
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-end gap-2">
            <Button
              variant="ghost"
              onClick={() => {
                setDeleteConfirmOpen(false);
                setPendingDeleteChat(null);
              }}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button variant="danger" onClick={deleteActiveChat} disabled={deleting}>
              <TrashIcon className="h-4 w-4" />
              {deleting ? "Deleting..." : "Delete Chat"}
            </Button>
          </div>
        </div>
      </Dialog>
    </>
  );
}
