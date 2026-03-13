"use client";

import { type FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { AdminPageSkeleton } from "@/components/admin/AdminPageSkeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { InfoIcon, MailIcon, RefreshIcon, SearchIcon, TrashIcon } from "@/components/ui/icons";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { SalesResearchHistoryItem } from "@/lib/types";
import { formatDate } from "@/lib/utils";

type SuggestedResearch = {
  clinicName: string;
  location: string;
  description: string;
};

const SUGGESTED_RESEARCHES: SuggestedResearch[] = [
  {
    clinicName: "Harbor Pediatric Dentistry",
    location: "Tampa, FL",
    description: "Research a pediatric clinic and build outreach around reminder automation, front-desk strain, and family scheduling.",
  },
  {
    clinicName: "Northgate Orthopedics",
    location: "Charlotte, NC",
    description: "Score a specialty group where referral leakage, utilization, and patient follow-up likely shape the sales angle.",
  },
  {
    clinicName: "Lakeside Family Dental",
    location: "Nashville, TN",
    description: "Assess a multi-provider dental clinic for recall automation, claims visibility, and better front-office consistency.",
  },
  {
    clinicName: "Summit Dermatology Partners",
    location: "Phoenix, AZ",
    description: "Evaluate fit for a fast-paced dermatology clinic and draft outreach around reviews, volume, and check-in flow.",
  },
  {
    clinicName: "Riverbend Eye Clinic",
    location: "Columbus, OH",
    description: "Research a medical prospect where schedule recovery, no-show reduction, and intake speed may be strong entry points.",
  },
  {
    clinicName: "Westbrook Oral Surgery",
    location: "Denver, CO",
    description: "Qualify a specialty dental practice around referral coordination, treatment acceptance, and premium consult throughput.",
  },
  {
    clinicName: "Cedar Women's Health",
    location: "Raleigh, NC",
    description: "Look at staffing pressure, patient communication delays, and whether growth readiness makes this clinic a better fit now.",
  },
  {
    clinicName: "Brighton Implant Center",
    location: "San Diego, CA",
    description: "Shape a more consultative first touch for an implant practice that likely cares about follow-up speed and conversion.",
  },
  {
    clinicName: "Maple Family Medicine",
    location: "Minneapolis, MN",
    description: "Assess if workflow friction, open schedule capacity, and patient re-engagement needs justify outbound outreach now.",
  },
  {
    clinicName: "Oakpoint Dermatology",
    location: "Austin, TX",
    description: "Research engagement signals and likely operational pain around appointment demand, reminders, and online reputation.",
  },
  {
    clinicName: "Crescent Endodontics",
    location: "Atlanta, GA",
    description: "Find the best prospect story around referral response time, specialty conversion, and front-office coordination.",
  },
  {
    clinicName: "Bluebird Allergy & Asthma",
    location: "Seattle, WA",
    description: "Score fit for a clinic that may benefit from faster follow-up, easier reminders, and fewer missed visits.",
  },
];

function pickSuggestedResearches(previousNames: string[] = []) {
  const previous = new Set(previousNames);
  for (let attempt = 0; attempt < 6; attempt += 1) {
    const next = [...SUGGESTED_RESEARCHES].sort(() => Math.random() - 0.5).slice(0, 4);
    if (next.some((item) => !previous.has(item.clinicName))) {
      return next;
    }
  }
  return [...SUGGESTED_RESEARCHES].sort(() => Math.random() - 0.5).slice(0, 4);
}

function fitVariant(score: number | null | undefined): "success" | "warning" | "danger" {
  const value = score ?? 0;
  if (value >= 75) return "success";
  if (value >= 55) return "warning";
  return "danger";
}

function historyTitle(item: SalesResearchHistoryItem) {
  return `${item.clinic_name}${item.location ? `, ${item.location}` : ""}`;
}

function ResearchResultSkeleton() {
  return (
    <Card className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-3">
          <div className="flex gap-2">
            <div className="shimmer-line h-7 w-24 rounded-full" />
            <div className="shimmer-line h-7 w-36 rounded-full" />
          </div>
          <div className="shimmer-line h-9 w-72 rounded-full" />
          <div className="shimmer-line h-4 w-56 rounded-full" />
        </div>
        <div className="shimmer-line h-4 w-32 rounded-full" />
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-[22px] border border-slate-200/85 bg-slate-50/75 p-4">
          <div className="shimmer-line h-3 w-28 rounded-full" />
          <div className="mt-4 space-y-3">
            <div className="shimmer-line h-3 w-full rounded-full" />
            <div className="shimmer-line h-3 w-5/6 rounded-full" />
            <div className="shimmer-line h-3 w-2/3 rounded-full" />
          </div>
        </div>
        <div className="rounded-[22px] border border-slate-200/85 bg-slate-50/75 p-4">
          <div className="shimmer-line h-3 w-36 rounded-full" />
          <div className="mt-4 space-y-3">
            <div className="shimmer-line h-3 w-full rounded-full" />
            <div className="shimmer-line h-3 w-full rounded-full" />
            <div className="shimmer-line h-3 w-4/5 rounded-full" />
          </div>
        </div>
      </div>

      <div className="rounded-[26px] border border-slate-200/85 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(247,250,252,0.96))] p-5">
        <div className="flex items-center justify-between gap-3">
          <div className="space-y-3">
            <div className="shimmer-line h-3 w-36 rounded-full" />
            <div className="shimmer-line h-7 w-80 rounded-full" />
          </div>
          <div className="shimmer-line h-7 w-24 rounded-full" />
        </div>
        <div className="mt-5 space-y-3">
          <div className="shimmer-line h-3 w-full rounded-full" />
          <div className="shimmer-line h-3 w-full rounded-full" />
          <div className="shimmer-line h-3 w-5/6 rounded-full" />
          <div className="shimmer-line h-3 w-4/5 rounded-full" />
        </div>
      </div>
    </Card>
  );
}

export function SalesWorkspace() {
  const [clinicName, setClinicName] = useState("");
  const [location, setLocation] = useState("");
  const [history, setHistory] = useState<SalesResearchHistoryItem[]>([]);
  const [selectedHistoryId, setSelectedHistoryId] = useState<number | null>(null);
  const [suggestedResearches, setSuggestedResearches] = useState(() => pickSuggestedResearches());
  const [guideOpen, setGuideOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [pendingDeleteResearch, setPendingDeleteResearch] = useState<SalesResearchHistoryItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [researching, setResearching] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [scrollToResult, setScrollToResult] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const resultRef = useRef<HTMLDivElement | null>(null);

  async function loadHistory(preferredId?: number | null) {
    const items = await api.listSalesResearchHistory();
    setHistory(items);

    const nextSelectedId =
      preferredId && items.some((item) => item.id === preferredId)
        ? preferredId
        : items[0]?.id ?? null;
    setSelectedHistoryId(nextSelectedId);
  }

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      try {
        setLoading(true);
        await loadHistory();
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Failed to load Sales & Outreach");
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
  }, [scrollToResult, selectedHistoryId, researching]);

  async function runResearch(event?: FormEvent, override?: SuggestedResearch) {
    event?.preventDefault();
    const nextClinicName = (override?.clinicName ?? clinicName).trim();
    const nextLocation = (override?.location ?? location).trim();
    if (!nextClinicName) return;

    setResearching(true);
    setError(null);
    setClinicName(nextClinicName);
    setLocation(nextLocation);

    try {
      const result = await api.salesResearch(nextClinicName, nextLocation || undefined);
      await loadHistory(result.outreach_draft.id);
      setScrollToResult(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run sales research");
    } finally {
      setResearching(false);
    }
  }

  async function deleteResearch() {
    const target = pendingDeleteResearch;
    if (!target || deleting) return;

    const fallbackId =
      selectedHistoryId === target.id
        ? history.find((item) => item.id !== target.id)?.id ?? null
        : selectedHistoryId;
    setDeleting(true);
    setError(null);

    try {
      await api.deleteSalesResearchHistory(target.id);
      await loadHistory(fallbackId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete sales research");
    } finally {
      setDeleting(false);
      setDeleteConfirmOpen(false);
      setPendingDeleteResearch(null);
    }
  }

  const selectedResearch = useMemo(
    () => history.find((item) => item.id === selectedHistoryId) ?? history[0] ?? null,
    [history, selectedHistoryId]
  );

  const historyCountLabel = useMemo(
    () => `${history.length} ${history.length === 1 ? "Saved Prospect" : "Saved Prospects"}`,
    [history.length]
  );

  const draftEmailHref = selectedResearch
    ? `mailto:?subject=${encodeURIComponent(selectedResearch.outreach_subject)}&body=${encodeURIComponent(selectedResearch.outreach_body)}`
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
                Research a real clinic before outreach starts. ClinicOS scores likely fit, surfaces operational signals,
                and drafts a more personal first message for the rep.
              </p>
            </div>
            <Button variant="secondary" className="w-full" onClick={() => setGuideOpen(true)}>
              <InfoIcon className="h-4 w-4" />
              How Sales & Outreach Tool Works
            </Button>
          </Card>

          <Card className="space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Research History</p>
                <p className="mt-1 text-sm text-slate-600">{historyCountLabel}</p>
              </div>
              <Badge variant="info">Saved</Badge>
            </div>

            <div className="max-h-[540px] space-y-2 overflow-y-auto pr-1">
              {history.length === 0 ? (
                <div className="rounded-[22px] border border-dashed border-slate-200 bg-slate-50/80 p-4 text-sm leading-6 text-slate-500">
                  Past prospect research will appear here after you score your first clinic.
                </div>
              ) : (
                history.map((item) => {
                  const active = selectedResearch?.id === item.id;
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
                        <button type="button" onClick={() => setSelectedHistoryId(item.id)} className="min-w-0 flex-1 text-left">
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant={fitVariant(item.fit_score)}>Fit {item.fit_score ?? "N/A"}</Badge>
                            <Badge variant={item.existing_lead ? "success" : "info"}>
                              {item.existing_lead ? "Expansion" : "Net-New"}
                            </Badge>
                          </div>
                          <p className="mt-3 line-clamp-2 text-sm font-semibold leading-6 text-ink">{historyTitle(item)}</p>
                          <p className="line-clamp-2 text-sm leading-6 text-slate-700">
                            {item.research_summary ?? "No research summary saved for this clinic yet."}
                          </p>
                          <p className="mt-2 text-[11px] uppercase tracking-[0.14em] text-muted">{formatDate(item.updated_at)}</p>
                        </button>
                        <button
                          type="button"
                          aria-label={`Delete ${historyTitle(item)}`}
                          onClick={() => {
                            setPendingDeleteResearch(item);
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
              <Badge variant="info">Sales & Outreach</Badge>
              <h2 className="text-3xl font-semibold tracking-[-0.03em] text-ink">Research a clinic before your rep reaches out</h2>
              <p className="max-w-2xl text-sm leading-6 text-slate-700">
                Start with the exact practice you want to understand. ClinicOS will profile the prospect, score the fit,
                and draft a personalized outreach message that sounds grounded in the clinic’s real operating pressures.
              </p>
            </div>

            <form className="space-y-4" onSubmit={runResearch}>
              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-xs font-semibold uppercase tracking-[0.1em] text-muted">Prospect Clinic</label>
                  <Input
                    value={clinicName}
                    onChange={(event) => setClinicName(event.target.value)}
                    placeholder="Example: Lakeside Family Dental, Brighton Implant Center, or Northgate Orthopedics"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold uppercase tracking-[0.1em] text-muted">Location</label>
                  <Input
                    value={location}
                    onChange={(event) => setLocation(event.target.value)}
                    placeholder="Example: Nashville, TN, Austin, TX, or Charlotte, NC"
                  />
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3 rounded-[22px] border border-white/75 bg-white/88 px-4 py-3">
                <p className="text-sm leading-6 text-slate-700">
                  Use a clinic name and market if you already know the target, or start from Suggested Researches on the right.
                </p>
                <Button type="submit" disabled={researching || !clinicName.trim()}>
                  <SearchIcon className="h-4 w-4" />
                  {researching ? "Researching Clinic..." : "Research Clinic"}
                </Button>
              </div>
            </form>
          </Card>

          <div ref={resultRef}>
            {researching ? (
              <ResearchResultSkeleton />
            ) : selectedResearch ? (
              <Card className="space-y-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant={fitVariant(selectedResearch.fit_score)}>Fit Score {selectedResearch.fit_score ?? "N/A"}</Badge>
                      <Badge variant={selectedResearch.existing_lead ? "success" : "info"}>
                        {selectedResearch.existing_lead ? "Existing Account Expansion" : "Net-New Prospect"}
                      </Badge>
                    </div>
                    <h3 className="mt-3 text-2xl font-semibold tracking-[-0.03em] text-ink">{selectedResearch.clinic_name}</h3>
                    <p className="mt-1 text-sm text-slate-600">
                      {selectedResearch.location ?? "Location not captured"} • {selectedResearch.specialty ?? selectedResearch.clinic_type}
                    </p>
                  </div>
                  <div className="flex min-w-[220px] flex-col items-start gap-2 sm:items-end">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">
                      Last Researched {formatDate(selectedResearch.updated_at)}
                    </p>
                    <Button
                      variant="secondary"
                      className="border-rose-200/90 bg-rose-50/70 text-rose-700 hover:border-rose-300 hover:bg-rose-50"
                      onClick={() => {
                        setPendingDeleteResearch(selectedResearch);
                        setDeleteConfirmOpen(true);
                      }}
                    >
                      <TrashIcon className="h-4 w-4" />
                      Delete Research
                    </Button>
                  </div>
                </div>

                <div className="grid gap-3 md:grid-cols-2">
                  <div className="rounded-[22px] border border-slate-200/85 bg-slate-50/75 p-4">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">Practice Snapshot</p>
                    <div className="mt-3 grid gap-2 text-sm text-slate-700">
                      <p><span className="font-semibold text-ink">Clinic Type:</span> {selectedResearch.clinic_type}</p>
                      <p><span className="font-semibold text-ink">Specialty:</span> {selectedResearch.specialty ?? "Not captured"}</p>
                      <p><span className="font-semibold text-ink">Size:</span> {selectedResearch.size_estimate ?? "Not captured"}</p>
                      <p><span className="font-semibold text-ink">Location:</span> {selectedResearch.location ?? "Not captured"}</p>
                    </div>
                  </div>
                  <div className="rounded-[22px] border border-slate-200/85 bg-slate-50/75 p-4">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">Research Brief</p>
                    <p className="mt-3 text-sm leading-6 text-slate-700">
                      {selectedResearch.research_summary ?? "No research summary saved for this clinic yet."}
                    </p>
                  </div>
                </div>

                <div className="rounded-[22px] border border-slate-200/85 bg-slate-50/75 p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">Operating Signals</p>
                  {selectedResearch.pain_points_json?.length ? (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {selectedResearch.pain_points_json.map((signal) => (
                        <span key={signal} className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-700">
                          {signal}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-3 text-sm text-slate-500">No specific operating signals were captured for this research run.</p>
                  )}
                </div>

                <div className="rounded-[26px] border border-slate-200/85 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(247,250,252,0.96))] p-5 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">Personalized Outreach</p>
                      <h4 className="mt-2 text-xl font-semibold tracking-[-0.02em] text-ink">{selectedResearch.outreach_subject}</h4>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
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
                      <Badge variant="success">Ready To Use</Badge>
                    </div>
                  </div>
                  <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-700">{selectedResearch.outreach_body}</p>
                </div>
              </Card>
            ) : (
              <Card>
                <p className="text-sm leading-6 text-muted">
                  Research a clinic to generate the fit score, the research brief, and the personalized outreach message here.
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
                <h3 className="text-lg font-semibold tracking-[-0.02em] text-ink">Suggested Researches</h3>
                <p className="text-sm text-slate-600">Start from realistic dental and medical clinics when you want faster prospecting momentum.</p>
              </div>
              <Button
                variant="ghost"
                className="px-3 py-2 text-xs"
                onClick={() => setSuggestedResearches((current) => pickSuggestedResearches(current.map((item) => item.clinicName)))}
              >
                <RefreshIcon className="h-4 w-4" />
                Refresh
              </Button>
            </div>

            <div className="grid gap-3">
              {suggestedResearches.map((item) => (
                <button
                  key={`${item.clinicName}-${item.location}`}
                  type="button"
                  onClick={() => runResearch(undefined, item)}
                  disabled={researching}
                  className="rounded-[24px] border border-slate-200/85 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(247,250,252,0.95))] p-4 text-left transition hover:-translate-y-0.5 hover:border-emerald-200 hover:shadow-[0_20px_45px_rgba(15,23,42,0.08)] disabled:cursor-not-allowed disabled:opacity-55"
                >
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">{item.location}</p>
                  <p className="mt-2 text-sm font-semibold leading-6 text-ink">{item.clinicName}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-700">{item.description}</p>
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
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Sales & Outreach</p>
              <h3 className="text-2xl font-semibold tracking-[-0.03em] text-ink">How Sales & Outreach Tool Works</h3>
            </div>
            <Button variant="ghost" className="px-3 py-2 text-xs" onClick={() => setGuideOpen(false)}>
              Close
            </Button>
          </div>

          <div className="space-y-4 text-sm leading-7 text-slate-700">
            <p>
              Start with the clinic name and market so the tool can ground the research in a realistic operating context.
              It then scores fit, surfaces likely pain points, and drafts outreach that sounds more like a thoughtful rep than a template.
            </p>
            <p>
              The strongest results usually come from clinics where there is a clear workflow story to tell, such as front-desk
              strain, referral leakage, billing drag, inconsistent reminders, or growth pressure across multiple locations.
            </p>
            <p>
              Use Suggested Researches when you want faster targets, and use Research History when you need to revisit an older
              clinic without rerunning everything from scratch.
            </p>
            <p>
              The most persuasive outreach usually starts from the clinic’s likely operating pressure, such as front-desk load,
              referral leakage, billing drag, or reminder friction, instead of from a generic feature list.
            </p>
          </div>
        </div>
      </Dialog>

      <Dialog
        open={deleteConfirmOpen}
        onClose={() => {
          setDeleteConfirmOpen(false);
          setPendingDeleteResearch(null);
        }}
        className="max-w-lg"
      >
        <div className="space-y-5">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Delete Research</p>
            <h3 className="text-2xl font-semibold tracking-[-0.03em] text-ink">Remove this research brief permanently?</h3>
            <p className="text-sm leading-7 text-slate-700">
              {pendingDeleteResearch
                ? `This will permanently delete ${pendingDeleteResearch.clinic_name}${
                    pendingDeleteResearch.location ? ` in ${pendingDeleteResearch.location}` : ""
                  } from Sales & Outreach history.`
                : "This research run will be deleted permanently from Sales & Outreach history."}
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-end gap-2">
            <Button
              variant="ghost"
              onClick={() => {
                setDeleteConfirmOpen(false);
                setPendingDeleteResearch(null);
              }}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button variant="danger" onClick={deleteResearch} disabled={deleting}>
              {deleting ? "Deleting..." : "Delete Research"}
            </Button>
          </div>
        </div>
      </Dialog>
    </>
  );
}
