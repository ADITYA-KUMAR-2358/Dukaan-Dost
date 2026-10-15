import { ChartLine, DotsThree, FileCsv, Gear, ListChecks, Package, Storefront, UploadSimple, type Icon } from "@phosphor-icons/react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { BrandMark } from "../components/BrandMark";
import { DataLocationChip, SampleBanner } from "../components/SampleBanner";
import { SiteFooter } from "../components/SiteFooter";
import { ThemeSwitch } from "../components/ThemeSwitch";
import { api } from "../lib/api";
import { useStatus } from "../lib/useStatus";

const LINKS: [string, string, Icon][] = [
  ["Overview", "/app", Storefront],
  ["Import Sales", "/app/import", UploadSimple],
  ["Inventory", "/app/inventory", Package],
  ["Forecasts", "/app/forecasts", ChartLine],
  ["Recommendations", "/app/recommendations", ListChecks],
  ["Reports", "/app/reports", FileCsv],
  ["Settings", "/app/settings", Gear],
];

const TABS: [string, string, Icon][] = [
  ["Overview", "/app", Storefront],
  ["Inventory", "/app/inventory", Package],
  ["Forecasts", "/app/forecasts", ChartLine],
  ["Recommendations", "/app/recommendations", ListChecks],
];

const MORE: [string, string][] = [
  ["Import Sales", "/app/import"],
  ["Reports", "/app/reports"],
  ["Settings", "/app/settings"],
];

function itemClass(active: boolean) {
  return `flex min-h-12 items-center gap-2 border-l-2 px-3 text-sm ${active ? "border-[var(--saffron)] font-medium text-[var(--ink)]" : "border-transparent text-[var(--muted)]"}`;
}

export function AppLayout() {
  const navigate = useNavigate();
  const { status, reload } = useStatus();
  const [more, setMore] = useState(false);
  const [switchError, setSwitchError] = useState<string | null>(null);
  const demo = Boolean(status?.shop?.is_demo);
  const shopName = status?.shop?.name ?? null;

  useEffect(() => {
    const sync = () => {
      void reload();
    };
    window.addEventListener("dukaan-shop", sync);
    return () => window.removeEventListener("dukaan-shop", sync);
  }, [reload]);

  async function openMyShop() {
    setSwitchError(null);
    try {
      await api("/api/workspaces/local", { method: "POST" });
      await reload();
      navigate("/app/import");
    } catch (err) {
      setSwitchError(err instanceof Error ? err.message : "Could not open your shop.");
    }
  }

  return (
    <div className="flex min-h-[100dvh] flex-col pb-24 md:pb-0">
      <header className="sticky top-[var(--wake-h,0px)] z-10 border-b border-[var(--line)] bg-[var(--bg)]">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-4">
          <div className="flex min-w-0 items-center gap-3">
            <BrandMark className="shrink-0 text-xl sm:text-2xl" />
            {shopName ? <p className="truncate text-sm text-[var(--muted)]">{shopName}</p> : null}
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden sm:inline-flex">
              <DataLocationChip />
            </span>
            <ThemeSwitch />
          </div>
        </div>
        {demo ? (
          <>
            <SampleBanner onUseMine={() => void openMyShop()} />
            {switchError ? <p className="bg-[var(--sage)] px-4 pb-2 text-sm text-[var(--danger)]">{switchError}</p> : null}
          </>
        ) : null}
      </header>
      <div className="md:grid md:flex-1 md:grid-cols-[220px_1fr] md:content-start">
        <aside className="hidden border-[var(--line)] bg-[var(--paper)] md:block md:border-r">
          <nav aria-label="Shop" className="grid gap-1 px-3 py-4">
            {LINKS.map(([label, href, Icon]) => (
              <NavLink key={href} to={href} end={href === "/app"} className={({ isActive }) => itemClass(isActive)}>
                <Icon size={18} weight="regular" aria-hidden="true" />
                {label}
              </NavLink>
            ))}
          </nav>
        </aside>
        <div className="mx-auto w-full max-w-6xl px-4 py-5 md:px-8">
          <Outlet />
        </div>
      </div>
      <SiteFooter />
      <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-[var(--line)] bg-[var(--paper)] pb-[env(safe-area-inset-bottom)] md:hidden" aria-label="Shop">
        <ul className="grid grid-cols-5">
          {TABS.map(([label, href, Icon]) => (
            <li key={href}>
              <NavLink
                to={href}
                end={href === "/app"}
                className={({ isActive }) => `flex min-h-14 flex-col items-center justify-center gap-0.5 px-1 text-center text-[10px] leading-tight sm:text-[11px] ${isActive ? "text-[var(--ink)]" : "text-[var(--muted)]"}`}
                onClick={() => setMore(false)}
              >
                <Icon size={18} weight="regular" aria-hidden="true" />
                {label}
              </NavLink>
            </li>
          ))}
          <li>
            <button type="button" className="flex min-h-14 w-full flex-col items-center justify-center gap-0.5 px-1 text-center text-[10px] leading-tight text-[var(--muted)] sm:text-[11px]" aria-expanded={more} onClick={() => setMore((value) => !value)}>
              <DotsThree size={18} weight="regular" aria-hidden="true" />
              More
            </button>
          </li>
        </ul>
      </nav>
      {more ? (
        <div className="fixed inset-x-3 bottom-20 z-20 rounded-[var(--r)] border border-[var(--line)] bg-[var(--paper)] p-2 md:hidden">
          {MORE.map(([label, href]) => (
            <NavLink key={href} to={href} className="flex min-h-12 items-center px-3 text-sm" onClick={() => setMore(false)}>
              {label}
            </NavLink>
          ))}
        </div>
      ) : null}
    </div>
  );
}
