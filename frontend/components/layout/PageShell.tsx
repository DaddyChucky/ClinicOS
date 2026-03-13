import { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface PageShellProps {
  children: ReactNode;
  className?: string;
}

export function PageShell({ children, className }: PageShellProps) {
  return <div className={cn("mx-auto min-h-screen max-w-[1440px] px-5 py-8 lg:px-10 lg:py-10", className)}>{children}</div>;
}
