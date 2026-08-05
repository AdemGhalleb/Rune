import type { ReactNode } from "react";

type BadgeTone = "neutral" | "blue" | "amber" | "green" | "violet" | "rose" | "success" | "warning" | "error" | "info";

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: BadgeTone }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}
