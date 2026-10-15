export function DataLocationChip() {
  return (
    <span className="prov-tag" title="This install keeps the shop database on this computer.">
      On this computer
    </span>
  );
}

export function SampleBanner({ onUseMine }: { onUseMine: () => void }) {
  return (
    <div className="border-t border-[var(--line)] bg-[var(--sage)] text-[var(--on-sage)]">
      <div className="slats h-1.5" aria-hidden="true" />
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-2">
        <p className="text-sm">Sample shop. Fictional data.</p>
        <button type="button" className="btn" onClick={onUseMine}>
          Use my shop
        </button>
      </div>
    </div>
  );
}
