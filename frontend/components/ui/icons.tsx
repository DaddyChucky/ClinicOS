import type { SVGProps } from "react";

export function ConsoleIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" {...props}>
      <rect x="3.5" y="4" width="13" height="12" rx="2.25" stroke="currentColor" strokeWidth="1.5" />
      <path d="M7 8.25H13" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
      <path d="M7 11.75H10.75" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
    </svg>
  );
}

export function DeskIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" {...props}>
      <path
        d="M4.25 5.25H15.75C16.164 5.25 16.5 5.586 16.5 6V12.25C16.5 12.664 16.164 13 15.75 13H4.25C3.836 13 3.5 12.664 3.5 12.25V6C3.5 5.586 3.836 5.25 4.25 5.25Z"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <path d="M7.25 15.25H12.75" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
      <path d="M10 13V15.25" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
      <path d="M6.75 8.5H13.25" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
    </svg>
  );
}

export function SalesIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" {...props}>
      <path
        d="M4.5 13.75L8.25 10L10.75 12.5L15.5 7.75"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
      />
      <path d="M12.75 7.75H15.5V10.5" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
    </svg>
  );
}

export function MarketingIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" {...props}>
      <path
        d="M5.25 12.75L12.75 5.25M12.75 5.25H15.25M12.75 5.25V7.75"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
      />
      <path d="M5 6.75H8" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
      <path d="M4.75 10H7.75" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
      <path d="M4.5 13.25H7.5" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
    </svg>
  );
}

export function TrashIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" {...props}>
      <path
        d="M4.75 6.25H15.25M8 9V13.5M12 9V13.5M6.5 6.25V4.75C6.5 4.336 6.836 4 7.25 4H12.75C13.164 4 13.5 4.336 13.5 4.75V6.25M6.875 16H13.125C13.539 16 13.875 15.664 13.875 15.25L14.35 6.25H5.65L6.125 15.25C6.125 15.664 6.461 16 6.875 16Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
      />
    </svg>
  );
}

export function MailIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" {...props}>
      <path
        d="M3.75 5.5H16.25C16.664 5.5 17 5.836 17 6.25V13.75C17 14.164 16.664 14.5 16.25 14.5H3.75C3.336 14.5 3 14.164 3 13.75V6.25C3 5.836 3.336 5.5 3.75 5.5Z"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <path
        d="M3.5 6L10 10.75L16.5 6"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
      />
    </svg>
  );
}

export function PrintIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" {...props}>
      <path
        d="M5.5 7V4.75C5.5 4.336 5.836 4 6.25 4H13.75C14.164 4 14.5 4.336 14.5 4.75V7M5.5 12.5H4.75C4.336 12.5 4 12.164 4 11.75V8.75C4 8.336 4.336 8 4.75 8H15.25C15.664 8 16 8.336 16 8.75V11.75C16 12.164 15.664 12.5 15.25 12.5H14.5M5.5 10.5H14.5V15.25C14.5 15.664 14.164 16 13.75 16H6.25C5.836 16 5.5 15.664 5.5 15.25V10.5Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
      />
      <path d="M13.25 9.75H13.26" stroke="currentColor" strokeLinecap="round" strokeWidth="2" />
    </svg>
  );
}

export function QueueIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" {...props}>
      <path
        d="M4.5 5.25H15.5C15.914 5.25 16.25 5.586 16.25 6V12C16.25 12.414 15.914 12.75 15.5 12.75H9.25L6 15.5V12.75H4.5C4.086 12.75 3.75 12.414 3.75 12V6C3.75 5.586 4.086 5.25 4.5 5.25Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
      />
      <path d="M7 8.5H13" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
      <path d="M7 10.5H11.25" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
    </svg>
  );
}

export function RefreshIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" {...props}>
      <path
        d="M15.25 7.5A5.75 5.75 0 1 0 16 10.25"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
      />
      <path d="M12.75 4.75H15.25V7.25" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
    </svg>
  );
}

export function SendIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" {...props}>
      <path
        d="M15.75 4.75L8.875 11.625"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
      />
      <path
        d="M15.75 4.75L11.375 15.25L8.875 11.625L4.75 9.5L15.75 4.75Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
      />
    </svg>
  );
}

export function PlusIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" {...props}>
      <path d="M10 5.25V14.75" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
      <path d="M5.25 10H14.75" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
    </svg>
  );
}

export function SaveIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" {...props}>
      <path
        d="M5 4.5H13.75L15.5 6.25V15.25C15.5 15.664 15.164 16 14.75 16H5.25C4.836 16 4.5 15.664 4.5 15.25V5.25C4.5 4.836 4.836 4.5 5.25 4.5H5Z"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="1.5"
      />
      <path d="M7 4.75V8H12.5V4.75" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.5" />
      <path d="M7.25 12.25H12.75" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
    </svg>
  );
}

export function SearchIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" {...props}>
      <circle cx="9" cy="9" r="4.75" stroke="currentColor" strokeWidth="1.5" />
      <path d="M12.5 12.5L15.75 15.75" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
    </svg>
  );
}

export function InfoIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" {...props}>
      <circle cx="10" cy="10" r="6.25" stroke="currentColor" strokeWidth="1.5" />
      <path d="M10 9V12.5" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
      <path d="M10 6.75H10.01" stroke="currentColor" strokeLinecap="round" strokeWidth="2" />
    </svg>
  );
}

export function ArchiveIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" {...props}>
      <rect x="4" y="5" width="12" height="3.25" rx="0.75" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M5.5 8.25H14.5V14.75C14.5 15.164 14.164 15.5 13.75 15.5H6.25C5.836 15.5 5.5 15.164 5.5 14.75V8.25Z"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <path d="M8 11H12" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
    </svg>
  );
}
