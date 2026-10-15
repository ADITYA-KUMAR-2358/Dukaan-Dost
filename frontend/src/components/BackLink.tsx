import { ArrowLeft } from "@phosphor-icons/react";
import { Link } from "react-router-dom";

export function BackLink({ to, children = "Back" }: { to: string; children?: string }) {
  return (
    <Link to={to} className="mb-3 inline-flex min-h-11 items-center gap-1.5 text-sm text-[var(--muted)] hover:text-[var(--ink)]">
      <ArrowLeft aria-hidden="true" size={16} />
      {children}
    </Link>
  );
}
