"use client";

import Link from "next/link";
import { type ReactNode, useEffect, useMemo, useState } from "react";

import { AdminPageSkeleton } from "@/components/admin/AdminPageSkeleton";
import { PowerSwitch } from "@/components/admin/PowerSwitch";
import { PmsInfoButton } from "@/components/profile/PmsInfoButton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { ArchiveIcon, DeskIcon, SaveIcon, TrashIcon } from "@/components/ui/icons";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { CaseSnapshot, ConversationDeletion, ConversationSummary, OpenAIHealth } from "@/lib/types";
import { formatDate, toTitleCaseLabel } from "@/lib/utils";

type ProfileFormState = {
  clinic_name: string;
  practice_type: string;
  location: string;
  providers: string;
  front_desk_staff_count: string;
  pms_software: string;
  insurance_billing_status: string;
};

type ArchiveSnapshotData = {
  case_snapshot?: {
    case_id?: string;
    clinic_memory?: {
      clinic_name?: string | null;
      practice_type?: string | null;
      location?: string | null;
      providers?: number | null;
      front_desk_staff_count?: number | null;
      pms_software?: string | null;
      insurance_billing_status?: string | null;
    };
  };
  messages?: Array<{
    id: number;
    role: string;
    content: string;
    agent_name?: string | null;
    workflow?: string | null;
    created_at: string;
  }>;
  event_logs?: Array<{
    id: number;
    stage: string;
    detail: string;
    status: string;
    created_at: string;
  }>;
};

function logVariant(status: string): "success" | "danger" {
  return ["blocked", "offline"].includes(status) ? "danger" : "success";
}

function logLabel(status: string) {
  return ["blocked", "offline"].includes(status) ? "Offline" : "Live";
}

function friendlyChatTitle(item: Pick<ConversationSummary, "id" | "title" | "last_message_preview">) {
  if (item.title && !["ClinicOS AI Conversation", "ClinicOS AI Chat"].includes(item.title)) {
    return item.title;
  }
  if (item.last_message_preview) {
    return item.last_message_preview.slice(0, 72);
  }
  return `Chat #${item.id}`;
}

function archivePreview(value: string | null | undefined, length = 180) {
  if (!value) return "No archive summary captured.";
  const compact = value.replace(/\s+/g, " ").trim();
  if (compact.length <= length) {
    return compact;
  }
  return `${compact.slice(0, length - 3).trimEnd()}...`;
}

function profileFormFromSnapshot(snapshot: CaseSnapshot | null): ProfileFormState {
  return {
    clinic_name: snapshot?.clinic_memory.clinic_name ?? "",
    practice_type: snapshot?.clinic_memory.practice_type ?? "",
    location: snapshot?.clinic_memory.location ?? "",
    providers: snapshot?.clinic_memory.providers?.toString() ?? "",
    front_desk_staff_count: snapshot?.clinic_memory.front_desk_staff_count?.toString() ?? "",
    pms_software: snapshot?.clinic_memory.pms_software ?? "",
    insurance_billing_status: snapshot?.clinic_memory.insurance_billing_status ?? "",
  };
}

function LabeledInput({
  label,
  placeholder,
  value,
  onChange,
  action,
}: {
  label: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  action?: ReactNode;
}) {
  return (
    <div className="grid gap-2">
      <div className="flex min-h-6 items-center justify-between gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">
        <span>{label}</span>
        {action}
      </div>
      <Input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />
    </div>
  );
}

export default function AdminOverviewPage() {
  const [threads, setThreads] = useState<ConversationSummary[]>([]);
  const [selectedThread, setSelectedThread] = useState<number | null>(null);
  const [snapshot, setSnapshot] = useState<CaseSnapshot | null>(null);
  const [health, setHealth] = useState<OpenAIHealth | null>(null);
  const [deletedArchive, setDeletedArchive] = useState<ConversationDeletion[]>([]);
  const [selectedArchive, setSelectedArchive] = useState<ConversationDeletion | null>(null);
  const [profileForm, setProfileForm] = useState<ProfileFormState>(profileFormFromSnapshot(null));
  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [updatingControl, setUpdatingControl] = useState<"active_chat" | "global_agent" | null>(null);
  const [deletingThread, setDeletingThread] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadSnapshot(conversationId: number) {
    const result = await api.getCaseSnapshot(conversationId);
    setSnapshot(result);
    setProfileForm(profileFormFromSnapshot(result));
  }

  async function refreshThreadRail() {
    const threadList = await api.listConversations("manager@clinicos.app");
    setThreads(threadList);
    return threadList;
  }

  async function refreshDeletedArchive() {
    const archive = await api.listDeletedConversationArchive();
    setDeletedArchive(archive);
    return archive;
  }

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        setLoading(true);
        const [threadList, openaiHealth, archive] = await Promise.all([
          api.listConversations("manager@clinicos.app"),
          api.getOpenAIHealth().catch(() => null),
          api.listDeletedConversationArchive().catch(() => []),
        ]);
        if (!active) return;

        setThreads(threadList);
        setHealth(openaiHealth);
        setDeletedArchive(archive);

        if (threadList.length > 0) {
          setSelectedThread(threadList[0].id);
          await loadSnapshot(threadList[0].id);
        }
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Failed to load Operations Console");
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    return () => {
      active = false;
    };
  }, []);

  async function toggleControl(field: "active_chat_enabled" | "global_agent_enabled") {
    if (!selectedThread || !snapshot?.controls) return;
    setUpdatingControl(field === "active_chat_enabled" ? "active_chat" : "global_agent");
    setError(null);

    try {
      await api.updateConversationControls(selectedThread, {
        [field]: !snapshot.controls[field],
      });
      await Promise.all([loadSnapshot(selectedThread), refreshThreadRail()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update ClinicOS AI Triage Agent");
    } finally {
      setUpdatingControl(null);
    }
  }

  async function saveProfile() {
    if (!selectedThread) return;
    setSavingProfile(true);
    setError(null);

    try {
      const updated = await api.updatePracticeProfile(selectedThread, {
        clinic_name: profileForm.clinic_name || null,
        practice_type: profileForm.practice_type || null,
        location: profileForm.location || null,
        providers: profileForm.providers ? Number(profileForm.providers) : null,
        front_desk_staff_count: profileForm.front_desk_staff_count ? Number(profileForm.front_desk_staff_count) : null,
        pms_software: profileForm.pms_software || null,
        insurance_billing_status: profileForm.insurance_billing_status || null,
      });
      setSnapshot(updated);
      setProfileForm(profileFormFromSnapshot(updated));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save practice profile");
    } finally {
      setSavingProfile(false);
    }
  }

  async function deleteChat() {
    if (!selectedThread || deletingThread) return;

    setDeletingThread(true);
    setError(null);

    try {
      await api.deleteConversation(selectedThread, "admin");
      const [threadList] = await Promise.all([refreshThreadRail(), refreshDeletedArchive()]);

      if (threadList.length > 0) {
        setSelectedThread(threadList[0].id);
        await loadSnapshot(threadList[0].id);
      } else {
        setSelectedThread(null);
        setSnapshot(null);
        setProfileForm(profileFormFromSnapshot(null));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete chat");
    } finally {
      setDeletingThread(false);
      setDeleteConfirmOpen(false);
    }
  }

  const recentChatCountLabel = useMemo(
    () => `${threads.length} ${threads.length === 1 ? "Chat" : "Chats"}`,
    [threads.length]
  );

  const selectedArchiveSnapshot = (selectedArchive?.snapshot_json ?? null) as ArchiveSnapshotData | null;

  if (loading) {
    return <AdminPageSkeleton />;
  }

  return (
    <>
      <div className="grid gap-5 xl:grid-cols-[300px_minmax(0,1fr)]">
        <aside className="space-y-4">
          <Card className="space-y-4">
            <div className="flex items-center justify-between gap-2">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Recent Chats</p>
                <p className="mt-1 text-sm text-slate-600">{recentChatCountLabel}</p>
              </div>
              <Badge variant={health?.runtime_mode === "live_ai" ? "success" : "danger"}>
                {health?.runtime_mode === "live_ai" ? "Live" : "Offline"}
              </Badge>
            </div>

            <div className="max-h-[320px] space-y-2 overflow-y-auto pr-1">
              {threads.length === 0 ? (
                <div className="rounded-[22px] border border-dashed border-slate-200 bg-slate-50/80 p-4 text-sm text-slate-500">
                  No active Practice Desk chats are available right now.
                </div>
              ) : (
                threads.map((item) => {
                  const active = selectedThread === item.id;
                  return (
                    <div
                      key={item.id}
                      className={`w-full rounded-[22px] border p-4 text-left transition ${
                        active
                          ? "border-emerald-200 bg-[linear-gradient(180deg,rgba(237,252,248,0.98),rgba(255,255,255,0.98))] shadow-[0_18px_40px_rgba(13,118,104,0.12)]"
                          : "border-slate-200/85 bg-white/92 hover:border-slate-300 hover:bg-white"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <button
                          type="button"
                          onClick={async () => {
                            setSelectedThread(item.id);
                            await loadSnapshot(item.id);
                          }}
                          className="min-w-0 flex-1 text-left"
                        >
                          <p className="line-clamp-2 text-sm font-semibold leading-6 text-ink">{friendlyChatTitle(item)}</p>
                          <p className="line-clamp-2 text-xs leading-5 text-slate-600">{item.last_message_preview ?? "No summary yet"}</p>
                          <p className="mt-2 text-[11px] uppercase tracking-[0.14em] text-muted">{formatDate(item.updated_at)}</p>
                        </button>
                        <button
                          type="button"
                          aria-label={`Delete ${friendlyChatTitle(item)}`}
                          onClick={async () => {
                            setSelectedThread(item.id);
                            await loadSnapshot(item.id);
                            setDeleteConfirmOpen(true);
                          }}
                          className="rounded-full border border-slate-200/85 bg-white/92 p-2 text-slate-500 transition hover:border-rose-200 hover:bg-rose-50 hover:text-rose-700"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </Card>
        </aside>

        <section className="space-y-5">
          {snapshot ? (
            <>
              <Card className="space-y-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Practice Profile</p>
                    <h2 className="text-2xl font-semibold tracking-[-0.03em] text-ink">Chat-Specific Practice Profile</h2>
                    <p className="text-sm leading-6 text-slate-700">
                      Start with the operating context for this exact Practice Desk chat so ClinicOS AI can respond
                      with the right systems, staffing, and billing assumptions.
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <div className="min-w-[140px] rounded-full border border-white/80 bg-white/90 px-3 py-2 text-center shadow-[0_12px_24px_rgba(15,23,42,0.06)]">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">Completion</p>
                      <p className="mt-1 text-lg font-semibold text-ink">{snapshot.clinic_memory.profile_completion_score}%</p>
                    </div>
                    <Button
                      variant="secondary"
                      className="border-rose-200/90 bg-rose-50/70 text-rose-700 hover:border-rose-300 hover:bg-rose-50"
                      onClick={() => setDeleteConfirmOpen(true)}
                      disabled={deletingThread}
                    >
                      <TrashIcon className="h-4 w-4" />
                      Delete Chat
                    </Button>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <LabeledInput
                    label="Clinic Name"
                    placeholder="Example: Downtown Dental Group"
                    value={profileForm.clinic_name}
                    onChange={(value) => setProfileForm((current) => ({ ...current, clinic_name: value }))}
                  />
                  <LabeledInput
                    label="Practice Type"
                    placeholder="Example: General Dentistry"
                    value={profileForm.practice_type}
                    onChange={(value) => setProfileForm((current) => ({ ...current, practice_type: value }))}
                  />
                  <LabeledInput
                    label="Location"
                    placeholder="Example: Austin, TX"
                    value={profileForm.location}
                    onChange={(value) => setProfileForm((current) => ({ ...current, location: value }))}
                  />
                  <LabeledInput
                    label="Providers"
                    placeholder="Example: 4"
                    value={profileForm.providers}
                    onChange={(value) => setProfileForm((current) => ({ ...current, providers: value }))}
                  />
                  <LabeledInput
                    label="Front Desk Staff"
                    placeholder="Example: 6"
                    value={profileForm.front_desk_staff_count}
                    onChange={(value) => setProfileForm((current) => ({ ...current, front_desk_staff_count: value }))}
                  />
                  <LabeledInput
                    label="PMS / EHR"
                    placeholder="Example: Dentrix"
                    value={profileForm.pms_software}
                    onChange={(value) => setProfileForm((current) => ({ ...current, pms_software: value }))}
                    action={<PmsInfoButton className="self-center" />}
                  />
                  <div className="md:col-span-2">
                    <LabeledInput
                      label="Billing Status"
                      placeholder="Example: Claims delayed after nightly sync"
                      value={profileForm.insurance_billing_status}
                      onChange={(value) => setProfileForm((current) => ({ ...current, insurance_billing_status: value }))}
                    />
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button onClick={saveProfile} disabled={savingProfile}>
                    <SaveIcon className="h-4 w-4" />
                    {savingProfile ? "Saving..." : "Save Practice Profile"}
                  </Button>
                </div>
              </Card>

              <Card className="space-y-5">
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Operations Console</p>
                  <h2 className="text-2xl font-semibold tracking-[-0.03em] text-ink">ClinicOS AI Triage Agent</h2>
                  <p className="text-sm leading-6 text-slate-700">
                    Use the Active Chat Power Switch to take only this Practice Desk chat offline, or use the All Chats Power
                    Switch to take the ClinicOS AI Triage Agent offline across every Practice Desk chat.
                  </p>
                </div>

                <div className="grid gap-3">
                  <PowerSwitch
                    checked={Boolean(snapshot.controls?.active_chat_enabled)}
                    disabled={Boolean(updatingControl)}
                    onClick={() => toggleControl("active_chat_enabled")}
                    label="Active Chat Power Switch"
                    description={
                      snapshot.controls?.active_chat_enabled
                        ? "Live. ClinicOS AI can keep working inside this selected Practice Desk chat."
                        : "Offline. This selected Practice Desk chat is suspended and the workspace composer is locked."
                    }
                  />
                  <PowerSwitch
                    checked={Boolean(snapshot.controls?.global_agent_enabled)}
                    disabled={Boolean(updatingControl)}
                    onClick={() => toggleControl("global_agent_enabled")}
                    label="All Chats Power Switch"
                    description={
                      snapshot.controls?.global_agent_enabled
                        ? "Live. The ClinicOS AI Triage Agent is available across all Practice Desk chats."
                        : "Offline. The ClinicOS AI Triage Agent is suspended across all Practice Desk chats."
                    }
                  />
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 rounded-[24px] border border-slate-200/85 bg-slate-50/70 p-4">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">Workspace Status</p>
                    <p className="mt-2 text-sm leading-6 text-slate-700">
                      {snapshot.controls?.workspace_available
                        ? "Practice Desk is Live for this chat."
                        : snapshot.controls?.admin_message ?? "Practice Desk is currently Offline for this chat."}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={snapshot.controls?.workspace_available ? "success" : "danger"}>
                      {snapshot.controls?.workspace_available ? "Live" : "Offline"}
                    </Badge>
                    <Link href="/workspace">
                      <Button variant="secondary">
                        <DeskIcon className="h-4 w-4" />
                        Open Practice Desk
                      </Button>
                    </Link>
                  </div>
                </div>
              </Card>

              <Card className="space-y-5">
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Orchestration Logs</p>
                  <h2 className="text-2xl font-semibold tracking-[-0.03em] text-ink">Power Switch Activity</h2>
                  <p className="text-sm leading-6 text-slate-700">
                    Review how the Active Chat Power Switch and All Chats Power Switch changed availability for this Practice
                    Desk chat and for ClinicOS AI across the wider workspace.
                  </p>
                </div>

                <div className="space-y-3">
                  {snapshot.timeline.slice(0, 14).map((event) => (
                    <div key={event.event_id} className="rounded-[24px] border border-slate-200/85 bg-white/90 p-4">
                      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                        <p className="text-sm font-semibold text-ink">{event.stage}</p>
                        <Badge variant={logVariant(event.status)}>{logLabel(event.status)}</Badge>
                      </div>
                      <p className="text-sm leading-6 text-slate-700">{event.detail}</p>
                      <p className="mt-2 text-[11px] uppercase tracking-[0.14em] text-muted">{formatDate(event.timestamp)}</p>
                    </div>
                  ))}
                </div>

                <div className="space-y-3 rounded-[24px] border border-slate-200/85 bg-slate-50/70 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">Deleted Chat Archive</p>
                      <p className="mt-1 text-sm text-slate-700">
                        Deleted chats stay out of the normal UI but remain available here with the full archived transcript and audit trail.
                      </p>
                    </div>
                    <Badge variant="info">{deletedArchive.length} Archived</Badge>
                  </div>

                  <div className="max-h-[240px] space-y-2 overflow-y-auto pr-1">
                    {deletedArchive.length === 0 ? (
                      <div className="rounded-[20px] border border-dashed border-slate-200 bg-white/85 p-4 text-sm text-slate-500">
                        No deleted chats have been archived yet.
                      </div>
                    ) : (
                      deletedArchive.map((archive) => (
                        <div key={archive.id} className="flex flex-wrap items-center justify-between gap-3 rounded-[20px] border border-slate-200 bg-white/92 p-4">
                          <div className="space-y-1">
                            <p className="text-sm font-semibold text-ink">{archive.title ?? `Archived Chat #${archive.conversation_id}`}</p>
                            <p className="line-clamp-2 text-sm leading-6 text-slate-700">{archivePreview(archive.summary)}</p>
                            <p className="text-[11px] uppercase tracking-[0.14em] text-muted">
                              Deleted by {toTitleCaseLabel(archive.deleted_by)} • {formatDate(archive.created_at)}
                            </p>
                          </div>
                          <Button variant="secondary" onClick={() => setSelectedArchive(archive)}>
                            <ArchiveIcon className="h-4 w-4" />
                            View Archive
                          </Button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </Card>
            </>
          ) : (
            <Card>
              <p className="text-sm text-muted">Select a chat to load its Practice Profile, controls, and logs.</p>
            </Card>
          )}

          {error ? <p className="text-sm text-danger">{error}</p> : null}
        </section>
      </div>

      <Dialog open={Boolean(selectedArchive)} onClose={() => setSelectedArchive(null)} className="max-w-4xl">
        <div className="space-y-5">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Deleted Chat Archive</p>
              <h3 className="text-2xl font-semibold tracking-[-0.03em] text-ink">
                {selectedArchive?.title ?? (selectedArchive ? `Archived Chat #${selectedArchive.conversation_id}` : "Archive")}
              </h3>
              <p className="text-sm leading-6 text-slate-700">
                Deleted by {selectedArchive ? toTitleCaseLabel(selectedArchive.deleted_by) : "Unknown"} on{" "}
                {selectedArchive ? formatDate(selectedArchive.created_at) : ""}
              </p>
            </div>
            <Button variant="ghost" className="px-3 py-2 text-xs" onClick={() => setSelectedArchive(null)}>
              Close
            </Button>
          </div>

          <div className="grid gap-4 lg:grid-cols-[320px_minmax(0,1fr)]">
            <div className="space-y-4">
              <Card className="space-y-3 border-slate-200/85 bg-slate-50/70">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Archived Practice Profile</p>
                <div className="grid gap-3 text-sm leading-6 text-slate-700">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">Clinic Name</p>
                    <p>{selectedArchiveSnapshot?.case_snapshot?.clinic_memory?.clinic_name ?? "Unknown"}</p>
                  </div>
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">Practice Type</p>
                    <p>{selectedArchiveSnapshot?.case_snapshot?.clinic_memory?.practice_type ?? "Unknown"}</p>
                  </div>
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">Location</p>
                    <p>{selectedArchiveSnapshot?.case_snapshot?.clinic_memory?.location ?? "Unknown"}</p>
                  </div>
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">Providers</p>
                    <p>{selectedArchiveSnapshot?.case_snapshot?.clinic_memory?.providers ?? "Unknown"}</p>
                  </div>
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">Front Desk Staff</p>
                    <p>{selectedArchiveSnapshot?.case_snapshot?.clinic_memory?.front_desk_staff_count ?? "Unknown"}</p>
                  </div>
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">PMS / EHR</p>
                    <p>{selectedArchiveSnapshot?.case_snapshot?.clinic_memory?.pms_software ?? "Unknown"}</p>
                  </div>
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">Billing Status</p>
                    <p>{selectedArchiveSnapshot?.case_snapshot?.clinic_memory?.insurance_billing_status ?? "Unknown"}</p>
                  </div>
                </div>
              </Card>

              <Card className="space-y-3 border-slate-200/85 bg-slate-50/70">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Archive Audit Trail</p>
                <div className="max-h-[320px] space-y-2 overflow-y-auto pr-1">
                  {(selectedArchiveSnapshot?.event_logs ?? []).slice(0, 8).map((event) => (
                    <div key={event.id} className="rounded-[18px] border border-slate-200 bg-white/92 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-semibold text-ink">{event.stage}</p>
                        <Badge variant={logVariant(event.status)}>{logLabel(event.status)}</Badge>
                      </div>
                      <div className="mt-1 max-h-[96px] overflow-y-auto pr-1">
                        <p className="text-sm leading-6 text-slate-700">{archivePreview(event.detail, 260)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>

            <Card className="space-y-4 border-slate-200/85 bg-white">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Archived Transcript</p>
                <p className="mt-1 text-sm text-slate-700">
                  Messages removed from the normal UI remain available here for admin review.
                </p>
              </div>

              <div className="max-h-[520px] space-y-3 overflow-y-auto pr-1">
                {(selectedArchiveSnapshot?.messages ?? []).map((message) => (
                  <div key={message.id} className="rounded-[22px] border border-slate-200/85 bg-slate-50/70 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="text-sm font-semibold text-ink">{toTitleCaseLabel(message.role)}</p>
                      <p className="text-[11px] uppercase tracking-[0.14em] text-muted">{formatDate(message.created_at)}</p>
                    </div>
                    {message.agent_name ? (
                      <p className="mt-1 text-[11px] uppercase tracking-[0.14em] text-muted">
                        {message.agent_name} {message.workflow ? `• ${toTitleCaseLabel(message.workflow)}` : ""}
                      </p>
                    ) : null}
                    <div className="mt-3 max-h-[180px] overflow-y-auto pr-1">
                      <p className="whitespace-pre-wrap text-sm leading-6 text-slate-700">{message.content}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </Dialog>

      <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)} className="max-w-lg">
        <div className="space-y-5">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Delete Chat</p>
            <h3 className="text-2xl font-semibold tracking-[-0.03em] text-ink">Remove this chat from Practice Desk?</h3>
            <p className="text-sm leading-7 text-slate-700">
              This chat will disappear from the active workspace, but the full archive will remain available here for audit
              review.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-end gap-2">
            <Button variant="ghost" onClick={() => setDeleteConfirmOpen(false)} disabled={deletingThread}>
              Cancel
            </Button>
            <Button variant="danger" onClick={deleteChat} disabled={deletingThread}>
              {deletingThread ? "Deleting..." : "Delete Chat"}
            </Button>
          </div>
        </div>
      </Dialog>
    </>
  );
}
