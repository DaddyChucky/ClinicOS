import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Prospect } from "@/lib/types";

export function ProspectCard({ prospect, summary, fitReasons }: { prospect: Prospect; summary: string; fitReasons: string[] }) {
  const fitScore = prospect.fit_score ?? 0;
  const fitVariant = fitScore >= 75 ? "success" : fitScore >= 55 ? "warning" : "danger";

  return (
    <Card className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-lg font-semibold text-ink">{prospect.clinic_name}</h3>
          <p className="text-sm text-slate">{summary}</p>
        </div>
        <Badge variant={fitVariant}>Fit Score {fitScore || "N/A"}</Badge>
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        <p className="text-sm">
          <span className="font-semibold text-ink">Type:</span> {prospect.clinic_type}
        </p>
        <p className="text-sm">
          <span className="font-semibold text-ink">Specialty:</span> {prospect.specialty ?? "N/A"}
        </p>
        <p className="text-sm">
          <span className="font-semibold text-ink">Size:</span> {prospect.size_estimate ?? "N/A"}
        </p>
        <p className="text-sm">
          <span className="font-semibold text-ink">Motion:</span> {prospect.existing_lead ? "Existing Account Expansion" : "Net-New Prospect"}
        </p>
      </div>

      <div className="space-y-1 text-sm">
        <p className="font-semibold text-ink">Fit Reasons</p>
        {fitReasons.map((reason) => (
          <p key={reason} className="text-slate">
            - {reason}
          </p>
        ))}
      </div>
    </Card>
  );
}
