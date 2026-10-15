import { useGSAP } from "@gsap/react";
import type { Icon } from "@phosphor-icons/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useRef, type ReactNode } from "react";

gsap.registerPlugin(useGSAP, ScrollTrigger);

type Tag = "h1" | "h2";

export function RevealText({
  text,
  as = "h1",
  className,
}: {
  text: string;
  as?: Tag;
  className?: string;
}) {
  const ref = useRef<HTMLHeadingElement>(null);
  const TagName = as;
  const words = text.split(" ");

  useGSAP(
    () => {
      const motion = gsap.matchMedia();
      motion.add("(prefers-reduced-motion: no-preference)", () => {
        gsap.from("[data-word]", {
          y: 28,
          autoAlpha: 0,
          duration: 0.72,
          stagger: 0.045,
          ease: "power3.out",
        });
      });
    },
    { scope: ref, dependencies: [text], revertOnUpdate: true },
  );

  return (
    <TagName ref={ref} className={className}>
      {words.map((word, index) => (
        <span key={`${word}-${index}`} className="inline-block pb-1 align-bottom">
          <span data-word className="inline-block">
            {word}
            {index < words.length - 1 ? "\u00A0" : ""}
          </span>
        </span>
      ))}
    </TagName>
  );
}

export function ShopPhoto({ src, alt, className }: { src: string; alt: string; className?: string }) {
  const ref = useRef<HTMLImageElement>(null);

  useGSAP(
    () => {
      const motion = gsap.matchMedia();
      motion.add("(prefers-reduced-motion: no-preference)", () => {
        gsap.from(ref.current, {
          autoAlpha: 0,
          y: 20,
          duration: 0.7,
          ease: "power2.out",
          scrollTrigger: { trigger: ref.current, start: "top 88%" },
        });
      });
    },
    { scope: ref },
  );

  return <img ref={ref} src={src} alt={alt} className={className} />;
}

export function DrawnIcon({ icon: Icon }: { icon: Icon }) {
  const ref = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const motion = gsap.matchMedia();
      motion.add("(prefers-reduced-motion: no-preference)", () => {
        const shapes = ref.current?.querySelectorAll<SVGGeometryElement>("path, circle, line, polyline, polygon, rect");
        if (!shapes?.length) return;
        const timeline = gsap.timeline({
          scrollTrigger: { trigger: ref.current, start: "top 88%", once: true },
        });
        shapes.forEach((shape, index) => {
          let length = 0;
          try {
            length = shape.getTotalLength();
          } catch {
            return;
          }
          if (!length) return;
          gsap.set(shape, { strokeDasharray: length, strokeDashoffset: length, immediateRender: false });
          timeline.to(shape, { strokeDashoffset: 0, duration: 0.85, ease: "power2.out" }, index * 0.08);
        });
      });
      return () => motion.revert();
    },
    { scope: ref },
  );

  return (
    <div ref={ref} className="grid size-16 place-items-center rounded-full bg-[var(--sage)] text-[var(--saffron)]" aria-hidden="true">
      <Icon size={30} weight="regular" />
    </div>
  );
}

export function RiseGroup({ children, className }: { children: ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const motion = gsap.matchMedia();
      motion.add("(prefers-reduced-motion: no-preference)", () => {
        gsap.from("[data-rise]", {
          y: 22,
          autoAlpha: 0,
          duration: 0.65,
          stagger: 0.08,
          ease: "power2.out",
          scrollTrigger: { trigger: ref.current, start: "top 92%", once: true },
          immediateRender: false,
        });
      });
    },
    { scope: ref },
  );

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}
