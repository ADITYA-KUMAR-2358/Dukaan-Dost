import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { BackLink } from "../../components/BackLink";
import { ChartKey } from "../../components/ChartKey";
import { ChartTip } from "../../components/ChartTip";
import { ProvenanceTag, forecastProvenance } from "../../components/ProvenanceTag";
import { api } from "../../lib/api";
import { ErrorNote } from "../dashboard/OverviewPage";

type ForecastDetail = {
  id: string;
  status: string;
  error_code: string | null;
  summary: {
    products: {
      product_id: string;
      name: string;
      status: string;
      model_id: string | null;
      baseline_id: string | null;
      fallback_reason: string | null;
      limitations: string[];
      history: { date: string; quantity: number | null; stockout: boolean }[];
      evaluation: { primary?: { mae: number | null }; baseline?: { mae: number | null }; note?: string } | null;
    }[];
  };
  series: Record<string, { date: string; predicted_qty: number; baseline_qty: number; model_id: string }[]>;
};

function shownNumber(value: number | null | undefined) {
  return value === null || value === undefined ? "not available" : String(value);
}

function noteText(note: string) {
  if (note === "primary_model_is_the_baseline") return "The checked model is the baseline.";
  return note.replaceAll("_", " ");
}

function fallbackText(reason: string) {
  if (reason === "fewer_than_7_observed_days") return "Fewer than 7 observed days, so a baseline was used.";
  if (reason === "tabpfn_requirements_not_met") return "TabPFN did not have enough history, so a baseline was used.";
  if (reason.startsWith("tabpfn_failed")) return "TabPFN could not run, so a baseline was used.";
  return reason.replaceAll("_", " ");
}

export function ForecastPage() {
  const [horizon, setHorizon] = useState(14);
  const [detail, setDetail] = useState<ForecastDetail | null>(null);
  const [productId, setProductId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [asTable, setAsTable] = useState(false);

  async function refreshList() {
    const list = await api<{ forecasts: { id: string; status: string }[] }>("/api/forecasts");
    const latest = list.forecasts[0];
    if (!latest) return;
    if (latest.status === "queued" || latest.status === "running") {
      window.setTimeout(() => void refreshList(), 1000);
      return;
    }
    const full = await api<ForecastDetail>(`/api/forecasts/${latest.id}`);
    setDetail(full);
    setProductId((current) => current ?? full.summary.products[0]?.product_id ?? null);
  }

  useEffect(() => {
    void refreshList().catch((err: unknown) => setError(err instanceof Error ? err.message : "No forecast yet."));
    // The list is loaded once when the page opens.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      const created = await api<{ id: string; status: string }>("/api/forecasts", {
        method: "POST",
        body: JSON.stringify({ horizon_days: horizon }),
      });
      if (created.status === "completed") {
        setDetail(await api<ForecastDetail>(`/api/forecasts/${created.id}`));
      } else {
        await refreshList();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Forecast failed.");
    } finally {
      setBusy(false);
    }
  }

  const product = detail?.summary.products.find((item) => item.product_id === productId);
  const future = productId ? detail?.series[productId] ?? [] : [];
  const chart = [
    ...(product?.history ?? []).slice(-30).map((point) => ({
      date: point.date.slice(5),
      actual: point.stockout ? null : point.quantity,
      forecast: null as number | null,
      baseline: null as number | null,
    })),
    ...future.map((point) => ({
      date: point.date.slice(5),
      actual: null as number | null,
      forecast: point.predicted_qty,
      baseline: point.baseline_qty,
    })),
  ];

  return (
    <section>
      <BackLink to="/app">Overview</BackLink>
      <h1 className="text-4xl">Forecasts</h1>
      <div className="mt-4 flex flex-wrap items-end gap-3">
        <label className="text-sm">
          Horizon
          <select className="field" value={horizon} onChange={(event) => setHorizon(Number(event.target.value))}>
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
          </select>
        </label>
        <button type="button" disabled={busy} className="btn" onClick={() => void run()}>
          {busy ? "Working..." : "Generate forecast"}
        </button>
      </div>
      {error ? <div className="mt-4"><ErrorNote message={error} /></div> : null}
      {!detail ? <p className="mt-6">No forecast yet. Generate one after the shop has sales.</p> : null}
      {detail?.status === "failed" ? <ErrorNote message={`Forecast failed (${detail.error_code ?? "unknown"}).`} /> : null}
      {detail && detail.summary.products.length ? (
        <div className="mt-6 grid gap-4 lg:grid-cols-[220px_1fr]">
          <div className="grid gap-2">
            {detail.summary.products.map((item) => (
              <button key={item.product_id} type="button" className={`min-h-12 rounded-[var(--r-input)] px-3 py-2 text-left text-sm ${item.product_id === productId ? "bg-[var(--sage)]" : "border border-[var(--line)]"}`} onClick={() => setProductId(item.product_id)}>
                {item.name}
              </button>
            ))}
          </div>
          {product ? (
            <article>
              <div className="flex flex-wrap items-center gap-2">
                <ProvenanceTag {...forecastProvenance(product.model_id, product.fallback_reason)} />
              </div>
              <p className="mt-2 text-sm">
                {product.model_id ? `Baseline compared: ${product.baseline_id ?? "none"}.` : "Not enough history for a forecast."}
                {product.fallback_reason ? ` ${fallbackText(product.fallback_reason)}` : ""}
              </p>
              {product.evaluation?.primary ? (
                <p className="mt-2 text-sm">
                  Last 7-day check, MAE {shownNumber(product.evaluation.primary.mae)} versus baseline MAE {shownNumber(product.evaluation.baseline?.mae)}.
                  {product.evaluation.note ? ` ${noteText(product.evaluation.note)}` : ""}
                </p>
              ) : (
                <p className="mt-2 text-sm">Not enough history for a backtest on this product.</p>
              )}
              <ChartKey
                className="mt-3 text-sm"
                items={[
                  { kind: "solid", label: "Sold" },
                  { kind: "dashed", label: "Forecast" },
                  { kind: "dotted", label: "Baseline" },
                ]}
              />
              {asTable ? (
                <table className="mt-3 w-full text-sm">
                  <caption className="sr-only">Forecast table</caption>
                  <thead>
                    <tr className="text-left text-[var(--muted)]">
                      <th className="py-1 font-medium">Date</th>
                      <th className="py-1 text-right font-medium">Sold</th>
                      <th className="py-1 text-right font-medium">Forecast</th>
                      <th className="py-1 text-right font-medium">Baseline</th>
                    </tr>
                  </thead>
                  <tbody>
                    {chart.map((point) => (
                      <tr key={point.date}>
                        <th className="py-1 text-left font-medium" scope="row">{point.date}</th>
                        <td className="nums py-1 text-right">{point.actual ?? ""}</td>
                        <td className="nums py-1 text-right">{point.forecast ?? ""}</td>
                        <td className="nums py-1 text-right">{point.baseline ?? ""}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="mt-3 h-64" key={`${product.product_id}-${future.length}`}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chart}>
                      <CartesianGrid stroke="var(--line)" vertical={false} />
                      <XAxis dataKey="date" tick={{ fill: "var(--muted)", fontSize: 12 }} axisLine={{ stroke: "var(--line)" }} tickLine={false} />
                      <YAxis width={32} tick={{ fill: "var(--muted)", fontSize: 12 }} axisLine={false} tickLine={false} />
                      <Tooltip content={<ChartTip />} />
                      <Line dataKey="actual" name="Sold" stroke="var(--series-actual)" strokeWidth={2} dot={false} isAnimationActive={false} />
                      <Line dataKey="forecast" name="Forecast" stroke="var(--series-forecast)" strokeWidth={2} strokeDasharray="6 4" dot={false} isAnimationActive={false} />
                      <Line dataKey="baseline" name="Baseline" stroke="var(--series-baseline)" strokeWidth={2} strokeDasharray="1 4" dot={false} isAnimationActive={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
              <button type="button" className="btn btn-quiet mt-3" onClick={() => setAsTable((value) => !value)}>
                {asTable ? "View as chart" : "View as table"}
              </button>
              <h3 className="mt-6 text-xl">Limits</h3>
              <ul className="mt-2 text-sm text-[var(--muted)]">
                {product.limitations.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              {product.status !== "ok" ? <p className="mt-3">This product does not have a usable forecast yet.</p> : null}
            </article>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
