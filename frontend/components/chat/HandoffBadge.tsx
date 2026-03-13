import { Badge } from "@/components/ui/badge";

interface Props {
  from: string;
  to: string;
  reason: string;
}

export function HandoffBadge({ from, to, reason }: Props) {
  return (
    <div className="space-y-2 rounded-xl border border-teal-100 bg-teal-50/60 p-3">
      <Badge variant="info">Handoff {from} to {to}</Badge>
      <p className="text-xs text-slate">{reason}</p>
    </div>
  );
}
