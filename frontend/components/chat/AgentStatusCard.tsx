import { Card } from "@/components/ui/card";

interface Props {
  activeWorkflow: string;
  activeAgent: string;
  loopCount: number;
  unresolvedTurnCount: number;
  escalationRecommended: boolean;
  draftStatus: string;
}

export function AgentStatusCard({
  activeWorkflow,
  activeAgent,
  loopCount,
  unresolvedTurnCount,
  escalationRecommended,
  draftStatus
}: Props) {
  return (
    <Card className="space-y-3">
      <h3 className="text-sm font-semibold text-ink">Live Workflow State</h3>
      <div className="space-y-2 text-sm">
        <p><span className="font-medium">Active Workflow:</span> {activeWorkflow}</p>
        <p><span className="font-medium">Active Agent:</span> {activeAgent}</p>
        <p><span className="font-medium">Loop Count:</span> {loopCount}</p>
        <p><span className="font-medium">Unresolved Turns:</span> {unresolvedTurnCount}</p>
        <p><span className="font-medium">Escalation:</span> {escalationRecommended ? "Recommended" : "No"}</p>
        <p><span className="font-medium">Draft Status:</span> {draftStatus}</p>
      </div>
    </Card>
  );
}
