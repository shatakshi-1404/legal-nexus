import { useEffect, useRef } from "react";

/** Calls fn every `ms` until it returns true (done). */
export function usePolling(fn: () => Promise<boolean>, ms = 2000, deps: unknown[] = []) {
  const saved = useRef(fn);
  saved.current = fn;
  useEffect(() => {
    let stop = false;
    const tick = async () => {
      if (stop) return;
      const done = await saved.current().catch(() => false);
      if (!done && !stop) setTimeout(tick, ms);
    };
    tick();
    return () => { stop = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
