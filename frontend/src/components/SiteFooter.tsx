import { GithubLogo, Heart } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import { BrandMark } from "./BrandMark";

const COLUMNS = [
  {
    title: "Shop",
    links: [
      ["Open Shutters", "/app"],
      ["Sample forecast", "/#sample"],
      ["How it works", "/#how"],
    ],
  },
  {
    title: "Help",
    links: [
      ["Questions", "/#faq"],
      ["Limits", "/limits"],
      ["Security", "/limits#security"],
    ],
  },
  {
    title: "About",
    links: [
      ["Privacy", "/#privacy"],
      ["License", "/limits#license"],
      ["GitHub", "https://github.com/ADITYA-KUMAR-2358"],
    ],
  },
] as const;

function FooterLink({ label, href }: { label: string; href: string }) {
  const className = "inline-flex min-h-9 items-center text-[15px] text-[var(--ink)] hover:underline";
  if (href.startsWith("http")) {
    return (
      <a className={className} href={href} target="_blank" rel="noreferrer">
        {label}
      </a>
    );
  }
  if (href.startsWith("/#")) {
    return (
      <a className={className} href={href}>
        {label}
      </a>
    );
  }
  return (
    <Link className={className} to={href}>
      {label}
    </Link>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t border-[var(--line)] bg-[var(--bg)] text-[var(--ink)]">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:py-10">
        <div className="lg:grid lg:grid-cols-4 lg:gap-10">
          <div className="max-w-md">
            <BrandMark className="text-2xl sm:text-[1.65rem]" />
            <p className="tagline mt-4 text-xl text-[var(--ink)] sm:text-[1.35rem]">Kam andaaza. Sahi stock. Behtar dukaan.</p>
            <p className="mt-3 text-[15px] leading-relaxed text-[var(--muted)]">
              Billing records become stock advice a shop can check before the next purchase.
            </p>
          </div>
          <div className="mt-8 grid grid-cols-3 gap-x-3 gap-y-6 lg:contents lg:mt-0">
            {COLUMNS.map((column) => (
              <nav key={column.title} aria-label={column.title}>
                <p className="text-[15px] font-semibold">{column.title}</p>
                <ul className="mt-2 grid sm:mt-3">
                  {column.links.map(([label, href]) => (
                    <li key={label}>
                      <FooterLink label={label} href={href} />
                    </li>
                  ))}
                </ul>
              </nav>
            ))}
          </div>
        </div>
        <p className="mt-8 text-sm leading-relaxed text-[var(--muted)] sm:mt-10">
          The sample kirana is fictional. Forecasts are estimates, not a promise of tomorrow&apos;s sales. This application is MIT licensed. TabPFN weights have their own license.
        </p>
      </div>
      <div className="border-t border-[var(--line)]">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] sm:flex-row sm:items-center sm:justify-between">
          <p className="tagline flex items-center gap-2 text-xl sm:text-[1.35rem]">
            Built by Aditya Kumar
            <Heart aria-hidden="true" size={16} weight="fill" className="text-[var(--saffron)]" />
          </p>
          <a
            className="inline-flex min-h-11 w-fit items-center gap-2 rounded-full border border-[var(--line)] bg-[var(--paper)] px-4 text-sm text-[var(--ink)]"
            href="https://github.com/ADITYA-KUMAR-2358"
            target="_blank"
            rel="noreferrer"
          >
            <GithubLogo aria-hidden="true" size={16} weight="regular" />
            Aditya on GitHub
          </a>
        </div>
      </div>
    </footer>
  );
}
