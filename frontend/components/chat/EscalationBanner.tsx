import { Button } from "@/components/ui/button";

interface Props {
  visible: boolean;
  summary?: string | null;
  onTalkToHuman: () => void;
}

export function EscalationBanner({ visible, summary, onTalkToHuman }: Props) {
  if (!visible) return null;

  return (
    <div className="rounded-lg border border-amber-300 bg-amber-50 p-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-warn">Escalation Recommended</p>
          <p className="text-xs text-slate">{summary ?? "A human specialist can take over this issue now."}</p>
        </div>
        <Button variant="secondary" onClick={onTalkToHuman}>
          Talk to Human
        </Button>
      </div>
    </div>
  );
}
