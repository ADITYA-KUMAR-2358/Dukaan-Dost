import { useEffect, useState } from "react";
import { BackLink } from "../../components/BackLink";
import { ProvenanceTag, explanationProvenance, forecastProvenance } from "../../components/ProvenanceTag";
import { api } from "../../lib/api";
import { ErrorNote } from "../dashboard/OverviewPage";

function shown(value: number | null) {
  return value === null ? "not calculated" : new Intl.NumberFormat("en-IN").format(value);
}

function SlowTag({ status }: { status: string }) {
  if (status === "no_recent_sales") return <span className="stock-tag stock-tag-still">No recent sales</span>;
  if (status === "insufficient_history") return <span className="stock-tag stock-tag-still">Not enough history</span>;
  if (status === "stockout_confounds_demand") return <span className="stock-tag stock-tag-check">Was out of stock</span>;
  if (status === "out_of_stock") return <span className="stock-tag stock-tag-check">Out of stock</span>;
  if (status === "declining") return <span className="stock-tag stock-tag-still">Low demand</span>;
  return null;
}

function because(policy: string) {
  if (policy === "lead_time_unknown") return "Lead time is not set, so this is not a full reorder point.";
  if (policy === "lead_time_demand_plus_z_sigma") return "Lead-time demand plus safety stock from past variation.";
  return policy.replaceAll("_", " ");
}

type Row = {
  id: string;
  product_name: string;
  sku: string | null;
  suggested_qty: number | null;
  calculated_qty: number | null;
  reorder_point: number | null;
  policy: string;
  slow_status: string;
  model_id: string | null;
  fallback_reason: string | null;
  user_note: string | null;
  flags: { code: string; reason: string }[];
  explanation: { source: string; summary: string; assumptions: string[]; verify: string[] };
};

export function RecommendationsPage() {
  const [rows, setRows] = useState<Row[]>([]);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [edit, setEdit] = useState<Record<string, string>>({});
  const [notes, setNotes] = useState<Record<string, string>>({});

  async function load(slow = filter) {
    try {
      const params = slow ? `?slow=${slow}` : "";
      const payload = await api<{ recommendations: Row[] }>(`/api/recommendations${params}`);
      setRows(payload.recommendations);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Recommendations are not available.");
    }
  }

  useEffect(() => {
    void load("");
    // Filters call load themselves.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function save(row: Row) {
    const raw = edit[row.id];
    const quantity = raw === undefined || raw === "" ? undefined : Number(raw);
    if (quantity !== undefined && (Number.isNaN(quantity) || quantity < 0)) {
      setError("Order quantity can't be negative.");
      return;
    }
    try {
      await api(`/api/recommendations/${row.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          ...(quantity === undefined ? {} : { user_qty: quantity }),
          user_note: notes[row.id] ?? row.user_note ?? "",
        }),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the edit.");
    }
  }

  async function explain(id: string) {
    try {
      const payload = await api<Row["explanation"]>(`/api/recommendations/${id}/explain`, { method: "POST" });
      setRows((current) => current.map((row) => (row.id === id ? { ...row, explanation: payload } : row)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Explanation failed.");
    }
  }

  return (
    <section>
      <BackLink to="/app">Overview</BackLink>
      <h1 className="text-4xl">Recommendations</h1>
      <label className="mt-4 block text-sm">
        Movement
        <select
          className="field"
          value={filter}
          onChange={(event) => {
            setFilter(event.target.value);
            void load(event.target.value);
          }}
        >
          <option value="">All</option>
          <option value="declining">Low demand</option>
          <option value="no_recent_sales">No recent sales</option>
          <option value="insufficient_history">Not enough history</option>
          <option value="stockout_confounds_demand">Was out of stock</option>
          <option value="out_of_stock">Out of stock</option>
        </select>
      </label>
      {error ? <div className="mt-4"><ErrorNote message={error} /></div> : null}
      {rows.length === 0 ? <p className="mt-6">Generate a forecast first. Recommendations are calculated from that run.</p> : null}
      <div className="mt-4 grid gap-4">
        {rows.map((row) => (
          <article key={row.id} className="parchi">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-2xl">{row.product_name}</h2>
              <SlowTag status={row.slow_status} />
            </div>
            <p className="mt-1 text-sm text-[var(--muted)]">{row.sku ?? "No SKU"}</p>
            <p className="nums mt-3 text-lg">Order about {shown(row.suggested_qty)}</p>
            <p className="mt-3 text-sm"><span className="font-medium">Because: </span>{because(row.policy)}</p>
            <div className="mt-2"><ProvenanceTag {...forecastProvenance(row.model_id, row.fallback_reason)} /></div>
            {row.explanation.assumptions.length ? (
              <p className="mt-3 text-sm"><span className="font-medium">Assumed: </span>{row.explanation.assumptions.join(" ")}</p>
            ) : null}
            {row.explanation.verify.length ? (
              <p className="mt-2 text-sm"><span className="font-medium">Check: </span>{row.explanation.verify.join(" ")}</p>
            ) : null}
            <p className="parchi-tear mt-3 pt-3 text-sm">{row.explanation.summary}</p>
            <div className="mt-2"><ProvenanceTag {...explanationProvenance(row.explanation.source)} /></div>
            <label className="mt-3 block text-sm">
              Note
              <textarea
                className="field hand"
                value={notes[row.id] ?? row.user_note ?? ""}
                onChange={(event) => setNotes({ ...notes, [row.id]: event.target.value })}
              />
            </label>
            <div className="mt-3 flex flex-wrap items-end gap-2">
              <label className="text-sm">
                Edit quantity
                <input
                  className="field w-28"
                  value={edit[row.id] ?? ""}
                  onChange={(event) => setEdit({ ...edit, [row.id]: event.target.value })}
                />
              </label>
              <button type="button" className="btn btn-quiet" onClick={() => void save(row)}>
                Save edit
              </button>
              <button type="button" className="btn btn-quiet" onClick={() => void explain(row.id)}>
                Ask local AI
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
