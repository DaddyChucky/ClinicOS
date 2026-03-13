interface HelpTipProps {
  text: string;
}

export function HelpTip({ text }: HelpTipProps) {
  return (
    <span className="group relative inline-flex align-middle">
      <span
        className="inline-flex h-4 w-4 items-center justify-center rounded-full border border-slate-300 bg-white text-[10px] font-bold text-slate-600"
        aria-label={text}
      >
        ?
      </span>
      <span className="pointer-events-none absolute left-1/2 top-[130%] z-20 hidden w-56 -translate-x-1/2 rounded-lg border border-slate-200 bg-white p-2 text-[11px] text-slate-600 shadow-panel group-hover:block">
        {text}
      </span>
    </span>
  );
}

