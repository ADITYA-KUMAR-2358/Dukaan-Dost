import { useCallback, useEffect, useState } from "react";
import { api } from "./api";

export type Status = {
  active_shop_id: string | null;
  shop: { id: string; name: string; is_demo: boolean } | null;
  explanation_mode: string;
  tabpfn: { installed: boolean; package_version: string | null; requested_version: string; detail: string };
  gemma: { ready: boolean; configured_model: string };
};

export function useStatus() {
  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      setStatus(await api<Status>("/api/status"));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The shop service is not responding.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { status, error, loading, reload };
}
