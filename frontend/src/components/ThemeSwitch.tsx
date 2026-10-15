import { Moon, Sun } from "@phosphor-icons/react";
import { useEffect, useState } from "react";

export type ThemeName = "light" | "dark";

const KEY = "dukaan-theme";

export function readTheme(): ThemeName {
  const stored = localStorage.getItem(KEY);
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function applyTheme(next: ThemeName) {
  document.documentElement.dataset.theme = next;
  localStorage.setItem(KEY, next);
  window.dispatchEvent(new Event("dukaan-theme"));
}

export function ThemeSwitch() {
  const [theme, setTheme] = useState<ThemeName>(() => readTheme());

  useEffect(() => {
    const sync = () => setTheme(readTheme());
    sync();
    window.addEventListener("dukaan-theme", sync);
    return () => window.removeEventListener("dukaan-theme", sync);
  }, []);

  const next: ThemeName = theme === "dark" ? "light" : "dark";
  const label = next === "dark" ? "Switch to dark mode" : "Switch to light mode";

  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className="inline-flex size-12 shrink-0 items-center justify-center rounded-full border border-[var(--line)] bg-[var(--pill)] text-[var(--pill-text)]"
      onClick={() => applyTheme(next)}
    >
      {theme === "dark" ? <Sun aria-hidden="true" size={18} weight="regular" /> : <Moon aria-hidden="true" size={18} weight="regular" />}
    </button>
  );
}
