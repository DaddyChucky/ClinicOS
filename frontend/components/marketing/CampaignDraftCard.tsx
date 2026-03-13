import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CampaignDraft } from "@/lib/types";

interface Props {
  draft: CampaignDraft;
  onApprove?: (id: number) => Promise<void>;
  onReject?: (id: number) => Promise<void>;
}

export function CampaignDraftCard({ draft, onApprove, onReject }: Props) {
  const variant = draft.status === "approved" ? "success" : draft.status === "rejected" ? "danger" : "warning";

  return (
    <Card className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-ink">{draft.title}</h3>
        <Badge variant={variant}>{draft.status}</Badge>
      </div>
      <p className="text-sm"><span className="font-semibold text-ink">Audience:</span> {draft.audience}</p>
      <p className="text-sm"><span className="font-semibold text-ink">Channel:</span> {draft.channel}</p>
      <p className="whitespace-pre-wrap text-sm text-slate">{draft.brief}</p>
      <div className="text-sm">
        <p className="font-semibold text-ink">Nurture Sequence</p>
        {(draft.nurture_sequence_json ?? []).map((item, idx) => (
          <p key={idx} className="text-slate">- {(item.subject as string) ?? "Step"}</p>
        ))}
      </div>
      {onApprove && onReject ? (
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => onReject(draft.id)}>Reject</Button>
          <Button onClick={() => onApprove(draft.id)}>Approve</Button>
        </div>
      ) : null}
    </Card>
  );
}
