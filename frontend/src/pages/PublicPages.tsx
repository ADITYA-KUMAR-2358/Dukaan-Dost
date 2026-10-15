import { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { BackLink } from "../components/BackLink";
import { BrandMark } from "../components/BrandMark";
import { ClosedShutter } from "../components/ClosedShutter";
import { SiteFooter } from "../components/SiteFooter";
import { ThemeSwitch } from "../components/ThemeSwitch";

function PublicBar() {
  return (
    <div className="flex justify-end px-4 py-4">
      <ThemeSwitch />
    </div>
  );
}

export function NotFoundPage() {
  const heading = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    const previous = document.title;
    document.title = "Page not found | DukaanDost";
    heading.current?.focus();
    return () => {
      document.title = previous;
    };
  }, []);

  return (
    <div className="flex min-h-[100dvh] flex-col">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="sticky top-[var(--wake-h,0px)] z-20 border-b border-[var(--line)] bg-[var(--bg)]">
        <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4" aria-label="Primary">
          <BrandMark className="text-xl sm:text-2xl" />
          <ThemeSwitch />
        </nav>
      </header>
      <main id="main" className="mx-auto grid w-full max-w-6xl flex-1 items-center gap-10 px-4 py-12 md:grid-cols-2 md:py-16">
        <div>
          <h1 ref={heading} tabIndex={-1} className="max-w-[10ch] text-5xl leading-[1.02] outline-none sm:text-6xl">
            Oops, shopkeeper!
            <span className="sr-only"> Error 404</span>
          </h1>
          <p className="mt-6 max-w-[28ch] text-lg text-[var(--muted)]">The shop is closed, not the system.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/" className="rounded-full bg-[var(--btn)] px-5 py-2.5 text-sm font-medium text-[var(--btn-text)]">
              Back to Shop
            </Link>
            <Link to="/app" className="rounded-full border border-[var(--ink)] px-5 py-2.5 text-sm">
              Open Shutters
            </Link>
          </div>
        </div>
        <ClosedShutter />
      </main>
      <SiteFooter />
    </div>
  );
}

export function LimitsPage() {
  return (
    <div>
    <PublicBar />
    <main className="mx-auto max-w-2xl px-4 pb-16">
      <BackLink to="/">Home</BackLink>
      <h1 className="text-4xl font-semibold">Limits</h1>
      <ul className="mt-6 list-disc space-y-3 pl-5 text-[var(--muted)]">
        <li>Forecasts are estimates. They are not a promise of tomorrow's sales.</li>
        <li>TabPFN runs only when the package, weights, and history are all available. Otherwise you see a named baseline.</li>
        <li>Gemma explanations need an API key in .env. Without it, the wording is a template built from the same numbers.</li>
        <li>Photographed ledgers are not read.</li>
        <li>This version is one shop on one computer, without accounts.</li>
      </ul>
      <h2 id="security" className="mt-10 text-2xl">Security</h2>
      <p className="mt-3 text-[var(--muted)]">
        The shop database is a SQLite file on this computer. Do not commit .env, and do not upload a real billing CSV to a machine you do not control.
      </p>
      <h2 id="license" className="mt-10 text-2xl">License</h2>
      <p className="mt-3 text-[var(--muted)]">
        The application is MIT licensed. TabPFN model weights have their own license. The Simsa shop photograph is CC BY-SA 4.0.
      </p>
    </main>
    <SiteFooter />
    </div>
  );
}

export function RouteErrorPage() {
  return (
    <div className="flex min-h-[100dvh] flex-col">
    <PublicBar />
    <main className="mx-auto flex w-full max-w-xl flex-1 flex-col justify-center px-4">
      <h1 className="text-4xl font-semibold">The app hit a problem.</h1>
      <p className="mt-3 text-[var(--muted)]">Refresh the page. If you were importing a file, check the column mapping and try again.</p>
      <Link to="/app" className="btn mt-6 w-fit">
        Return to the shop
      </Link>
    </main>
    <SiteFooter />
    </div>
  );
}
