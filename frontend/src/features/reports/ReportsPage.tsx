import { BackLink } from "../../components/BackLink";

const REPORTS: [string, string, string][] = [
  ["inventory", "Inventory CSV", "sku, name, stock, cost, and supplier for the open shop"],
  ["forecast", "Forecast CSV", "predicted and baseline quantities from the latest run"],
  ["recommendations", "Reorder CSV", "suggested order lines for the open shop"],
  ["quality", "Data-quality report", "import problems recorded for this shop"],
  ["imports", "Import history", "accepted, rejected, and duplicate counts by file"],
  ["evaluation", "Forecast evaluation", "how the latest run compared with later sales, when that comparison exists"],
];

export function ReportsPage() {
  return (
    <section className="max-w-3xl">
      <BackLink to="/app">Overview</BackLink>
      <h1 className="text-4xl">Reports</h1>
      <p className="mt-2 max-w-xl text-sm text-[var(--muted)]">
        Each download is named dukaandost-{"{shop}"}-{"{report}"}.csv and contains only the shop that is open now.
      </p>
      <ul className="khata khata-plain mt-6">
        {REPORTS.map(([kind, label, detail]) => (
          <li key={kind} className="flex flex-wrap items-center justify-between gap-3 py-4">
            <div>
              <p className="text-sm">{label}</p>
              <p className="mt-1 text-sm text-[var(--muted)]">{detail}</p>
            </div>
            <a className="btn btn-quiet" href={`/api/reports/export?kind=${kind}`}>
              Export
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}
