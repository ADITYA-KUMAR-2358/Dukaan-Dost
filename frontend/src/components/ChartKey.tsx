type KeyKind = "solid" | "dashed" | "dotted" | "dot" | "tick";

function Swatch({ kind }: { kind: KeyKind }) {
  if (kind === "dot") return <span className="size-2 rounded-full bg-[var(--saffron)]" aria-hidden="true" />;
  if (kind === "tick") return <span className="h-3 w-0.5 bg-[var(--saffron)]" aria-hidden="true" />;
  const border =
    kind === "dashed" ? "border-dashed" : kind === "dotted" ? "border-dotted" : "border-solid";
  const color = kind === "dotted" ? "border-[var(--series-baseline)]" : "border-[var(--ink)]";
  return <span className={`w-6 border-t-2 ${border} ${color}`} aria-hidden="true" />;
}

export function ChartKey({ items, className = "" }: { items: { kind: KeyKind; label: string }[]; className?: string }) {
  return (
    <ul className={`flex flex-wrap gap-x-4 gap-y-2 text-xs text-[var(--muted)] ${className}`} aria-label="Chart legend">
      {items.map((item) => (
        <li key={item.label} className="inline-flex items-center gap-2">
          <Swatch kind={item.kind} />
          {item.label}
        </li>
      ))}
    </ul>
  );
}
