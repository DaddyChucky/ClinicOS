import { useEffect, type MouseEvent, type PropsWithChildren } from "react";

import { cn } from "@/lib/utils";

interface DialogProps {
  open: boolean;
  className?: string;
  onClose?: () => void;
}

export function Dialog({ open, children, className, onClose }: PropsWithChildren<DialogProps>) {
  useEffect(() => {
    if (!open || !onClose) return undefined;
    const handleClose = onClose;

    function handleKeydown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        handleClose();
      }
    }

    window.addEventListener("keydown", handleKeydown);
    return () => window.removeEventListener("keydown", handleKeydown);
  }, [onClose, open]);

  function handleBackdropClick(event: MouseEvent<HTMLDivElement>) {
    if (event.target === event.currentTarget) {
      onClose?.();
    }
  }

  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-sm"
      onClick={handleBackdropClick}
    >
      <div
        className={cn(
          "w-full max-w-xl rounded-[30px] border border-white/80 bg-white p-6 shadow-[0_40px_100px_rgba(15,23,42,0.2)]",
          className
        )}
        onClick={(event) => event.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );
}
