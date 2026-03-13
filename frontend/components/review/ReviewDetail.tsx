import { Card } from "@/components/ui/card";
import { ReviewQueueItem } from "@/lib/types";

export function ReviewDetail({ item }: { item: ReviewQueueItem | null }) {
  if (!item) {
    return (
      <Card>
        <p className="text-sm text-slate">Select a queue item to review.</p>
      </Card>
    );
  }

  return (
    <Card className="space-y-2">
      <h3 className="text-lg font-semibold">Review Detail</h3>
      <p className="text-sm"><span className="font-medium">Type:</span> {item.entity_type}</p>
      <p className="text-sm"><span className="font-medium">Draft ID:</span> {item.draft_id}</p>
      <p className="text-sm"><span className="font-medium">Title:</span> {item.title}</p>
      <p className="text-sm"><span className="font-medium">Status:</span> {item.status}</p>
      <p className="text-sm"><span className="font-medium">Conversation:</span> {item.conversation_id ?? "N/A"}</p>
    </Card>
  );
}
