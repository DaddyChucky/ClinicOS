import { Card } from "@/components/ui/card";

export function AdminPageSkeleton() {
  return (
    <div className="grid gap-4 xl:grid-cols-[1.25fr_1fr]">
      <Card className="space-y-4">
        <div className="shimmer-line h-3 w-32 rounded-full" />
        <div className="shimmer-line h-24 w-full rounded-[24px]" />
        <div className="shimmer-line h-24 w-full rounded-[24px]" />
      </Card>
      <div className="space-y-4">
        <Card className="space-y-3">
          <div className="shimmer-line h-3 w-28 rounded-full" />
          <div className="shimmer-line h-16 w-full rounded-[24px]" />
        </Card>
        <Card className="space-y-3">
          <div className="shimmer-line h-3 w-36 rounded-full" />
          <div className="shimmer-line h-32 w-full rounded-[24px]" />
        </Card>
      </div>
    </div>
  );
}
