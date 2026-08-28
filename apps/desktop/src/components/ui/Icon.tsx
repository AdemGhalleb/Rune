export type IconName =
  | "arrowRight"
  | "book"
  | "bookmark"
  | "check"
  | "chevronDown"
  | "clock"
  | "command"
  | "cpu"
  | "database"
  | "fileText"
  | "folder"
  | "graph"
  | "home"
  | "lock"
  | "mail"
  | "message"
  | "moon"
  | "plus"
  | "search"
  | "settings"
  | "shield"
  | "sparkle"
  | "sun"
  | "target"
  | "tasks"
  | "trash"
  | "zap";

interface IconProps {
  name: IconName;
  size?: number;
  className?: string;
}

export function Icon({ name, size = 20, className }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      fill="none"
      height={size}
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.5"
      viewBox="0 0 24 24"
      width={size}
    >
      {renderIcon(name)}
    </svg>
  );
}

function renderIcon(name: IconName) {
  switch (name) {
    case "arrowRight":
      return <path d="M5 12h14m-6-6 6 6-6 6" />;
    case "book":
      return <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 4.5A2.5 2.5 0 0 1 6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15Z" />;
    case "bookmark":
      return <path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z" />;
    case "check":
      return <path d="m5 12 4 4L19 6" />;
    case "chevronDown":
      return <path d="m6 9 6 6 6-6" />;
    case "clock":
      return (
        <>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v5l3 2" />
        </>
      );
    case "command":
      return <path d="M9 6a3 3 0 1 0-3 3h12a3 3 0 1 0-3-3v12a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3V6Z" />;
    case "cpu":
      return (
        <>
          <rect height="12" rx="2" width="12" x="6" y="6" />
          <path d="M9 2v3m6-3v3M9 19v3m6-3v3M2 9h3m-3 6h3m14-6h3m-3 6h3M10 10h4v4h-4z" />
        </>
      );
    case "database":
      return (
        <>
          <ellipse cx="12" cy="5" rx="7" ry="3" />
          <path d="M5 5v14c0 1.7 3.1 3 7 3s7-1.3 7-3V5M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3" />
        </>
      );
    case "fileText":
      return <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Zm0 0v6h6M8 13h8M8 17h6" />;
    case "folder":
      return <path d="M3 6.5A2.5 2.5 0 0 1 5.5 4H10l2 2h6.5A2.5 2.5 0 0 1 21 8.5v8A2.5 2.5 0 0 1 18.5 19h-13A2.5 2.5 0 0 1 3 16.5z" />;
    case "graph":
      return (
        <>
          <circle cx="6" cy="16" r="3" />
          <circle cx="12" cy="6" r="3" />
          <circle cx="18" cy="16" r="3" />
          <path d="m7.5 13.5 3-5m3 0 3 5M9 16h6" />
        </>
      );
    case "home":
      return <path d="m3 11 9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z" />;
    case "lock":
      return (
        <>
          <rect height="11" rx="2" width="16" x="4" y="11" />
          <path d="M8 11V7a4 4 0 0 1 8 0v4" />
        </>
      );
    case "mail":
      return <path d="M4 6h16v12H4zM4 7l8 6 8-6" />;
    case "message":
      return <path d="M4 5h16v11H8l-4 4z" />;
    case "moon":
      return <path d="M20 14.5A8 8 0 0 1 9.5 4 8.5 8.5 0 1 0 20 14.5Z" />;
    case "plus":
      return <path d="M12 5v14M5 12h14" />;
    case "search":
      return (
        <>
          <circle cx="11" cy="11" r="7" />
          <path d="m16 16 4 4" />
        </>
      );
    case "settings":
      return (
        <>
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2 3.4-.2-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V22h-4v-.5a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.9.3l-.2.1-2-3.4.1-.1A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-1.5-1H3v-4h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.9L4.2 7l2-3.4.2.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.5V2h4v.5a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.2-.1 2 3.4-.1.1A1.7 1.7 0 0 0 19.4 9a1.7 1.7 0 0 0 1.5 1h.1v4h-.1a1.7 1.7 0 0 0-1.5 1Z" />
        </>
      );
    case "shield":
      return <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />;
    case "sparkle":
      return <path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8Zm6 12 .8 2.2L21 18l-2.2.8L18 21l-.8-2.2L15 18l2.2-.8Z" />;
    case "sun":
      return (
        <>
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
        </>
      );
    case "target":
      return (
        <>
          <circle cx="12" cy="12" r="9" />
          <circle cx="12" cy="12" r="5" />
          <circle cx="12" cy="12" r="1" />
        </>
      );
    case "tasks":
      return <path d="m4 7 2 2 4-4M13 7h7M4 17l2 2 4-4M13 17h7" />;
    case "trash":
      return (
        <path d="M3 6h18m-2 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
      );
    case "zap":
      return <path d="M13 2 4 14h7l-1 8 9-12h-7z" />;
  }
}
