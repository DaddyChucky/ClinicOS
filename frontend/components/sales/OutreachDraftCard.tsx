import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { OutreachDraft } from "@/lib/types";

interface Props {
  draft: OutreachDraft;
  onApprove?: (id: number) => Promise<void>;
  onReject?: (id: number) => Promise<void>;
}

export function OutreachDraftCard({ draft, onApprove, onReject }: Props) {
  const variant = draft.status === "approved" ? "success" : draft.status === "rejected" ? "danger" : "warning";

  return (
    <Card className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-ink">Outreach Draft #{draft.id}</h3>
        <Badge variant={variant}>{draft.status}</Badge>
      </div>
      <p className="text-sm"><span className="font-semibold text-ink">Subject:</span> {draft.subject}</p>
      <p className="whitespace-pre-wrap text-sm text-slate">{draft.body}</p>
      <p className="text-xs text-slate">Personalization notes: {draft.personalization_notes ?? "N/A"}</p>
      {onApprove && onReject ? (
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => onReject(draft.id)}>Reject</Button>
          <Button onClick={() => onApprove(draft.id)}>Approve</Button>
        </div>
      ) : null}
    </Card>
  );
}
