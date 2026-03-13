import { Button } from "@/components/ui/button";

interface Props {
  onApprove: () => Promise<void>;
  onReject: () => Promise<void>;
}

export function ApprovalActions({ onApprove, onReject }: Props) {
  return (
    <div className="flex gap-2">
      <Button variant="secondary" onClick={onReject}>Reject</Button>
      <Button onClick={onApprove}>Approve</Button>
    </div>
  );
}
