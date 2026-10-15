import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ChartKey } from "../../components/ChartKey";
import { ShopNameForm } from "../../components/ShopNameForm";
import { ChartTip } from "../../components/ChartTip";
import { api, type Dashboard } from "../../lib/api";
import { useStatus } from "../../lib/useStatus";

type Attention = {
  id: string;
  product_name: string;
  suggested_qty: number | null;
  slow_status: string;
};

export function FirstRun({ onReady }: { onReady: () => void }) {
  const navigate = useNavigate();
  const [message, setMessage] = useState<string | null>(null);
  const [shopName, setShopName] = useState("");
  const [busy, setBusy] = useState(false);
  const [guide, setGuide] = useState(false);
  const [readyOpen, setReadyOpen] = useState(false);
  const { status } = useStatus();

  async function openSample() {
    setBusy(true);
    try {
      await api("/api/workspaces/sample", { method: "POST" });
      onReady();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Could not open the sample shop.");
    } finally {
      setBusy(false);
    }
  }

  async function openLocal() {
    setBusy(true);
    try {
      await api("/api/workspaces/local", { method: "POST" });
      const trimmed = shopName.trim();
      if (trimmed) {
        await api("/api/workspaces/name", { method: "PATCH", body: JSON.stringify({ name: trimmed }) });
      }
      onReady();
      navigate("/app/import");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Could not create your shop.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mx-auto max-w-3xl">
      <h1 className="max-w-[16ch] text-4xl leading-[1.05] md:text-5xl">Start with a sample shop, or your own file.</h1>
      <p className="mt-3 max-w-xl text-[var(--muted)]">The sample kirana is fictional and stays separate from billing you import later.</p>
      <div className="mt-6 border-t border-[var(--line)]">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--line)] py-4">
          <div>
            <h2 className="text-xl">Explore sample shop</h2>
            <p className="text-sm text-[var(--muted)]">Fictional billing, kept in its own workspace.</p>
          </div>
          <button type="button" disabled={busy} className="btn" onClick={() => void openSample()}>Explore sample shop</button>
        </div>
        <div className="grid gap-3 border-b border-[var(--line)] py-4 sm:grid-cols-[1fr_auto] sm:items-end">
          <div>
            <h2 className="text-xl">Import billing CSV</h2>
            <p className="text-sm text-[var(--muted)]">Opens your shop, then the import screen.</p>
            <label className="mt-3 block max-w-sm text-sm">
              Shop name
              <input className="field" value={shopName} maxLength={80} placeholder="My shop" onChange={(event) => setShopName(event.target.value)} />
            </label>
          </div>
          <button type="button" disabled={busy} className="btn btn-quiet" onClick={() => void openLocal()}>Import billing CSV</button>
        </div>
        <div className="border-b border-[var(--line)] py-4">
          <button type="button" className="text-left text-xl" aria-expanded={guide} onClick={() => setGuide((value) => !value)}>
            View setup guide
          </button>
          {guide ? (
            <p className="mt-2 max-w-[52ch] text-sm text-[var(--muted)]">Run the API on port 8000 and this site on port 5173. A CSV template is on the import screen.</p>
          ) : null}
        </div>
        <div className="py-4">
          <button type="button" className="text-left text-xl" aria-expanded={readyOpen} onClick={() => setReadyOpen((value) => !value)}>
            Check local AI readiness
          </button>
          {readyOpen ? (
            <ul className="mt-3 grid gap-2 text-sm">
              <li>TabPFN: {status?.tabpfn.installed ? (status.tabpfn.package_version === "api" ? "API key is set" : `package ${status.tabpfn.package_version ?? "installed"}`) : "no API key, so forecasts use a named baseline."}</li>
              <li>Explanations: {status?.explanation_mode === "gemma" ? "Gemma is configured." : "Not running. The app still explains with a labelled template."}</li>
              <li>
                <Link className="underline" to="/limits">Read the limits</Link>
              </li>
            </ul>
          ) : null}
        </div>
      </div>
      {message ? <p className="mt-4 text-[var(--danger)]" role="alert">{message}</p> : null}
    </section>
  );
}

export function OverviewPage() {
  const { status, loading, error, reload } = useStatus();
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [attention, setAttention] = useState<Attention[]>([]);
  const [dashError, setDashError] = useState<string | null>(null);

  useEffect(() => {
    if (!status?.active_shop_id) return;
    void api<Dashboard>("/api/dashboard")
      .then((payload) => {
        setDash(payload);
        setDashError(null);
      })
      .catch((err: unknown) => {
        setDashError(err instanceof Error ? err.message : "Dashboard unavailable.");
      });
    void api<{ recommendations: Attention[] }>("/api/recommendations")
      .then((payload) => {
        setAttention(
          payload.recommendations
            .filter((row) => row.suggested_qty !== null && row.suggested_qty > 0)
            .slice(0, 4),
        );
      })
      .catch(() => setAttention([]));
  }, [status?.active_shop_id]);

  if (loading) {
    return (
      <div aria-busy="true" aria-label="Loading the shop" className="grid gap-3">
        <div className="h-10 w-56 rounded-[var(--r)] bg-[var(--sage)]" />
        <div className="h-28 rounded-[var(--r)] bg-[var(--sage)]" />
      </div>
    );
  }
  if (error) return <ErrorNote message={error} />;
  if (!status?.active_shop_id) return <FirstRun onReady={() => void reload()} />;

  const trend = dash?.demand_trend
    ? [
        { label: "Prior 7", sold: dash.demand_trend.prior_7_days },
        { label: "Last 7", sold: dash.demand_trend.recent_7_days },
      ]
    : [];

  return (
    <section>
      <h1 className="text-4xl leading-[1.05]">{dash?.shop.name ?? "Overview"}</h1>
      {dash && !dash.shop.is_demo ? (
        <ShopNameForm
          name={dash.shop.name}
          onSaved={(name) => {
            setDash({ ...dash, shop: { ...dash.shop, name } });
          }}
        />
      ) : null}
      {dashError ? <div className="mt-4"><ErrorNote message={dashError} /></div> : null}
      <h2 className="mt-8 text-2xl">Needs attention</h2>
      {attention.length === 0 ? (
        <p className="mt-3 max-w-[48ch] text-[var(--muted)]">No reorder yet. Generate a forecast after the shop has sales.</p>
      ) : (
        <ul className="mt-3 grid max-w-xl gap-3">
          {attention.map((row) => (
            <li key={row.id}>
              <Link to="/app/recommendations" className="parchi block">
                <span className="text-xl">{row.product_name}</span>
                <span className="nums mt-1 block">Order about {count(row.suggested_qty ?? 0)}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
      <h2 className="mt-10 text-2xl">Demand</h2>
      {dash?.demand_trend ? (
        <>
          <p className="mt-2 max-w-[52ch] text-sm">
            Sold {count(dash.demand_trend.recent_7_days)} in the last 7 days, and {count(dash.demand_trend.prior_7_days)} in the 7 days before.
          </p>
          <div className="mt-3 h-36 max-w-xl">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend}>
                <CartesianGrid stroke="var(--line)" vertical={false} />
                <XAxis dataKey="label" tick={{ fill: "var(--muted)", fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis width={36} tick={{ fill: "var(--muted)", fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTip />} />
                <Line dataKey="sold" name="Sold" stroke="var(--series-actual)" strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <ChartKey className="mt-2" items={[{ kind: "solid", label: "Sold" }]} />
        </>
      ) : (
        <p className="mt-2 text-sm text-[var(--muted)]">No sales yet.</p>
      )}
      <p className="mt-6 max-w-[52ch] text-sm">
        {dash?.inventory_value === null || dash?.inventory_value === undefined
          ? "Add cost prices to see stock value."
          : `Stock value at cost ${inr(dash.inventory_value)}.`}
      </p>
      <p className="mt-3 text-sm text-[var(--muted)]">
        Last import: {dash?.last_import ? `${dash.last_import.filename}, ${count(dash.last_import.accepted_rows)} rows, ${shownWhen(dash.last_import.created_at)}` : "none"}.
      </p>
      <p className="text-sm text-[var(--muted)]">Last forecast: {shownWhen(dash?.last_forecast?.completed_at)}.</p>
    </section>
  );
}

function shownWhen(value: string | null | undefined) {
  if (!value) return "none";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short", year: "numeric" }).format(date);
}

function count(value: number) {
  return new Intl.NumberFormat("en-IN").format(value);
}

function inr(value: number) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value);
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <p role="alert" className="rounded-[var(--r-input)] border border-[var(--danger)] px-3 py-2 text-sm text-[var(--danger)]">
      {message}
    </p>
  );
}
