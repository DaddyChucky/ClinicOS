import { Card } from "@/components/ui/card";

export function AdminStoryCard({
  eyebrow,
  title,
  story,
}: {
  eyebrow: string;
  title: string;
  story: string[];
}) {
  return (
    <Card className="space-y-3">
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">{eyebrow}</p>
        <h2 className="text-xl font-semibold tracking-[-0.02em] text-ink">{title}</h2>
      </div>
      <div className="space-y-2">
        {story.map((step, index) => (
          <div key={step} className="rounded-[22px] border border-slate-200/85 bg-slate-50/75 p-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">Step {index + 1}</p>
            <p className="mt-2 text-sm leading-6 text-slate-700">{step}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
