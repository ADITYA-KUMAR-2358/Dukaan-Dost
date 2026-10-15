import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { useStatus } from "../../lib/useStatus";
import { BackLink } from "../../components/BackLink";
import { ShopNameForm } from "../../components/ShopNameForm";
import { applyTheme, readTheme, type ThemeName } from "../../components/ThemeSwitch";
import { ErrorNote } from "../dashboard/OverviewPage";

type Settings = {
  language: string;
  service_level: number;
  coverage_days: number;
  horizon_days: number;
  prefer_tabpfn: boolean;
  ollama_model: string;
};

export function SettingsPage() {
  const { status, reload } = useStatus();
  const [settings, setSettings] = useState<Settings | null>(null);
  const [shops, setShops] = useState<{ id: string; name: string; is_demo: boolean }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [theme, setTheme] = useState<ThemeName>(() => readTheme());

  useEffect(() => {
    void api<{ shops: { id: string; name: string; is_demo: boolean }[]; active_shop_id: string | null }>("/api/workspaces")
      .then((payload) => setShops(payload.shops))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not load shops."));
    void api<{ settings: Settings | null }>("/api/settings")
      .then((payload) => setSettings(payload.settings))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not load settings."));
  }, [status?.active_shop_id]);

  useEffect(() => {
    const sync = () => setTheme(readTheme());
    window.addEventListener("dukaan-theme", sync);
    return () => window.removeEventListener("dukaan-theme", sync);
  }, []);

  async function save() {
    if (!settings) return;
    try {
      await api("/api/settings", { method: "PATCH", body: JSON.stringify(settings) });
      setMessage("Saved.");
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save settings.");
    }
  }

  async function activate(id: string) {
    await api("/api/settings", { method: "PATCH", body: JSON.stringify({ active_shop_id: id }) });
    await reload();
  }

  const active = shops.find((shop) => shop.id === status?.active_shop_id);

  return (
    <section className="max-w-xl">
      <BackLink to="/app">Overview</BackLink>
      <h1 className="text-4xl">Settings</h1>
      <h2 className="mt-6 font-semibold">Data location</h2>
      <p className="mt-2 text-sm">On this computer. This install is not a hosted demo.</p>
      <h2 className="mt-6 font-semibold">Local AI</h2>
      <ul className="mt-2 grid gap-1 text-sm">
        <li>Database: {status ? "SQLite on this computer" : "Not loaded"}</li>
        <li>TabPFN: {status?.tabpfn.installed ? (status.tabpfn.package_version === "api" ? "API key is set" : "package installed") : "no API key, so forecasts use a named baseline."}</li>
        <li>{status?.gemma.ready ? "Gemma is configured." : "No LLM API key. Explanations stay on the template."}</li>
      </ul>
      <h2 className="mt-6 font-semibold">Retention</h2>
      <p className="mt-2 text-sm text-[var(--muted)]">
        Sales stay in the local database file until that file is removed. This version has no delete control.
      </p>
      {error ? <div className="mt-4"><ErrorNote message={error} /></div> : null}
      <div className="mt-4 flex gap-2">
        <button type="button" aria-pressed={theme === "light"} className={`btn ${theme === "light" ? "" : "btn-quiet"}`} onClick={() => applyTheme("light")}>Light</button>
        <button type="button" aria-pressed={theme === "dark"} className={`btn ${theme === "dark" ? "" : "btn-quiet"}`} onClick={() => applyTheme("dark")}>Dark</button>
      </div>
      <h2 className="mt-6 font-semibold">Shops</h2>
      {active && !active.is_demo ? (
        <ShopNameForm
          name={active.name}
          onSaved={(name) => {
            setShops((current) => current.map((shop) => (shop.id === active.id ? { ...shop, name } : shop)));
            void reload();
          }}
        />
      ) : null}
      {active?.is_demo ? <p className="mt-2 text-sm text-[var(--muted)]">The sample shop keeps its name.</p> : null}
      <ul className="mt-2 grid gap-2">
        {shops.map((shop) => (
          <li key={shop.id}>
            <button type="button" className="btn btn-quiet" onClick={() => void activate(shop.id)}>
              {shop.name}
              {shop.is_demo && !shop.name.toLowerCase().includes("sample") ? " (sample)" : ""}
            </button>
          </li>
        ))}
      </ul>
      {settings ? (
        <div className="mt-4 grid gap-3">
          <label className="text-sm">
            Explanation language
            <select className="field" value={settings.language} onChange={(event) => setSettings({ ...settings, language: event.target.value })}>
              <option value="hinglish">Hinglish</option>
              <option value="english">English</option>
            </select>
          </label>
          <label className="text-sm">
            Service level
            <select className="field" value={settings.service_level} onChange={(event) => setSettings({ ...settings, service_level: Number(event.target.value) })}>
              <option value={0.9}>0.90</option>
              <option value={0.95}>0.95</option>
              <option value={0.99}>0.99</option>
            </select>
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={settings.prefer_tabpfn} onChange={(event) => setSettings({ ...settings, prefer_tabpfn: event.target.checked })} />
            Prefer TabPFN when it is actually available
          </label>
          <button type="button" className="btn w-fit" onClick={() => void save()}>
            Save settings
          </button>
          {message ? <p className="text-sm">{message}</p> : null}
        </div>
      ) : (
        <p className="mt-4 text-sm">Open a shop before changing forecast settings.</p>
      )}
    </section>
  );
}
