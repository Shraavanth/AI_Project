"use client";

import { Crosshair, LocateFixed, MapPin, Search, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useSim } from "./SimulationProvider";
import { Button } from "./ui";

export const LOCATION_KEY = "envmas.location.v1";

export type GeoStatus = "idle" | "requesting" | "granted" | "denied" | "unavailable" | "insecure";

const GEO_TEXT: Record<GeoStatus, string> = {
  idle: "",
  requesting: "Waiting for location permission in your browser...",
  granted: "Centred on your approximate location.",
  denied: "Location access is unavailable. Search for your monitoring area or select a location on the map.",
  unavailable: "Your browser could not provide a location. Search for your monitoring area or select a location on the map.",
  insecure: "Automatic location needs a secure page (HTTPS or localhost). Search for your monitoring area or select a location on the map.",
};

function safeStorage(action: "get" | "set", value?: string) {
  try {
    if (action === "get") return window.localStorage.getItem(LOCATION_KEY);
    window.localStorage.setItem(LOCATION_KEY, value ?? "");
  } catch {
    /* private mode / storage blocked: behave as a first visit */
  }
  return null;
}

/** Round to ~110 m so the exact position of the person is never stored or shown. */
const approx = (x: number) => Math.round(x * 1000) / 1000;

/**
 * Browser geolocation with permission, plus fallbacks.
 * On the first visit (nothing stored) it asks the browser for the location
 * once. The browser shows its own permission prompt; nothing happens silently.
 */
export function useGeolocation(radius: number) {
  const { act, snapshot } = useSim();
  const [status, setStatus] = useState<GeoStatus>("idle");
  const asked = useRef(false);

  const locate = useCallback(() => {
    if (typeof window === "undefined") return;
    if (!window.isSecureContext) {
      setStatus("insecure");
      safeStorage("set", "FALLBACK");
      return;
    }
    if (!("geolocation" in navigator)) {
      setStatus("unavailable");
      safeStorage("set", "FALLBACK");
      return;
    }
    setStatus("requesting");
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const ok = await act(
          "/api/simulation/deploy",
          { latitude: approx(pos.coords.latitude), longitude: approx(pos.coords.longitude), radius_m: radius, label: "Your area (approximate)", source: "GEOLOCATION" },
          "Monitoring area centred on your location. 20 agents deployed.",
        );
        setStatus(ok ? "granted" : "unavailable");
        safeStorage("set", "GEOLOCATION");
      },
      (err) => {
        setStatus(err.code === err.PERMISSION_DENIED ? "denied" : "unavailable");
        safeStorage("set", "FALLBACK");
      },
      { enableHighAccuracy: false, timeout: 12000, maximumAge: 10 * 60 * 1000 },
    );
  }, [act, radius]);

  useEffect(() => {
    if (!snapshot || asked.current) return;
    asked.current = true;
    if (!safeStorage("get")) locate();
  }, [snapshot, locate]);

  return { status, setStatus, locate };
}

interface SearchResult {
  display_name: string;
  lat: string;
  lon: string;
}

export function LocationPanel({
  open,
  onClose,
  geoStatus,
  onLocate,
  onPickOnMap,
  picking,
  radius,
  setRadius,
}: {
  open: boolean;
  onClose: () => void;
  geoStatus: GeoStatus;
  onLocate: () => void;
  onPickOnMap: () => void;
  picking: boolean;
  radius: number;
  setRadius: (r: number) => void;
}) {
  const { act } = useSim();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [demo, setDemo] = useState<{ lat: number; lng: number; label: string } | null>(null);

  useEffect(() => {
    if (open && !demo) {
      api.get<{ demo_location: { lat: number; lng: number; label: string } }>("/api/config")
        .then((c) => setDemo(c.demo_location))
        .catch(() => undefined);
    }
  }, [open, demo]);

  if (!open) return null;

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setSearchError(null);
    try {
      // OpenStreetMap Nominatim geocoder. Only the typed text is sent - never your position.
      const res = await fetch(`https://nominatim.openstreetmap.org/search?format=jsonv2&limit=5&q=${encodeURIComponent(query.trim())}`, {
        headers: { "Accept-Language": "en" },
      });
      if (!res.ok) throw new Error();
      const data: SearchResult[] = await res.json();
      setResults(data);
      if (!data.length) setSearchError("No places found. Try a city, campus or landmark name.");
    } catch {
      setSearchError("Search is unavailable right now. Pick a point on the map or use the demo location instead.");
      setResults(null);
    } finally {
      setSearching(false);
    }
  }

  async function deploy(lat: number, lng: number, label: string, source: string) {
    const ok = await act("/api/simulation/deploy", { latitude: lat, longitude: lng, radius_m: radius, label: label.slice(0, 120), source }, `Agents redeployed around ${label.split(",")[0]}.`);
    if (ok) {
      safeStorage("set", source);
      onClose();
    }
  }

  const message = GEO_TEXT[geoStatus];
  const warn = geoStatus === "denied" || geoStatus === "unavailable" || geoStatus === "insecure";

  return (
    <div className="absolute left-14 top-14 z-[600] w-[min(360px,calc(100%-4.5rem))] rounded-lg border border-line bg-surface shadow-xl shadow-[#18344D]/15">
      <div className="flex items-center justify-between border-b border-line px-4 py-2.5 bg-header rounded-t-lg">
        <h2 className="font-cond text-[15px] font-bold text-ink">Monitoring area</h2>
        <button onClick={onClose} aria-label="Close" className="text-ink-3 hover:text-ink">
          <X size={16} />
        </button>
      </div>
      <div className="space-y-4 p-4 text-sm">
        {message && (
          <p className={warn ? "rounded-md border border-amber/40 bg-amber/10 px-3 py-2 text-amber" : "text-ink-2"} role={warn ? "alert" : undefined}>
            {message}
          </p>
        )}

        <div>
          <label htmlFor="radius" className="flex justify-between text-ink-2">
            <span className="font-medium">Operating radius</span>
            <span className="tabular-nums text-ink font-bold">{(radius / 1000).toFixed(1)} km</span>
          </label>
          <input id="radius" type="range" min={400} max={5000} step={100} value={radius} onChange={(e) => setRadius(Number(e.target.value))} className="mt-1.5 w-full accent-[#397FB8]" />
          <p className="mt-1 text-xs text-ink-3">Applies to the next deployment. 1-1.5 km keeps agents within radio range of each other.</p>
        </div>

        <form onSubmit={search} className="space-y-2">
          <label htmlFor="place" className="text-ink-2 font-medium">Search for a place</label>
          <div className="flex gap-2">
            <input
              id="place"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. VIT Vellore, Lalbagh Bengaluru"
              className="h-9 min-w-0 flex-1 rounded-md border border-line bg-input px-3 text-ink placeholder:text-ink-3 focus:border-primary focus:outline-none shadow-2xs"
            />
            <Button type="submit" disabled={searching} aria-label="Search">
              <Search size={15} />
            </Button>
          </div>
          {searchError && <p className="text-xs text-amber">{searchError}</p>}
          {results && results.length > 0 && (
            <ul className="max-h-44 divide-y divide-line overflow-y-auto rounded-md border border-line bg-surface scroll-thin">
              {results.map((r) => (
                <li key={`${r.lat}${r.lon}`}>
                  <button onClick={() => deploy(Number(r.lat), Number(r.lon), r.display_name, "SEARCH")} className="w-full px-3 py-2 text-left text-xs text-ink hover:bg-selected/40">
                    {r.display_name}
                  </button>
                </li>
              ))}
            </ul>
          )}
          <p className="text-xs text-ink-3">Search uses OpenStreetMap Nominatim; only the text you type is sent.</p>
        </form>

        <div className="grid grid-cols-1 gap-2">
          <Button onClick={onPickOnMap} variant={picking ? "primary" : "secondary"}>
            <Crosshair size={15} /> {picking ? "Click the map to choose the centre" : "Select a point on the map"}
          </Button>
          <Button onClick={onLocate} disabled={geoStatus === "requesting"}>
            <LocateFixed size={15} /> Use my current location
          </Button>
          {demo && (
            <Button variant="ghost" onClick={() => deploy(demo.lat, demo.lng, demo.label, "DEMO")}>
              <MapPin size={15} /> Use demo location ({demo.label.replace(/^Demonstration area \(|\)$/g, "")})
            </Button>
          )}
        </div>
        <p className="text-xs leading-relaxed text-slate-500">
          Your location is used only to centre the simulation, rounded to about 100 m and sent only to this app&apos;s backend. In a shared public deployment other viewers see the same area.
        </p>
      </div>
    </div>
  );
}
