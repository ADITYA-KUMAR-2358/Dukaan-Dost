import { CalendarBlank, Export, List, ListChecks, Package, WarningCircle, type Icon } from "@phosphor-icons/react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { BrandMark } from "../components/BrandMark";
import { ChartKey } from "../components/ChartKey";
import { SiteFooter } from "../components/SiteFooter";
import { applyTheme, readTheme, type ThemeName } from "../components/ThemeSwitch";
import { DEMO_PRODUCTS, demoAdvice } from "../lib/demo";

const HORIZONS = [7, 14, 30] as const;

const PRODUCT_COPY: Record<string, { title: string; detail: string }> = {
  diya: { title: "Clay diya set, 12 pieces", detail: "Festive. Peaks before Diwali." },
  notebook: { title: "Classmate notebook", detail: "School term. Peaks at reopening." },
  ors: { title: "ORS sachet, orange", detail: "Medical. Peaks in summer heat." },
  parle: { title: "Parle-G, 250 g", detail: "Steady. Small weekly swing." },
};

const STEPS = [
  ["Export", "Save a sales report from the billing software you already use. Most export CSV."],
  ["Import", "Drop the file into DukaanDost. It checks the columns with you and shows any rows it could not read."],
  ["Forecast", "A forecast runs on this computer for each product, with the holidays and school dates you set."],
  ["Read the parchi", "Each suggestion says how much, by when, why, and what it assumed. You decide."],
] as const;

const COUNTER: { n: string; title: string; copy: string; where: string; Icon: Icon }[] = [
  { n: "01", title: "Reasons on every suggestion", copy: "Because, Assumed and Check are written on each parchi, so you can argue with it before you spend.", where: "Recommendations", Icon: ListChecks },
  { n: "02", title: "Rounds to how you actually buy", copy: "If the supplier sells in packs of 6, it says order 36, and shows that 31 was rounded up.", where: "Parchi", Icon: Package },
  { n: "03", title: "Knows your festivals and school dates", copy: "Add Diwali, Eid, Pongal or the local school calendar. Saffron ticks mark them on every chart.", where: "Forecasts", Icon: CalendarBlank },
  { n: "04", title: "Says when it does not know", copy: "Products with too little history get a Not enough history tag instead of a confident guess.", where: "Inventory", Icon: WarningCircle },
  { n: "05", title: "Exports a plain CSV for your supplier", copy: "Filter to Running low, export 42 rows, send it on WhatsApp or print it.", where: "Reports", Icon: Export },
];

const PARCHIS = [
  {
    id: "03",
    flag: "May run out before delivery",
    name: "Toor dal, 1 kg",
    shop: "Lakshmi Kirana, Indore. Sacks of 25 kg.",
    qty: "50",
    unit: "kg",
    need: "Need about 41 kg. Rounded up to 2 sacks.",
    when: "Order by Tue, 21 Oct",
    because: "Sales climb the week before Diwali.",
    assumed: "Supplier takes 5 days.",
    check: "Open sack in the back counts as stock.",
    note: "Kishore bhai gives better rate on 3 sacks.",
  },
  {
    id: "11",
    flag: "Running low",
    name: "Camlin geometry box",
    shop: "Vidya Stationers, Pune. Cartons of 12.",
    qty: "24",
    unit: "",
    need: "Need about 19. Rounded up to 2 cartons.",
    when: "Order by Mon, 9 Jun",
    because: "New term starts 16 June.",
    assumed: "Last year looks like this year.",
    check: "Two boxes are display pieces.",
    note: "",
  },
  {
    id: "27",
    flag: "Running low",
    name: "Paracetamol 650, strip of 15",
    shop: "Arogya Medicals, Kochi. Boxes of 10 strips.",
    qty: "30",
    unit: "strips",
    need: "Need about 26. Rounded up to 3 boxes.",
    when: "Order by Thu, 17 Jul",
    because: "Monsoon fever weeks sold 40% more last July.",
    assumed: "Distributor visits Thursday.",
    check: "Batch expiring in August, sell first.",
    note: "Ask for the 500 too.",
  },
];

const QUESTIONS: [string, string][] = [
  ["Does it need the internet?", "No. After installing, imports, forecasts and parchis all work offline on the shop computer."],
  ["Which billing software does it read?", "Anything that exports a CSV with a date, a product name and a quantity sold. The import step helps you match columns."],
  ["What is TabPFN?", "An optional forecast model. If it cannot run, the parchi names the baseline that was used instead."],
  ["Will it order for me?", "No. It writes the parchi. You decide what to send the supplier."],
  ["What if I have only a few weeks of sales?", "Those products get a Not enough history note. The app does not invent a confident number."],
];

function ThemePair() {
  const [theme, setTheme] = useState<ThemeName>(() => readTheme());
  useEffect(() => {
    const sync = () => setTheme(readTheme());
    window.addEventListener("dukaan-theme", sync);
    return () => window.removeEventListener("dukaan-theme", sync);
  }, []);
  return (
    <div className="flex items-center rounded-full bg-[var(--sage)] p-1">
      <button type="button" aria-label="Switch to light mode" aria-pressed={theme === "light"} className={`grid size-8 place-items-center rounded-full ${theme === "light" ? "bg-[var(--paper)] text-[var(--ink)]" : "text-[var(--muted)]"}`} onClick={() => applyTheme("light")}>
        <SunIcon />
      </button>
      <button type="button" aria-label="Switch to dark mode" aria-pressed={theme === "dark"} className={`grid size-8 place-items-center rounded-full ${theme === "dark" ? "bg-[var(--paper)] text-[var(--ink)]" : "text-[var(--muted)]"}`} onClick={() => applyTheme("dark")}>
        <MoonIcon />
      </button>
    </div>
  );
}

function SunIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.4">
      <circle cx="8" cy="8" r="2.4" />
      <path d="M8 1.6v1.6M8 12.8v1.6M1.6 8h1.6M12.8 8h1.6M3.4 3.4l1.1 1.1M11.5 11.5l1.1 1.1M12.6 3.4l-1.1 1.1M4.5 11.5l-1.1 1.1" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.4">
      <path d="M10.2 2.2A5.4 5.4 0 1 0 13.8 9 4.2 4.2 0 0 1 10.2 2.2Z" />
    </svg>
  );
}

const SAMPLE_LINES: Record<string, string> = {
  diya: "Order about 40 by Fri, 17 Oct",
  notebook: "Order about 36 by Sat, 18 Oct",
  ors: "Order about 48 by Mon, 20 Oct",
  parle: "Order about 24 by Thu, 16 Oct",
};

const SAMPLE_DATES: Record<number, string[]> = {
  7: ["8 Oct", "11 Oct", "15 Oct", "18 Oct"],
  14: ["10 Sep", "24 Sep", "8 Oct", "22 Oct"],
  30: ["27 Sep", "11 Oct", "25 Oct", "8 Nov"],
};

const REORDER_LABEL: Record<number, string> = {
  7: "Reorder by 15 Oct",
  14: "Reorder by 17 Oct",
  30: "Reorder by 31 Oct",
};

function SampleChart({ productId, horizon }: { productId: string; horizon: number }) {
  const spike = productId === "diya" ? 28 : productId === "notebook" ? 18 : productId === "ors" ? 22 : 8;
  const observed = [8, 9, 7, 10, 9, 11, 10, 12, 11, 14, spike, 16];
  const forecast = horizon === 7 ? [15, 13, 12] : horizon === 30 ? [15, 13, 18, 16, 14, 17] : [15, 13, 18, 16];
  const dates = SAMPLE_DATES[horizon] ?? SAMPLE_DATES[14];
  const width = 640;
  const height = 250;
  const values = [...observed, ...forecast];
  const max = Math.max(...values);
  const step = width / (values.length - 1);
  const y = (value: number) => 28 + (1 - value / max) * 130;
  const line = (rows: number[], offset: number) => rows.map((value, index) => `${(offset + index) * step},${y(value)}`).join(" ");
  const todayAt = (observed.length - 1) * step;
  const reorderAt = (observed.length - 1 + 2) * step;
  const festivalAt = observed.length * step * 0.78;
  return (
    <figure>
      <svg viewBox={`0 0 ${width} ${height}`} className="h-56 w-full" role="img" aria-label={`Illustrative sample forecast from ${dates[0]} to ${dates[3]}`}>
        <line x1="0" x2={width} y1={y(max * 0.35)} y2={y(max * 0.35)} stroke="var(--muted)" strokeDasharray="2 5" />
        <polyline fill="none" stroke="var(--ink)" strokeWidth="2.5" points={line(observed, 0)} />
        <polyline fill="none" stroke="var(--ink)" strokeWidth="2.5" strokeDasharray="6 5" points={line(forecast, observed.length - 1)} />
        <line x1={festivalAt} x2={festivalAt} y1="20" y2="168" stroke="var(--saffron)" strokeDasharray="2 4" />
        <circle cx={reorderAt} cy={y(forecast[1] ?? 14)} r="6" fill="var(--saffron)" />
        <text x={todayAt} y="186" fill="var(--muted)" fontSize="13" textAnchor="end">Today</text>
        <text x={width} y="186" fill="var(--saffron)" fontSize="13" textAnchor="end">{REORDER_LABEL[horizon] ?? REORDER_LABEL[14]}</text>
        {productId === "diya" ? <text x={festivalAt} y="16" fill="var(--saffron)" fontSize="13" textAnchor="middle">Diwali</text> : null}
        {dates.map((date, index) => (
          <text key={date} x={(width / (dates.length - 1)) * index} y="220" fill="var(--muted)" fontSize="14" textAnchor={index === 0 ? "start" : index === dates.length - 1 ? "end" : "middle"}>
            {date}
          </text>
        ))}
      </svg>
      <ChartKey
        className="mt-3"
        items={[
          { kind: "solid", label: "Observed" },
          { kind: "dashed", label: "Forecast" },
          { kind: "dotted", label: "Baseline: 4-week average" },
          { kind: "dot", label: "Reorder by" },
          ...(productId === "diya" ? [{ kind: "tick" as const, label: "Diwali" }] : []),
        ]}
      />
    </figure>
  );
}

export function DemoPanel() {
  const [productId, setProductId] = useState(DEMO_PRODUCTS[0].id);
  const [horizon, setHorizon] = useState<(typeof HORIZONS)[number]>(14);
  const product = DEMO_PRODUCTS.find((item) => item.id === productId) ?? DEMO_PRODUCTS[0];
  const advice = useMemo(() => demoAdvice(product.history, horizon), [product, horizon]);
  const copy = PRODUCT_COPY[product.id] ?? { title: product.name, detail: product.note };
  const orderLine = horizon === 14 ? SAMPLE_LINES[product.id] : `Order about ${advice.total} across ${horizon} days`;

  return (
    <section id="sample" className="scroll-mt-20 bg-[var(--bg)]">
      <div className="mx-auto max-w-6xl px-4 py-16">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="text-4xl text-[var(--ink)] sm:text-5xl">Play with a sample forecast</h2>
            <p className="mt-3 max-w-xl text-[var(--muted)]">Pick a product and a horizon. Watch where the dashed line goes, and where the saffron dot says to reorder.</p>
          </div>
          <div className="flex rounded-full bg-[var(--sage)] p-1" aria-label="Forecast horizon">
            {HORIZONS.map((value) => (
              <button key={value} type="button" className={`rounded-full px-3 py-1.5 text-sm ${horizon === value ? "bg-[var(--paper)] text-[var(--ink)]" : "text-[var(--muted)]"}`} onClick={() => setHorizon(value)}>
                {value} days
              </button>
            ))}
          </div>
        </div>
        <div className="mt-8 rounded-[1.5rem] border border-dashed border-[var(--line)] bg-[var(--paper)] p-4 sm:p-6">
          <p className="text-sm text-[var(--muted)]"><span className="mr-2 inline-block size-2 rounded-full bg-[var(--ok)]" />Sample data &nbsp; Illustrative. Seasonal demonstration, not TabPFN and not your shop.</p>
          <div className="mt-4 grid gap-6 lg:grid-cols-[220px_1fr]">
            <div>
              <p className="text-sm text-[var(--muted)]">Product</p>
              <div className="mt-2 grid gap-2" role="radiogroup" aria-label="Sample products">
                {DEMO_PRODUCTS.map((item) => {
                  const label = PRODUCT_COPY[item.id] ?? { title: item.name, detail: item.note };
                  const selected = item.id === product.id;
                  return (
                    <button key={item.id} type="button" role="radio" aria-checked={selected} className={`rounded-xl border px-3 py-2 text-left text-sm ${selected ? "border-[var(--ok)] bg-[var(--sage)]" : "border-[var(--line)]"}`} onClick={() => setProductId(item.id)}>
                      <span className="block font-medium">{label.title}</span>
                      <span className="text-[var(--muted)]">{label.detail}</span>
                    </button>
                  );
                })}
              </div>
            </div>
            <div>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <h3 className="text-lg">{copy.title.split(",")[0].trim()}, next {horizon} days</h3>
                <p className="text-sm">{orderLine}</p>
              </div>
              <SampleChart productId={product.id} horizon={horizon} />
              <p className="sr-only">
                <span role="rowheader">Example demand over {horizon} days</span> {advice.total}
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Shutter({ className }: { className: string }) {
  return (
    <div className={`overflow-hidden rounded-[1.75rem] bg-[var(--forest)] ${className}`}>
      {Array.from({ length: 12 }).map((_, index) => (
        <div key={index} className="h-5 border-b border-[rgb(244_241_232/0.12)]" />
      ))}
      <div className="absolute bottom-4 left-1/2 h-1.5 w-16 -translate-x-1/2 rounded-full bg-[var(--saffron)]" />
    </div>
  );
}

function ForecastCard() {
  return (
    <article className="rounded-2xl bg-[var(--paper)] p-4 shadow-[var(--shadow)]">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-medium">Classmate notebook, 172 pages</p>
        <span className="shrink-0 rounded-full bg-[var(--sage)] px-2 py-0.5 text-[10px] text-[var(--ok)]">TabPFN v2.5</span>
      </div>
      <p className="mt-1 max-w-[36ch] text-xs text-[var(--muted)]">Sales usually double the week school reopens. Order before Saturday.</p>
      <svg viewBox="0 0 280 118" className="mt-2 h-28 w-full" aria-hidden="true">
        <line x1="4" x2="268" y1="58" y2="58" stroke="var(--series-baseline)" strokeWidth="1.4" strokeDasharray="1.5 4" />
        <polyline fill="none" stroke="var(--ink)" strokeWidth="2" points="4,66 36,68 58,44 84,60 112,56 140,52 168,48 196,24" />
        <polyline fill="none" stroke="var(--ink)" strokeWidth="1.6" strokeDasharray="4 3" points="196,24 232,42 268,54" />
        <circle cx="196" cy="24" r="4.5" fill="var(--saffron)" />
        <text x="4" y="92" fill="var(--muted)" fontSize="10">27 Sep</text>
        <text x="120" y="92" fill="var(--muted)" fontSize="10" textAnchor="middle">Today · 14 Oct</text>
        <text x="196" y="92" fill="var(--saffron)" fontSize="10" textAnchor="middle">18 Oct</text>
        <text x="248" y="108" fill="var(--muted)" fontSize="10" textAnchor="end">School reopens</text>
      </svg>
      <ChartKey
        className="mt-1"
        items={[
          { kind: "solid", label: "Sold" },
          { kind: "dashed", label: "Forecast" },
          { kind: "dotted", label: "Baseline" },
          { kind: "dot", label: "Order by 18 Oct" },
        ]}
      />
    </article>
  );
}

function ParchiCard() {
  return (
    <article className="rounded-2xl bg-[var(--paper)] p-4 shadow-[var(--shadow)]">
      <p className="text-[11px] text-[var(--muted)]">Parchi 14 · 15 Oct <span className="text-[var(--saffron)]">Running low</span></p>
      <h3 className="mt-2 text-xl leading-tight">Classmate notebook</h3>
      <p className="text-xs text-[var(--muted)]">172 pages. Packs of 6.</p>
      <p className="mt-3 text-sm text-[var(--muted)]">Order about <span className="wordmark text-4xl text-[var(--ink)]">36</span></p>
      <p className="text-xs text-[var(--muted)]">Need about 31. Rounded up to 6 packs.</p>
      <p className="mt-2 inline-block rounded-full bg-[var(--sage)] px-2 py-1 text-xs">Order by Sat, 18 Oct</p>
      <dl className="mt-3 grid grid-cols-[4.5rem_1fr] gap-y-1 text-xs">
        <dt className="text-[var(--muted)]">Because</dt><dd>School reopens Monday.</dd>
        <dt className="text-[var(--muted)]">Assumed</dt><dd>Delivery in 4 days.</dd>
        <dt className="text-[var(--muted)]">Check</dt><dd>Shelf count says 11.</dd>
      </dl>
      <p className="mt-2 text-sm italic">Ask about the 200 page one.</p>
      <p className="mt-2 text-[10px] text-[var(--ok)]">TabPFN v2.5</p>
    </article>
  );
}

function HeroBoard() {
  return (
    <div>
      <div className="grid gap-4 md:hidden">
        <Shutter className="relative h-36" />
        <ForecastCard />
        <ParchiCard />
      </div>
      <div className="relative mx-auto hidden h-[540px] w-full max-w-[560px] md:block">
        <Shutter className="absolute left-[12%] right-[4%] top-0 h-[360px]" />
        <div className="absolute bottom-2 left-0 w-[70%]">
          <ForecastCard />
        </div>
        <div className="absolute right-0 top-16 w-[46%]">
          <ParchiCard />
        </div>
      </div>
    </div>
  );
}

export function MarketingPage() {
  return (
    <div className="bg-[var(--bg)] text-[var(--ink)]">
      <a className="skip-link" href="#main">Skip to content</a>
      <header className="sticky top-[var(--wake-h,0px)] z-20 border-b border-transparent bg-[var(--bg)]/95 backdrop-blur">
        <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-2 px-3 sm:gap-4 sm:px-4" aria-label="Primary">
          <BrandMark className="min-w-0 flex-1 text-[15px] sm:text-lg max-[370px]:[&_span]:sr-only" />
          <div className="hidden items-center gap-6 text-sm text-[var(--muted)] lg:flex">
            <a href="#how">How it works</a>
            <a href="#sample">Sample forecast</a>
            <a href="#privacy">Privacy</a>
            <a href="#faq">FAQ</a>
            <a href="https://github.com/ADITYA-KUMAR-2358" target="_blank" rel="noreferrer">GitHub</a>
          </div>
          <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
            <details className="relative lg:hidden">
              <summary aria-label="Menu" className="grid size-10 cursor-pointer list-none place-items-center rounded-full border border-[var(--line)] sm:w-auto sm:px-3">
                <List aria-hidden="true" className="sm:hidden" size={18} />
                <span className="hidden text-sm sm:inline">Menu</span>
              </summary>
              <div className="absolute right-0 z-20 mt-2 grid w-44 gap-3 rounded-xl border border-[var(--line)] bg-[var(--paper)] p-3 text-sm">
                <a href="#how">How it works</a>
                <a href="#sample">Sample forecast</a>
                <a href="#privacy">Privacy</a>
                <a href="#faq">FAQ</a>
              </div>
            </details>
            <ThemePair />
            <Link to="/app" className="whitespace-nowrap rounded-full bg-[var(--btn)] px-3 py-2 text-sm font-medium text-[var(--btn-text)] sm:px-4">Open Shutters</Link>
          </div>
        </nav>
      </header>
      <main id="main">
        <section className="mx-auto grid max-w-6xl items-center gap-10 px-4 py-12 lg:grid-cols-2 lg:py-16">
          <div>
            <h1 className="max-w-[12ch] text-5xl leading-[1.02] sm:text-6xl">Kam andaaza. Sahi stock. Behtar dukaan.</h1>
            <p className="mt-6 max-w-[42ch] text-[var(--muted)]">DukaanDost reads the billing export from your kirana, stationery or medical shop on your own computer, and writes you a parchi: what to reorder, how much, by when, and why.</p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link to="/app" className="rounded-full bg-[var(--btn)] px-5 py-2.5 text-sm font-medium text-[var(--btn-text)]">Open Shutters</Link>
              <a href="#sample" className="rounded-full border border-[var(--ink)] px-5 py-2.5 text-sm">See a sample forecast</a>
            </div>
            <p className="mt-6 flex flex-wrap items-center gap-3 text-sm text-[var(--muted)]">
              <span className="rounded-full bg-[var(--sage)] px-3 py-1 text-[var(--ink)]">On this computer</span>
              Open source. Your sales stay on the shop computer.
            </p>
          </div>
          <HeroBoard />
        </section>

        <DemoPanel />

        <section id="how" className="scroll-mt-20">
          <div className="mx-auto max-w-6xl px-4 py-16">
            <h2 className="text-4xl sm:text-5xl">How it works</h2>
            <p className="mt-3 text-[var(--muted)]">Four steps between the end of the day and an order you trust.</p>
            <ol className="mt-10 grid gap-8 border-t border-[var(--line)] pt-8 sm:grid-cols-2 lg:grid-cols-4">
              {STEPS.map(([title, copy], index) => (
                <li key={title}>
                  <p className={`wordmark text-4xl ${index === 3 ? "text-[var(--saffron)]" : ""}`}><span className="mr-2">{index + 1}</span>{title}</p>
                  <p className="mt-3 text-sm text-[var(--muted)]">{copy}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 pb-16">
          <h2 className="text-4xl sm:text-5xl">What it does at the counter</h2>
          <p className="mt-3 text-[var(--muted)]">Not a dashboard. A short list of things to order, written the way you would write them.</p>
          <ol className="mt-8 overflow-hidden rounded-[1.5rem] border border-[var(--line)] bg-[var(--paper)]">
            {COUNTER.map((item) => (
              <li key={item.n} className="flex items-start gap-3 border-b border-l-2 border-[var(--line)] border-l-[var(--saffron)] px-4 py-4 last:border-b-0 sm:items-center sm:gap-4 sm:px-6">
                <item.Icon aria-hidden="true" size={26} weight="regular" className="mt-0.5 shrink-0 text-[var(--ink)] sm:mt-0" />
                <span className="shrink-0 text-sm text-[var(--saffron)]">{item.n}</span>
                <div className="min-w-0 flex-1">
                  <h3 className="text-lg">{item.title}</h3>
                  <p className="text-sm text-[var(--muted)]">{item.copy}</p>
                </div>
                <span className="hidden shrink-0 text-sm text-[var(--muted)] sm:block">{item.where}</span>
              </li>
            ))}
          </ol>
        </section>

        <section id="privacy" className="scroll-mt-20 bg-[var(--sage)]">
          <div className="mx-auto max-w-6xl px-4 py-16">
            <h2 className="max-w-[16ch] text-4xl sm:text-5xl">Where your sales data lives</h2>
            <p className="mt-3 text-[var(--muted)]">Said plainly, because it is your shop.</p>
            <div className="mt-10 grid gap-10 border-t border-[var(--line)] pt-8 md:grid-cols-2">
              <article>
                <p className="text-sm">On this computer</p>
                <h3 className="mt-3 text-xl">Installed on your computer: data stays on that computer.</h3>
                <p className="mt-3 text-sm text-[var(--muted)]">Imports, forecasts and parchis are stored in a file on the machine you run DukaanDost on. Nothing is uploaded. The forecasting model runs locally too.</p>
              </article>
              <article>
                <p className="inline-flex rounded-full border border-[var(--saffron)] px-3 py-1 text-sm text-[var(--saffron)]">Hosted demo. Not private to you.</p>
                <h3 className="mt-3 text-xl">A hosted instance is not private to you.</h3>
                <p className="mt-3 text-sm text-[var(--muted)]">If you open a DukaanDost someone else runs on a server, including our public demo, whatever you import sits on their server. Use the demo with sample data only.</p>
              </article>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 py-16">
          <h2 className="max-w-[16ch] text-4xl sm:text-5xl">Three parchis from shops that do not exist</h2>
          <p className="mt-4 max-w-2xl text-[var(--muted)]">Every name, product and number below is made up, to show the shape of a suggestion. None of it is a customer.</p>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {PARCHIS.map((card) => (
              <article key={card.id} className="flex h-full flex-col rounded-2xl border border-[var(--line)] bg-[var(--paper)] p-5 shadow-[var(--shadow)]">
                <p className="text-xs text-[var(--muted)]">Parchi {card.id} · Fictional <span className="ml-1 text-[var(--saffron)]">{card.flag}</span></p>
                <h3 className="mt-4 text-2xl">{card.name}</h3>
                <p className="text-sm text-[var(--muted)]">{card.shop}</p>
                <p className="mt-4 text-sm text-[var(--muted)]">Order about <span className="wordmark text-4xl text-[var(--ink)]">{card.qty}</span> {card.unit}</p>
                <p className="text-sm text-[var(--muted)]">{card.need}</p>
                <p className="mt-3 inline-block rounded-full bg-[var(--sage)] px-3 py-1 text-sm">{card.when}</p>
                <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-3 gap-y-2 text-sm">
                  <dt className="text-[var(--muted)]">Because</dt><dd>{card.because}</dd>
                  <dt className="text-[var(--muted)]">Assumed</dt><dd>{card.assumed}</dd>
                  <dt className="text-[var(--muted)]">Check</dt><dd>{card.check}</dd>
                </dl>
                {card.note ? <p className="mt-4 italic">{card.note}</p> : <p className="mt-4">&nbsp;</p>}
                <p className="mt-auto pt-4 text-xs text-[var(--ok)]">Sample data</p>
                <p className="mt-2 text-xs text-[var(--muted)]">Fictional shop. Invented numbers.</p>
              </article>
            ))}
          </div>
        </section>

        <section id="faq" className="scroll-mt-20 border-t border-[var(--line)]">
          <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 lg:grid-cols-[0.7fr_1.3fr]">
            <div>
              <h2 className="max-w-[12ch] text-4xl sm:max-w-[8ch] sm:text-5xl">Questions shopkeepers ask</h2>
              <p className="mt-4 text-sm text-[var(--muted)]">And one honest page about what it cannot do.</p>
              <a className="mt-4 inline-block text-sm underline" href="/limits">Read the limits at /limits</a>
            </div>
            <div>
              {QUESTIONS.map(([question, answer], index) => (
                <details key={question} open={index < 2} className="border-t border-[var(--line)] py-4">
                  <summary className="cursor-pointer font-medium">{question}</summary>
                  <p className="mt-2 text-sm text-[var(--muted)]">{answer}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-[var(--forest)] text-[var(--on-forest)]">
          <div className="mx-auto max-w-3xl px-4 py-20 text-center">
            <h2 className="text-4xl leading-tight sm:text-5xl">Close the day knowing what to order tomorrow.</h2>
            <p className="mt-4 text-[var(--on-forest-muted)]">Free and open source. Runs on the shop computer you already have.</p>
            <Link to="/app" className="mt-6 inline-block rounded-full bg-[var(--on-forest)] px-5 py-2.5 text-sm font-medium text-[var(--forest)]">Open Shutters</Link>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
