import { CircleNotch } from "@phosphor-icons/react";
import { useEffect, useState } from "react";
import { apiBase } from "../lib/api";

const SLOW_AFTER_SECONDS = 60;
const SHOW_AFTER_MS = 1500;
const RETRY_MS = 4000;
const KEEP_ALIVE_MS = 8 * 60 * 1000;

export function isHostedHost(hostname: string) {
  return hostname !== "localhost" && hostname !== "127.0.0.1" && hostname !== "[::1]";
}

export function ServerWake() {
  const [waking, setWaking] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!isHostedHost(window.location.hostname)) return;
    let stopped = false;
    const started = performance.now();
    const clock = window.setInterval(() => {
      if (!stopped) setSeconds(Math.floor((performance.now() - started) / 1000));
    }, 1000);

    async function waitUntilReady() {
      const reveal = window.setTimeout(() => {
        if (!stopped) setWaking(true);
      }, SHOW_AFTER_MS);
      while (!stopped) {
        const controller = new AbortController();
        const limit = window.setTimeout(() => controller.abort(), 60_000);
        try {
          const response = await fetch(`${apiBase()}/health`, { signal: controller.signal, cache: "no-store" });
          if (response.ok) {
            window.clearTimeout(reveal);
            window.clearInterval(clock);
            if (!stopped) setWaking(false);
            return;
          }
        } catch {
          // A free Render instance hangs or refuses the request while it starts.
        } finally {
          window.clearTimeout(limit);
        }
        window.clearTimeout(reveal);
        if (!stopped) setWaking(true);
        await new Promise((resolve) => window.setTimeout(resolve, RETRY_MS));
      }
    }

    void waitUntilReady();
    return () => {
      stopped = true;
      window.clearInterval(clock);
    };
  }, [attempt]);

  useEffect(() => {
    if (!isHostedHost(window.location.hostname)) return;
    const timer = window.setInterval(() => {
      void fetch(`${apiBase()}/health`, { cache: "no-store" })
        .then((response) => {
          if (!response.ok) setAttempt((value) => value + 1);
        })
        .catch(() => setAttempt((value) => value + 1));
    }, KEEP_ALIVE_MS);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const node = document.documentElement;
    const clear = () => {
      node.style.removeProperty("--wake-h");
      document.body.style.paddingTop = "";
    };
    if (!waking) {
      clear();
      return;
    }
    const bar = document.getElementById("server-wake");
    const apply = () => {
      const height = `${bar?.offsetHeight ?? 0}px`;
      node.style.setProperty("--wake-h", height);
      document.body.style.paddingTop = height;
    };
    apply();
    const observer = new ResizeObserver(apply);
    if (bar) observer.observe(bar);
    return () => {
      observer.disconnect();
      clear();
    };
  }, [waking, seconds]);

  if (!waking) return null;

  return (
    <div id="server-wake" role="status" className="fixed inset-x-0 top-0 z-40 flex flex-wrap items-center justify-between gap-x-4 gap-y-2 bg-[var(--saffron)] px-4 py-2 text-sm text-[#17261f]">
      <p className="flex min-w-0 items-center gap-2">
        <CircleNotch aria-hidden="true" size={18} weight="bold" className="shrink-0 motion-safe:animate-spin" />
        <span>
          {seconds > SLOW_AFTER_SECONDS
            ? "Still starting. Taking longer than usual, it should be ready soon."
            : "The free server was asleep and is starting. This takes up to a minute."}
        </span>
      </p>
      <span className="flex items-center gap-3">
        <span className="nums" aria-hidden="true">{seconds}s</span>
        <button type="button" className="min-h-9 underline" onClick={() => setAttempt((value) => value + 1)}>
          Try again
        </button>
      </span>
    </div>
  );
}
