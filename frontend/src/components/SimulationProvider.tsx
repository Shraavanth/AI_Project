"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { api, ApiError, WS_URL } from "@/lib/api";
import type { Snapshot } from "@/lib/types";

export type Connection = "connecting" | "live" | "polling" | "offline";

interface Toast {
  id: number;
  kind: "ok" | "error" | "info";
  text: string;
}

interface SimContextValue {
  snapshot: Snapshot | null;
  connection: Connection;
  lastUpdate: number | null;
  /** POST an action; shows a toast with the result. Returns the response or null on error. */
  act: <T = unknown>(path: string, body?: unknown, success?: string) => Promise<T | null>;
  refresh: () => Promise<void>;
  toasts: Toast[];
  notify: (kind: Toast["kind"], text: string) => void;
  dismiss: (id: number) => void;
}

const SimContext = createContext<SimContextValue | null>(null);

export function useSim() {
  const ctx = useContext(SimContext);
  if (!ctx) throw new Error("useSim must be used inside SimulationProvider");
  return ctx;
}

/**
 * Keeps one live copy of the backend state for every page.
 * 1. WebSocket /ws pushes a full snapshot every tick.
 * 2. If the socket drops, it reconnects with back-off (1 s, 2 s, 4 s ... 10 s)
 *    and meanwhile polls GET /api/state every 2 s.
 * The frontend never invents agent positions - it only draws what the backend sends.
 */
export function SimulationProvider({ children }: { children: React.ReactNode }) {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [connection, setConnection] = useState<Connection>("connecting");
  const [lastUpdate, setLastUpdate] = useState<number | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const toastId = useRef(0);
  const wsRef = useRef<WebSocket | null>(null);
  const retry = useRef(0);
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const alive = useRef(true);

  const notify = useCallback((kind: Toast["kind"], text: string) => {
    const id = ++toastId.current;
    setToasts((t) => [...t.slice(-3), { id, kind, text }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), kind === "error" ? 7000 : 4000);
  }, []);
  const dismiss = useCallback((id: number) => setToasts((t) => t.filter((x) => x.id !== id)), []);

  const accept = useCallback((data: Snapshot) => {
    setSnapshot(data);
    setLastUpdate(Date.now());
  }, []);

  const refresh = useCallback(async () => {
    try {
      accept(await api.get<Snapshot>("/api/state"));
      return;
    } catch {
      setConnection((c) => (c === "live" ? c : "offline"));
    }
  }, [accept]);

  const startPolling = useCallback(() => {
    if (pollTimer.current) return;
    pollTimer.current = setInterval(async () => {
      try {
        accept(await api.get<Snapshot>("/api/state"));
        setConnection((c) => (c === "live" ? c : "polling"));
      } catch {
        setConnection((c) => (c === "live" ? c : "offline"));
      }
    }, 2000);
  }, [accept]);

  const stopPolling = useCallback(() => {
    if (pollTimer.current) clearInterval(pollTimer.current);
    pollTimer.current = null;
  }, []);

  const connect = useCallback(() => {
    if (!alive.current) return;
    let ws: WebSocket;
    try {
      ws = new WebSocket(WS_URL);
    } catch {
      startPolling();
      return;
    }
    wsRef.current = ws;
    let pinger: ReturnType<typeof setInterval> | null = null;
    ws.onopen = () => {
      retry.current = 0;
      setConnection("live");
      stopPolling();
      pinger = setInterval(() => ws.readyState === WebSocket.OPEN && ws.send("ping"), 20000);
    };
    ws.onmessage = (event) => {
      if (event.data === "pong") return;
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "state") accept(msg.data as Snapshot);
      } catch {
        /* ignore malformed frames */
      }
    };
    ws.onclose = () => {
      if (pinger) clearInterval(pinger);
      if (!alive.current) return;
      setConnection((c) => (c === "live" || c === "connecting" ? "polling" : c));
      startPolling();
      const delay = Math.min(10000, 1000 * 2 ** retry.current);
      retry.current += 1;
      reconnectTimer.current = setTimeout(connect, delay);
    };
    ws.onerror = () => ws.close();
  }, [accept, startPolling, stopPolling]);

  useEffect(() => {
    alive.current = true;
    refresh();
    connect();
    return () => {
      alive.current = false;
      stopPolling();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect, refresh, stopPolling]);

  const act = useCallback(
    async <T,>(path: string, body?: unknown, success?: string): Promise<T | null> => {
      try {
        const result = await api.post<T>(path, body);
        if (success) notify("ok", success);
        if (connection !== "live") refresh();
        return result;
      } catch (err) {
        notify("error", err instanceof ApiError ? err.message : "Action failed");
        return null;
      }
    },
    [connection, notify, refresh],
  );

  return (
    <SimContext.Provider value={{ snapshot, connection, lastUpdate, act, refresh, toasts, notify, dismiss }}>
      {children}
    </SimContext.Provider>
  );
}
