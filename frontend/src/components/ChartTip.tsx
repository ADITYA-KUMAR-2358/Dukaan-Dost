type TipProps = {
  active?: boolean;
  label?: string | number;
  payload?: { name?: string; value?: number | string; color?: string }[];
};

export function ChartTip({ active, label, payload }: TipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-[var(--r-input)] border border-[var(--line)] bg-[var(--paper)] px-3 py-2 text-sm text-[var(--ink)]">
      {label ? <p className="mb-1 font-medium">{label}</p> : null}
      <ul className="grid gap-1">
        {payload.map((item) => (
          <li key={item.name} className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full" style={{ background: item.color }} />
            <span>
              {item.name}: {item.value}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
