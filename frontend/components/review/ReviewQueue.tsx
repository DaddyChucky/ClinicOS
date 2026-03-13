import { Card } from "@/components/ui/card";
import { ReviewQueueItem } from "@/lib/types";
import { formatDate } from "@/lib/utils";

interface Props {
  items: ReviewQueueItem[];
  onSelect: (item: ReviewQueueItem) => void;
}

export function ReviewQueue({ items, onSelect }: Props) {
  return (
    <Card className="space-y-3">
      <h3 className="text-lg font-semibold">Pending Review Queue</h3>
      {items.length === 0 ? <p className="text-sm text-slate">No pending items.</p> : null}
      {items.map((item) => (
        <button
          key={`${item.entity_type}-${item.draft_id}`}
          className="w-full rounded-md border border-gray-200 p-3 text-left hover:bg-gray-50"
          onClick={() => onSelect(item)}
        >
          <p className="text-sm font-medium">{item.title}</p>
          <p className="text-xs text-slate">{item.entity_type} • {item.status} • {formatDate(item.created_at)}</p>
        </button>
      ))}
    </Card>
  );
}
