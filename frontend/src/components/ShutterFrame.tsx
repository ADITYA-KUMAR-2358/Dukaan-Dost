import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { useRef, useState, type ReactNode } from "react";

const SEEN = "dukaan-shutter";

function seenAlready() {
  try {
    return sessionStorage.getItem(SEEN) === "1";
  } catch {
    return false;
  }
}

export function ShutterFrame({ children }: { children: ReactNode }) {
  const frame = useRef<HTMLDivElement>(null);
  const cover = useRef<HTMLDivElement>(null);
  const [played] = useState(seenAlready);

  useGSAP(
    () => {
      const motion = gsap.matchMedia();
      motion.add("(prefers-reduced-motion: no-preference)", () => {
        if (!cover.current || played) return;
        gsap.fromTo(
          cover.current,
          { yPercent: 0 },
          {
            yPercent: -110,
            duration: 0.7,
            ease: "expo.out",
            onComplete: () => {
              try {
                sessionStorage.setItem(SEEN, "1");
              } catch {
                /* private mode */
              }
            },
          },
        );
      });
      return () => motion.revert();
    },
    { scope: frame },
  );

  return (
    <div ref={frame} className="relative overflow-hidden rounded-[var(--r)]">
      {children}
      {played ? null : <div ref={cover} className="shutter-cover slats pointer-events-none absolute inset-0" aria-hidden="true" />}
    </div>
  );
}
