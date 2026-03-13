"use client";

import { type FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { AdminPageSkeleton } from "@/components/admin/AdminPageSkeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { InfoIcon, MailIcon, MarketingIcon, PrintIcon, RefreshIcon, TrashIcon } from "@/components/ui/icons";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { CampaignDraft } from "@/lib/types";
import { formatDate } from "@/lib/utils";

type SuggestedCampaign = {
  audience: string;
  objective: string;
  notes: string;
};

const OBJECTIVES = [
  "Hygiene Recall Reactivation",
  "Implant Consult Promotion",
  "Invisalign Awareness",
  "Local Launch For Second Location",
  "Review Generation",
  "No-Show Reduction",
];

const SUGGESTED_CAMPAIGNS: SuggestedCampaign[] = [
  {
    audience: "Overdue hygiene patients with no visit in 9+ months",
    objective: "Hygiene Recall Reactivation",
    notes: "manual reminder backlog, open chair time next month, front desk needs lighter follow-up workload",
  },
  {
    audience: "High-value implant leads who asked for pricing but never booked",
    objective: "Implant Consult Promotion",
    notes: "strong consult interest, incomplete follow-up, need better confidence-building nurture",
  },
  {
    audience: "Satisfied patients from the last 30 days",
    objective: "Review Generation",
    notes: "practice wants more local reviews without adding more front-desk tasks",
  },
  {
    audience: "Families near a newly opened satellite office",
    objective: "Local Launch For Second Location",
    notes: "new market awareness, same-week availability, need a simple launch message",
  },
  {
    audience: "Patients with unfinished treatment plans over $2,500",
    objective: "Implant Consult Promotion",
    notes: "treatment acceptance stalled, financing concerns, front desk wants a softer nurture sequence",
  },
  {
    audience: "Patients with two or more missed hygiene visits",
    objective: "No-Show Reduction",
    notes: "late cancellations, schedule gaps, need a stronger reminder and recovery flow",
  },
  {
    audience: "Parents who inquired about Invisalign but did not book",
    objective: "Invisalign Awareness",
    notes: "price hesitation, no follow-up sequence, need higher consult conversion",
  },
  {
    audience: "Established dermatology patients due for annual skin checks",
    objective: "Review Generation",
    notes: "summer volume ramp, preventive care reminders, low recent patient engagement",
  },
];

function pickSuggestedCampaigns(previousAudiences: string[] = []) {
  const previous = new Set(previousAudiences);
  for (let attempt = 0; attempt < 6; attempt += 1) {
    const next = [...SUGGESTED_CAMPAIGNS].sort(() => Math.random() - 0.5).slice(0, 4);
    if (next.some((item) => !previous.has(item.audience))) {
      return next;
    }
  }
  return [...SUGGESTED_CAMPAIGNS].sort(() => Math.random() - 0.5).slice(0, 4);
}

function CampaignPlanSkeleton() {
  return (
    <Card className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-3">
          <div className="shimmer-line h-7 w-28 rounded-full" />
          <div className="shimmer-line h-9 w-80 rounded-full" />
          <div className="shimmer-line h-4 w-64 rounded-full" />
        </div>
        <div className="shimmer-line h-4 w-32 rounded-full" />
      </div>

      <div className="rounded-[22px] border border-slate-200/85 bg-slate-50/75 p-4">
        <div className="shimmer-line h-3 w-28 rounded-full" />
        <div className="mt-4 space-y-3">
          <div className="shimmer-line h-3 w-full rounded-full" />
          <div className="shimmer-line h-3 w-full rounded-full" />
          <div className="shimmer-line h-3 w-5/6 rounded-full" />
          <div className="shimmer-line h-3 w-4/5 rounded-full" />
        </div>
      </div>

      <div className="rounded-[22px] border border-slate-200/85 bg-slate-50/75 p-4">
        <div className="shimmer-line h-3 w-32 rounded-full" />
        <div className="mt-4 space-y-3">
          <div className="shimmer-line h-24 w-full rounded-[18px]" />
          <div className="shimmer-line h-24 w-full rounded-[18px]" />
        </div>
      </div>
    </Card>
  );
}

function escapeHtml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function campaignSteps(campaign: CampaignDraft) {
  return (campaign.nurture_sequence_json ?? []).map((step, index) => ({
    title: String((step.subject as string) ?? (step.title as string) ?? `Campaign Step ${index + 1}`),
    body: String(step.body ?? ""),
    index,
  }));
}

export function MarketingWorkspace() {
  const [audience, setAudience] = useState("");
  const [objective, setObjective] = useState("");
  const [segmentNotes, setSegmentNotes] = useState("");
  const [campaigns, setCampaigns] = useState<CampaignDraft[]>([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState<number | null>(null);
  const [suggestedCampaigns, setSuggestedCampaigns] = useState(() => pickSuggestedCampaigns());
  const [guideOpen, setGuideOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [pendingDeleteCampaign, setPendingDeleteCampaign] = useState<CampaignDraft | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [scrollToResult, setScrollToResult] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const resultRef = useRef<HTMLDivElement | null>(null);

  async function loadCampaigns(preferredId?: number | null) {
    const list = await api.listCampaignDrafts();
    setCampaigns(list);
    const nextSelectedId =
      preferredId && list.some((item) => item.id === preferredId)
        ? preferredId
        : list[0]?.id ?? null;
    setSelectedCampaignId(nextSelectedId);
  }

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      try {
        setLoading(true);
        await loadCampaigns();
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Failed to load Marketing");
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
    if (!scrollToResult || !resultRef.current) return;
    resultRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    setScrollToResult(false);
  }, [scrollToResult, selectedCampaignId, generating]);

  async function generateCampaign(event?: FormEvent, override?: SuggestedCampaign) {
    event?.preventDefault();
    const nextAudience = (override?.audience ?? audience).trim();
    const nextObjective = override?.objective ?? objective;
    const nextNotes = (override?.notes ?? segmentNotes).trim();
    if (!nextAudience || !nextObjective) return;

    setGenerating(true);
    setError(null);
    setAudience(nextAudience);
    setObjective(nextObjective);
    setSegmentNotes(nextNotes);

    try {
      const result = await api.generateMarketing(nextAudience, nextObjective, nextNotes || undefined);
      await loadCampaigns(result.id);
      setScrollToResult(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate the campaign plan");
    } finally {
      setGenerating(false);
    }
  }

  async function deleteCampaignPlan() {
    const target = pendingDeleteCampaign;
    if (!target || deleting) return;

    const fallbackId =
      selectedCampaignId === target.id
        ? campaigns.find((item) => item.id !== target.id)?.id ?? null
        : selectedCampaignId;
    setDeleting(true);
    setError(null);

    try {
      await api.deleteMarketingPlan(target.id);
      await loadCampaigns(fallbackId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete the campaign plan");
    } finally {
      setDeleting(false);
      setDeleteConfirmOpen(false);
      setPendingDeleteCampaign(null);
    }
  }

  const selectedCampaign = useMemo(
    () => campaigns.find((item) => item.id === selectedCampaignId) ?? campaigns[0] ?? null,
    [campaigns, selectedCampaignId]
  );

  const campaignCountLabel = useMemo(
    () => `${campaigns.length} ${campaigns.length === 1 ? "Campaign Plan" : "Campaign Plans"}`,
    [campaigns.length]
  );

  function downloadCampaignPdf(campaign: CampaignDraft) {
    const iframe = document.createElement("iframe");
    iframe.setAttribute("aria-hidden", "true");
    iframe.style.position = "fixed";
    iframe.style.right = "0";
    iframe.style.bottom = "0";
    iframe.style.width = "0";
    iframe.style.height = "0";
    iframe.style.border = "0";
    document.body.appendChild(iframe);

    const steps = campaignSteps(campaign);
    const sequenceHtml = steps
      .map(
        (step) => `
          <section style="margin-top:20px;padding:16px;border:1px solid #dbe5ec;border-radius:16px;">
            <p style="margin:0 0 8px;font-size:11px;letter-spacing:0.12em;text-transform:uppercase;color:#5b6471;">Step ${step.index + 1}</p>
            <h3 style="margin:0 0 10px;font-size:18px;color:#11233b;">${escapeHtml(step.title)}</h3>
            <p style="margin:0;white-space:pre-wrap;line-height:1.7;color:#334155;">${escapeHtml(step.body)}</p>
          </section>
        `
      )
      .join("");
    const doc = iframe.contentWindow?.document;
    if (!doc) {
      document.body.removeChild(iframe);
      return;
    }

    doc.open();
    doc.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>${escapeHtml(campaign.title)}</title>
          <style>
            @page { size: auto; margin: 18mm; }
            body { font-family: Georgia, "Times New Roman", serif; padding: 24px; color: #11233b; }
          </style>
        </head>
        <body>
          <p style="margin:0 0 8px;font-size:12px;letter-spacing:0.16em;text-transform:uppercase;color:#5b6471;">ClinicOS Marketing</p>
          <h1 style="margin:0 0 10px;font-size:32px;">${escapeHtml(campaign.title)}</h1>
          <p style="margin:0 0 24px;color:#475569;">${escapeHtml(campaign.audience)} • ${escapeHtml(campaign.channel)}</p>
          <section style="padding:18px;border:1px solid #dbe5ec;border-radius:18px;background:#f8fafc;">
            <p style="margin:0 0 10px;font-size:11px;letter-spacing:0.12em;text-transform:uppercase;color:#5b6471;">Campaign Brief</p>
            <p style="margin:0;white-space:pre-wrap;line-height:1.75;color:#334155;">${escapeHtml(campaign.brief)}</p>
          </section>
          <section style="margin-top:24px;">
            <p style="margin:0 0 12px;font-size:11px;letter-spacing:0.12em;text-transform:uppercase;color:#5b6471;">Nurture Sequence</p>
            ${sequenceHtml || "<p style='color:#64748b;'>No nurture sequence steps were generated for this plan.</p>"}
          </section>
        </body>
      </html>
    `);
    doc.close();

    window.setTimeout(() => {
      const frameWindow = iframe.contentWindow;
      if (!frameWindow) {
        document.body.removeChild(iframe);
        return;
      }
      frameWindow.focus();
      frameWindow.print();
      window.setTimeout(() => {
        if (document.body.contains(iframe)) {
          document.body.removeChild(iframe);
        }
      }, 1200);
    }, 250);
  }

  const draftEmailHref = selectedCampaign
    ? `mailto:?subject=${encodeURIComponent(`Campaign Plan: ${selectedCampaign.title}`)}&body=${encodeURIComponent(
        [
          "Hi team,",
          "",
          `Here is the ClinicOS campaign plan for ${selectedCampaign.title}.`,
          "",
          `Audience: ${selectedCampaign.audience}`,
          `Primary Channel: ${selectedCampaign.channel}`,
          "",
          "Campaign Brief:",
          selectedCampaign.brief,
          "",
          "Nurture Sequence:",
          ...(campaignSteps(selectedCampaign).length > 0
            ? campaignSteps(selectedCampaign).flatMap((step) => [`Step ${step.index + 1}: ${step.title}`, step.body, ""])
            : ["No nurture sequence steps were generated for this plan.", ""]),
        ].join("\n")
      )}`
    : "#";

  if (loading) {
    return <AdminPageSkeleton />;
  }

  return (
    <>
      <div className="grid gap-6 xl:grid-cols-[320px_minmax(0,1.45fr)_320px]">
        <aside className="space-y-4">
          <Card className="space-y-4">
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Guidance</p>
              <h3 className="text-lg font-semibold tracking-[-0.02em] text-ink">How It Works</h3>
              <p className="text-sm leading-6 text-slate-700">
                Turn one clinic growth goal into a usable campaign brief with a clearer audience, stronger context, and a practical nurture plan.
              </p>
            </div>
            <Button variant="secondary" className="w-full" onClick={() => setGuideOpen(true)}>
              <InfoIcon className="h-4 w-4" />
              How Marketing Tool Works
            </Button>
          </Card>

          <Card className="space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Campaign History</p>
                <p className="mt-1 text-sm text-slate-600">{campaignCountLabel}</p>
              </div>
              <Badge variant="info">Saved</Badge>
            </div>

            <div className="max-h-[540px] space-y-2 overflow-y-auto pr-1">
              {campaigns.length === 0 ? (
                <div className="rounded-[22px] border border-dashed border-slate-200 bg-slate-50/80 p-4 text-sm leading-6 text-slate-500">
                  Generated campaign plans will appear here after you build the first one.
                </div>
              ) : (
                campaigns.map((campaign) => {
                  const active = selectedCampaign?.id === campaign.id;
                  return (
                    <div
                      key={campaign.id}
                      className={`w-full rounded-[22px] border p-4 text-left transition ${
                        active
                          ? "border-emerald-200 bg-[linear-gradient(180deg,rgba(237,252,248,0.98),rgba(255,255,255,0.98))] shadow-[0_18px_40px_rgba(13,118,104,0.12)]"
                          : "border-slate-200/85 bg-white/92 hover:border-slate-300 hover:bg-white"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <button type="button" onClick={() => setSelectedCampaignId(campaign.id)} className="min-w-0 flex-1 text-left">
                          <Badge variant="success">Campaign Plan</Badge>
                          <p className="mt-3 line-clamp-2 text-sm font-semibold leading-6 text-ink">{campaign.title}</p>
                          <p className="line-clamp-2 text-sm leading-6 text-slate-700">{campaign.brief}</p>
                          <p className="mt-2 text-[11px] uppercase tracking-[0.14em] text-muted">
                            {formatDate(campaign.updated_at ?? campaign.created_at)}
                          </p>
                        </button>
                        <button
                          type="button"
                          aria-label={`Delete ${campaign.title}`}
                          onClick={() => {
                            setPendingDeleteCampaign(campaign);
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

        <section className="space-y-4">
          <Card className="space-y-5 border-accent/20 bg-[linear-gradient(135deg,rgba(236,253,245,0.96),rgba(255,255,255,0.98),rgba(239,246,255,0.95))]">
            <div className="space-y-3">
              <Badge variant="warning">Marketing</Badge>
              <h2 className="text-3xl font-semibold tracking-[-0.03em] text-ink">Build a campaign plan that fits the clinic you are growing</h2>
              <p className="max-w-2xl text-sm leading-6 text-slate-700">
                Define the audience, the growth objective, and the operational context behind the campaign. ClinicOS will turn that into a sharper brief and a campaign sequence the team can actually use.
              </p>
            </div>

            <form className="space-y-4" onSubmit={generateCampaign}>
              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-xs font-semibold uppercase tracking-[0.1em] text-muted">Audience</label>
                  <Input
                    value={audience}
                    onChange={(event) => setAudience(event.target.value)}
                    placeholder="Example: Overdue hygiene patients with no visit in 9+ months"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold uppercase tracking-[0.1em] text-muted">Campaign Objective</label>
                  <select
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-ink outline-none ring-accent focus:border-accent focus:ring-2"
                    value={objective}
                    onChange={(event) => setObjective(event.target.value)}
                  >
                    <option value="" disabled>
                      Choose an objective
                    </option>
                    {OBJECTIVES.map((item) => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold uppercase tracking-[0.1em] text-muted">Segment Notes</label>
                <Input
                  value={segmentNotes}
                  onChange={(event) => setSegmentNotes(event.target.value)}
                  placeholder="Example: open chair time next month, low recent engagement, manual reminder backlog, softer financing language needed"
                />
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3 rounded-[22px] border border-white/75 bg-white/88 px-4 py-3">
                <p className="text-sm leading-6 text-slate-700">
                  Start with a clinic growth problem you want to solve, or use a Suggested Campaign on the right for a faster brief.
                </p>
                <Button type="submit" disabled={generating || !audience.trim() || !objective}>
                  <MarketingIcon className="h-4 w-4" />
                  {generating ? "Generating Campaign..." : "Generate Campaign Plan"}
                </Button>
              </div>
            </form>
          </Card>

          <div ref={resultRef}>
            {generating ? (
              <CampaignPlanSkeleton />
            ) : selectedCampaign ? (
              <Card className="space-y-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <Badge variant="success">Campaign Plan</Badge>
                    <h3 className="mt-3 text-2xl font-semibold tracking-[-0.03em] text-ink">{selectedCampaign.title}</h3>
                    <p className="mt-1 text-sm text-slate-600">
                      {selectedCampaign.audience} • {selectedCampaign.channel}
                    </p>
                  </div>
                  <div className="flex min-w-[240px] flex-col items-start gap-2 sm:items-end">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">
                      Updated {formatDate(selectedCampaign.updated_at ?? selectedCampaign.created_at)}
                    </p>
                    <div className="flex flex-wrap items-center gap-2">
                      <Button variant="secondary" type="button" onClick={() => downloadCampaignPdf(selectedCampaign)}>
                        <PrintIcon className="h-4 w-4" />
                        PDF
                      </Button>
                      <Button
                        variant="secondary"
                        type="button"
                        onClick={() => {
                          window.location.href = draftEmailHref;
                        }}
                      >
                        <MailIcon className="h-4 w-4" />
                        Draft Email
                      </Button>
                      <Button
                        variant="secondary"
                        type="button"
                        className="border-rose-200/90 bg-rose-50/70 text-rose-700 hover:border-rose-300 hover:bg-rose-50"
                        onClick={() => {
                          setPendingDeleteCampaign(selectedCampaign);
                          setDeleteConfirmOpen(true);
                        }}
                      >
                        <TrashIcon className="h-4 w-4" />
                        Delete Plan
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="rounded-[22px] border border-slate-200/85 bg-slate-50/75 p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">Campaign Brief</p>
                  <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">{selectedCampaign.brief}</p>
                </div>

                <div className="rounded-[22px] border border-slate-200/85 bg-slate-50/75 p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">Nurture Sequence</p>
                  {(selectedCampaign.nurture_sequence_json ?? []).length > 0 ? (
                    <div className="mt-3 space-y-3">
                      {(selectedCampaign.nurture_sequence_json ?? []).map((step, index) => (
                        <div key={`${selectedCampaign.id}-${index}`} className="rounded-[18px] border border-slate-200 bg-white/92 p-4">
                          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">Step {index + 1}</p>
                          <p className="mt-2 text-sm font-semibold text-ink">
                            {(step.subject as string) ?? (step.title as string) ?? `Campaign Step ${index + 1}`}
                          </p>
                          {step.body ? (
                            <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">{String(step.body)}</p>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-3 text-sm text-slate-500">No nurture sequence steps were generated for this plan.</p>
                  )}
                </div>
              </Card>
            ) : (
              <Card>
                <p className="text-sm leading-6 text-muted">
                  Generate a campaign plan to see the brief and the nurture sequence here.
                </p>
              </Card>
            )}
          </div>

          {error ? <p className="text-sm text-danger">{error}</p> : null}
        </section>

        <aside className="space-y-4">
          <Card className="space-y-4">
            <div className="flex items-center justify-between gap-2">
              <div>
                <h3 className="text-lg font-semibold tracking-[-0.02em] text-ink">Suggested Campaigns</h3>
                <p className="text-sm text-slate-600">Jump into realistic clinic growth plays without starting from a blank page.</p>
              </div>
              <Button
                variant="ghost"
                className="px-3 py-2 text-xs"
                onClick={() => setSuggestedCampaigns((current) => pickSuggestedCampaigns(current.map((item) => item.audience)))}
              >
                <RefreshIcon className="h-4 w-4" />
                Refresh
              </Button>
            </div>

            <div className="grid gap-3">
              {suggestedCampaigns.map((item) => (
                <button
                  key={`${item.audience}-${item.objective}`}
                  type="button"
                  onClick={() => generateCampaign(undefined, item)}
                  disabled={generating}
                  className="rounded-[24px] border border-slate-200/85 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(247,250,252,0.95))] p-4 text-left transition hover:-translate-y-0.5 hover:border-emerald-200 hover:shadow-[0_20px_45px_rgba(15,23,42,0.08)] disabled:cursor-not-allowed disabled:opacity-55"
                >
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">{item.objective}</p>
                  <p className="mt-2 text-sm font-semibold leading-6 text-ink">{item.audience}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-700">{item.notes}</p>
                </button>
              ))}
            </div>
          </Card>
        </aside>
      </div>

      <Dialog open={guideOpen} onClose={() => setGuideOpen(false)} className="max-w-2xl">
        <div className="space-y-5">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Marketing</p>
              <h3 className="text-2xl font-semibold tracking-[-0.03em] text-ink">How Marketing Tool Works</h3>
            </div>
            <Button variant="ghost" className="px-3 py-2 text-xs" onClick={() => setGuideOpen(false)}>
              Close
            </Button>
          </div>

          <div className="space-y-4 text-sm leading-7 text-slate-700">
            <p>
              Start with a clear audience and one concrete growth objective so the campaign stays tied to a real clinic need
              instead of drifting into generic promotion.
            </p>
            <p>
              Segment notes help the plan stay grounded in operational context such as no-show recovery, overdue recall,
              front-desk bandwidth, review generation, or local demand for a new location.
            </p>
            <p>
              Use Campaign History to revisit older plans, and Suggested Campaigns when you want a faster starting point for
              realistic dental and medical practice workflows.
            </p>
            <p>
              Use email when the campaign needs context or a softer nurture path. Keep SMS more selective for timely reminders,
              schedule recovery, or shorter follow-up moments.
            </p>
          </div>
        </div>
      </Dialog>

      <Dialog
        open={deleteConfirmOpen}
        onClose={() => {
          setDeleteConfirmOpen(false);
          setPendingDeleteCampaign(null);
        }}
        className="max-w-lg"
      >
        <div className="space-y-5">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Delete Campaign Plan</p>
            <h3 className="text-2xl font-semibold tracking-[-0.03em] text-ink">Remove this campaign plan permanently?</h3>
            <p className="text-sm leading-7 text-slate-700">
              {pendingDeleteCampaign
                ? `This will permanently delete "${pendingDeleteCampaign.title}" from Marketing history with no archive.`
                : "This campaign plan will be deleted permanently from Marketing history with no archive."}
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-end gap-2">
            <Button
              variant="ghost"
              onClick={() => {
                setDeleteConfirmOpen(false);
                setPendingDeleteCampaign(null);
              }}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button variant="danger" onClick={deleteCampaignPlan} disabled={deleting}>
              {deleting ? "Deleting..." : "Delete Plan"}
            </Button>
          </div>
        </div>
      </Dialog>
    </>
  );
}
