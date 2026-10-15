import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { useId, useRef, useState } from "react";

const REPLY = "Sorry! Come back tomorrow!";

export function ClosedShutter() {
  const root = useRef<HTMLDivElement>(null);
  const shutter = useRef<HTMLDivElement>(null);
  const timer = useRef(0);
  const [note, setNote] = useState("");
  const patternId = useId().replace(/:/g, "");

  const { contextSafe } = useGSAP(
    () => () => window.clearTimeout(timer.current),
    { scope: root },
  );

  const rattle = contextSafe(() => {
    window.clearTimeout(timer.current);
    setNote("");
    timer.current = window.setTimeout(() => setNote(REPLY), 30);
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce || !shutter.current) return;
    gsap.killTweensOf(shutter.current);
    gsap.set(shutter.current, { x: 0 });
    gsap.to(shutter.current, {
      keyframes: [
        { x: -6, duration: 0.05 },
        { x: 5, duration: 0.06 },
        { x: -4, duration: 0.07 },
        { x: 3, duration: 0.07 },
        { x: -2, duration: 0.07 },
        { x: 1, duration: 0.06 },
        { x: 0, duration: 0.08 },
      ],
      ease: "power2.out",
    });
  });

  return (
    <div ref={root} className="mx-auto w-full max-w-[24rem]">
      <div className="overflow-hidden rounded-[var(--r)] border border-[var(--line)] bg-[var(--paper)]">
        <svg viewBox="0 0 360 128" className="block h-auto w-full" aria-hidden="true">
          <rect width="360" height="128" fill="var(--paper)" />
          <ellipse cx="180" cy="96" rx="130" ry="22" fill="var(--saffron)" opacity="0.22" />
          <rect x="118" y="14" width="124" height="7" rx="3" fill="var(--on-forest)" />
          <rect x="40" y="36" width="280" height="64" rx="6" fill="var(--forest)" />
          <text x="180" y="76" textAnchor="middle" fill="var(--on-forest)" fontFamily="Spectral, serif" fontSize="22">
            Sharma General Store
          </text>
        </svg>
        <button
          type="button"
          className="mx-5 mb-2 block w-[calc(100%-2.5rem)] cursor-pointer border-0 bg-transparent p-0"
          aria-label="Rattle the closed shop shutter"
          onClick={rattle}
        >
          <div ref={shutter}>
            <svg viewBox="0 0 320 250" className="block h-auto w-full" aria-hidden="true">
              <defs>
                <pattern id={patternId} width="320" height="16" patternUnits="userSpaceOnUse">
                  <rect width="320" height="12" fill="var(--forest)" />
                  <rect y="12" width="320" height="4" fill="var(--on-forest)" opacity="0.16" />
                </pattern>
              </defs>
              <rect width="320" height="250" fill={`url(#${patternId})`} />
              <text x="46" y="58" fill="var(--on-forest)" opacity="0.28" fontFamily="Familjen Grotesk, sans-serif" fontSize="16">
                Nimbu Cola
              </text>
              <text x="188" y="214" fill="var(--saffron)" opacity="0.4" fontFamily="Familjen Grotesk, sans-serif" fontSize="15">
                Rani Biscuits
              </text>
              <text x="160" y="132" textAnchor="middle" fill="var(--on-forest)" opacity="0.72" fontFamily="Spectral, serif" fontSize="64">
                404
              </text>
              <rect x="136" y="148" width="48" height="34" rx="5" fill="var(--saffron)" />
              <path d="M148 150 v-12 a12 12 0 0 1 24 0 v12" fill="none" stroke="var(--saffron)" strokeWidth="5" />
              <circle cx="160" cy="164" r="3.5" fill="var(--forest)" />
            </svg>
          </div>
        </button>
        <div className="parchi mx-5 mb-5 bg-[var(--sage)] text-[var(--ink)] shadow-none">
          <p className="text-sm">TODAY&apos;S STOCK: One missing page!</p>
        </div>
      </div>
      <p role="status" aria-live="polite" className="mt-3 min-h-6 text-sm text-[var(--ink)]">
        {note}
      </p>
    </div>
  );
}
