"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "./api";

/** Fetch a backend path now and every `intervalMs` (0 = only once / on reload). */
export function usePolling<T>(path: string | null, intervalMs = 0) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const current = useRef(path);
  current.current = path;

  const load = useCallback(async () => {
    if (!path) return;
    setLoading(true);
    try {
      const result = await api.get<T>(path);
      if (current.current === path) {
        setData(result);
        setError(null);
      }
    } catch (err) {
      if (current.current === path) setError(err instanceof ApiError ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }, [path]);

  useEffect(() => {
    setData(null);
    if (!path) return;
    load();
    if (!intervalMs) return;
    const timer = setInterval(load, intervalMs);
    return () => clearInterval(timer);
  }, [path, intervalMs, load]);

  return { data, error, loading, reload: load };
}
