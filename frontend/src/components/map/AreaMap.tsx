"use client";

import L from "leaflet";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { Circle, MapContainer, Marker, Polygon, Polyline, TileLayer, Tooltip, useMap, useMapEvents } from "react-leaflet";
import { glyphSvg } from "@/components/AgentGlyph";
import { HAZARD_COLOR, HAZARD_LABEL, STATUS_COLOR } from "@/lib/format";
import type { Agent, Incident, Link, Site, CoverageSummary } from "@/lib/types";

export type MapTypeOption = "tactical" | "roadmap" | "satellite" | "terrain" | "hybrid";

export const TILE_PROVIDERS: Record<MapTypeOption, { url: string; attribution: string; subdomains?: string; maxZoom?: number }> = {
  tactical: {
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    subdomains: "abc",
    maxZoom: 19,
  },
  roadmap: {
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    subdomains: "abc",
    maxZoom: 19,
  },
  satellite: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
    subdomains: "",
    maxZoom: 19,
  },
  terrain: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
    attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey',
    subdomains: "",
    maxZoom: 19,
  },
  hybrid: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, DigitalGlobe, GeoEye, Earthstar Geographics, CNES/Airbus DS, USDA, USGS, AeroGRID, IGN, and the GIS User Community',
    subdomains: "",
    maxZoom: 19,
  },
};

export const HYBRID_LABELS_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}";

export type PickMode = null | "incident" | "location" | "move";

export interface AreaMapProps {
  site: Site;
  agents: Agent[];
  incidents: Incident[];
  links: Link[];
  tickMs: number;
  selectedAgentId?: string | null;
  selectedIncidentId?: string | null;
  onSelectAgent?: (id: string | null) => void;
  onSelectIncident?: (id: string | null) => void;
  pickMode?: PickMode;
  onPick?: (lat: number, lng: number) => void;
  pickPreview?: { lat: number; lng: number; radius_m: number; color: string } | null;
  showLinks?: boolean;
  showTrails?: boolean;
  showRanges?: boolean;
  showLabels?: boolean;
  showCoverageZones?: boolean;
  showHazardZones?: boolean;
  coverage?: CoverageSummary;
  mapType?: MapTypeOption;
  className?: string;
}

// Icons are cached so Leaflet keeps the same DOM node between ticks; that is
// what lets the CSS transition glide markers smoothly to the next position.
const iconCache = new Map<string, L.DivIcon>();

function agentIcon(agent: Agent, selected: boolean, showLabel: boolean): L.DivIcon {
  const color = STATUS_COLOR[agent.status] ?? "#76807B";
  const failed = agent.status === "FAILED";
  const coordinator = agent.coordinator_of.length > 0;
  const key = `${agent.id}|${agent.type}|${agent.status}|${selected}|${coordinator}|${showLabel}`;
  const cached = iconCache.get(key);
  if (cached) return cached;
  const size = selected ? 18 : 14;
  const ring = selected ? "#E4E8E5" : coordinator ? "#E0A43A" : null;
  const pulse =
    agent.status === "DETECTING"
      ? `<svg width="${size}" height="${size}" style="position:absolute;left:0;top:0;overflow:visible"><circle class="pulse-ring" cx="${size / 2}" cy="${size / 2}" r="${size / 2 + 4}" fill="none" stroke="#E0A43A" stroke-width="1.5"/></svg>`
      : "";
  const label = showLabel ? `<div class="agent-label" style="position:absolute;left:${size + 5}px;top:${size / 2 - 7}px">${agent.id}</div>` : "";
  const icon = L.divIcon({
    className: "agent-icon",
    html: `<div style="position:relative;width:${size}px;height:${size}px">${pulse}${glyphSvg(agent.type, color, { failed, ring, size })}${label}</div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
  iconCache.set(key, icon);
  return icon;
}

function incidentLabelIcon(incident: Incident): L.DivIcon {
  const color = HAZARD_COLOR[incident.type];
  return L.divIcon({
    className: "",
    html: `<div style="transform:translate(-50%,-50%);display:inline-flex;align-items:center;gap:6px;white-space:nowrap;padding:2px 7px;border-radius:4px;background:rgba(16,20,22,.86);border:1px solid ${color};font:600 11px 'Barlow Semi Condensed',Barlow,sans-serif;color:#E4E8E5"><span style="width:7px;height:7px;border-radius:50%;background:${color}"></span>${incident.id} · ${HAZARD_LABEL[incident.type]} ${Math.round(incident.severity)}</div>`,
    iconSize: [0, 0],
  });
}

const estimateIcon = L.divIcon({
  className: "",
  html: `<svg width="18" height="18" viewBox="0 0 18 18" style="transform:translate(-9px,-9px)"><circle cx="9" cy="9" r="5" fill="none" stroke="#E4E8E5" stroke-width="1.4"/><path d="M9 0v5M9 13v5M0 9h5M13 9h5" stroke="#E4E8E5" stroke-width="1.4"/></svg>`,
  iconSize: [0, 0],
});

function FollowSite({ site }: { site: Site }) {
  const map = useMap();
  const key = `${site.run_id}-${site.lat}-${site.lng}-${site.radius_m}`;
  const last = useRef<string | null>(null);
  useEffect(() => {
    if (last.current === key) return;
    const first = last.current === null;
    last.current = key;
    const bounds = L.latLng(site.lat, site.lng).toBounds(site.radius_m * 2.3);
    if (first) map.fitBounds(bounds, { animate: false });
    else map.flyToBounds(bounds, { duration: 0.8 });
  }, [key, map, site.lat, site.lng, site.radius_m]);
  return null;
}

/** Stop the glide transition while zooming, otherwise markers slide after every zoom. */
function GlideControl() {
  const map = useMap();
  useEffect(() => {
    const el = map.getContainer();
    let timer: ReturnType<typeof setTimeout> | null = null;
    const off = () => {
      if (timer) clearTimeout(timer);
      el.classList.add("no-glide");
    };
    const on = () => {
      timer = setTimeout(() => el.classList.remove("no-glide"), 80);
    };
    map.on("zoomstart", off);
    map.on("zoomend", on);
    return () => {
      map.off("zoomstart", off);
      map.off("zoomend", on);
    };
  }, [map]);
  return null;
}

function MapResizer() {
  const map = useMap();
  useEffect(() => {
    const container = map.getContainer();
    if (!container) return;

    // Immediately invalidate
    map.invalidateSize();

    // Use ResizeObserver so that any container dimension changes (e.g. side panel opening/closing)
    // immediately trigger map.invalidateSize()
    const ro = new ResizeObserver(() => {
      map.invalidateSize();
    });
    ro.observe(container);

    if (container.parentElement) {
      ro.observe(container.parentElement);
    }

    const onResize = () => {
      map.invalidateSize();
    };
    window.addEventListener("resize", onResize);

    return () => {
      ro.disconnect();
      window.removeEventListener("resize", onResize);
    };
  }, [map]);

  return null;
}

function ClickHandler({ pickMode, onPick, onBackground }: { pickMode: PickMode; onPick?: (lat: number, lng: number) => void; onBackground?: () => void }) {
  useMapEvents({
    click(e) {
      if (pickMode && onPick) onPick(e.latlng.lat, e.latlng.lng);
      else onBackground?.();
    },
  });
  return null;
}

export default function AreaMap(props: AreaMapProps) {
  const {
    site, agents, incidents, links, tickMs, selectedAgentId, selectedIncidentId, onSelectAgent, onSelectIncident,
    pickMode = null, onPick, pickPreview, showLinks = false, showTrails = true, showRanges = false, showLabels = true,
    showCoverageZones = false, showHazardZones = true, coverage, mapType = "tactical",
    className,
  } = props;
  const [tilesFailed, setTilesFailed] = useState(false);
  // Counted in refs so re-renders (every tick) do not reset them
  const tileErrors = useRef(0);
  const tileLoads = useRef(0);
  const tileEvents = useMemo(
    () => ({
      tileerror: () => {
        tileErrors.current += 1;
        if (tileErrors.current >= 4 && tileLoads.current === 0) setTilesFailed(true);
      },
      tileload: () => {
        tileLoads.current += 1;
        setTilesFailed(false);
      },
    }),
    [],
  );
  const byId = useMemo(() => new Map(agents.map((a) => [a.id, a])), [agents]);
  const tileConfig = TILE_PROVIDERS[mapType] || TILE_PROVIDERS.tactical || TILE_PROVIDERS.roadmap;

  return (
    <div
      className={`relative h-full w-full ${pickMode ? "map-picking" : ""} ${tilesFailed ? "tiles-failed" : ""} map-${mapType} ${className ?? ""}`}
      style={{ ["--tick-ms" as string]: `${Math.max(150, tickMs)}ms` }}
    >
      <MapContainer
        center={[site.lat, site.lng]}
        zoom={15}
        minZoom={3}
        maxZoom={19}
        zoomControl
        className="h-full w-full"
      >
        <MapResizer />
        <TileLayer
          key={mapType}
          url={tileConfig.url}
          attribution={tileConfig.attribution}
          subdomains={tileConfig.subdomains || "abc"}
          maxZoom={tileConfig.maxZoom || 19}
          eventHandlers={tileEvents}
        />
        {mapType === "hybrid" && (
          <TileLayer
            key="hybrid-labels"
            url={HYBRID_LABELS_URL}
            attribution=""
            maxZoom={19}
            zIndex={200}
          />
        )}
        <FollowSite site={site} />
        <GlideControl />
        <ClickHandler pickMode={pickMode} onPick={onPick} onBackground={() => { onSelectAgent?.(null); }} />

        {/* Monitoring area boundary (radius covered by all drones) */}
        <Circle
          center={[site.lat, site.lng]}
          radius={site.radius_m}
          pathOptions={{
            color: "#38bdf8",
            weight: 2,
            opacity: 0.8,
            dashArray: "6 6",
            fillColor: "#38bdf8",
            fillOpacity: 0.03,
            interactive: false,
          }}
        />

        {/* Pick preview for incident creation / placement */}
        {pickPreview && (
          <Circle
            center={[pickPreview.lat, pickPreview.lng]}
            radius={pickPreview.radius_m}
            pathOptions={{
              color: pickPreview.color,
              weight: 2,
              dashArray: "5 5",
              fillColor: pickPreview.color,
              fillOpacity: 0.22,
              interactive: false,
            }}
          />
        )}

        {/* Sprinkler operating radius */}
        {showRanges &&
          agents
            .filter((a) => a.type === "SPRINKLER")
            .map((a) => (
              <Circle
                key={`range-${a.id}`}
                center={[a.lat, a.lng]}
                radius={a.operating_radius_m}
                pathOptions={{
                  color: a.status === "RESPONDING" ? "#5B9BD5" : "#4A5A63",
                  weight: 1,
                  opacity: a.status === "FAILED" ? 0.25 : 0.7,
                  dashArray: "3 4",
                  fillColor: "#5B9BD5",
                  fillOpacity: a.status === "RESPONDING" ? 0.08 : 0,
                  interactive: false,
                }}
              />
            ))}

        {/* Monitor Drones Nominal Detection Radius & Boundary Tolerance Band */}
        {showCoverageZones &&
          agents
            .filter((a) => a.type === "MONITOR_DRONE" && a.status !== "FAILED")
            .map((a) => {
              const nominalR = coverage?.nominal_radius_m ?? 450;
              const bufferR = coverage?.boundary_tolerance_m ?? 80;
              return (
                <React.Fragment key={`coverage-${a.id}`}>
                  {/* Nominal detection radius (450m) */}
                  <Circle
                    center={[a.lat, a.lng]}
                    radius={nominalR}
                    pathOptions={{
                      color: "#38bdf8",
                      weight: 1.2,
                      opacity: 0.65,
                      fillColor: "#38bdf8",
                      fillOpacity: 0.035,
                      interactive: false,
                    }}
                  />
                  {/* Boundary tolerance buffer margin (450m + 80m = 530m) */}
                  <Circle
                    center={[a.lat, a.lng]}
                    radius={nominalR + bufferR}
                    pathOptions={{
                      color: "#0284c7",
                      weight: 1,
                      opacity: 0.45,
                      dashArray: "3 6",
                      fill: false,
                      interactive: false,
                    }}
                  />
                </React.Fragment>
              );
            })}

        {/* Failed Drone Former Surveillance Area */}
        {showCoverageZones &&
          agents
            .filter((a) => a.type === "MONITOR_DRONE" && a.status === "FAILED")
            .map((a) => (
              <Circle
                key={`failed-zone-${a.id}`}
                center={[a.lat, a.lng]}
                radius={coverage?.nominal_radius_m ?? 450}
                pathOptions={{
                  color: "#ef4444",
                  weight: 2,
                  opacity: 0.85,
                  dashArray: "5 5",
                  fillColor: "#ef4444",
                  fillOpacity: 0.09,
                  interactive: true,
                }}
              >
                <Tooltip direction="top">
                  Lost surveillance area of failed drone {a.id}
                </Tooltip>
              </Circle>
            ))}

        {/* Uncovered Geographical Sectors (Blind Spots) */}
        {showCoverageZones &&
          coverage?.uncovered_areas &&
          coverage.uncovered_areas.map((sec, idx) => {
            const numPts = 12;
            const pts: [number, number][] = [[site.lat, site.lng]];
            const step = (sec.end_angle - sec.start_angle) / numPts;
            const latDegPerM = 1 / 111139;
            const lngDegPerM = 1 / (111139 * Math.cos((site.lat * Math.PI) / 180));
            for (let i = 0; i <= numPts; i++) {
              const ang = sec.start_angle + i * step;
              pts.push([
                site.lat + sec.radius_m * Math.sin(ang) * latDegPerM,
                site.lng + sec.radius_m * Math.cos(ang) * lngDegPerM,
              ]);
            }
            return (
              <Polygon
                key={`uncovered-sec-${idx}`}
                positions={pts}
                pathOptions={{
                  color: "#f97316",
                  weight: 1.5,
                  opacity: 0.8,
                  dashArray: "4 4",
                  fillColor: "#f97316",
                  fillOpacity: 0.14,
                  interactive: true,
                }}
              >
                <Tooltip direction="center">
                  Unmonitored Sector ({sec.name}) - Surveillance Blind Spot
                </Tooltip>
              </Polygon>
            );
          })}

        {/* Overlapping Coverage Highlights */}
        {showCoverageZones &&
          coverage?.overlapping_regions &&
          coverage.overlapping_regions.map((ov, idx) => (
            <Circle
              key={`overlap-${idx}`}
              center={ov.midpoint}
              radius={Math.max(30, ov.overlap_width_m / 2)}
              pathOptions={{
                color: "#a855f7",
                weight: 1.2,
                opacity: 0.75,
                fillColor: "#a855f7",
                fillOpacity: 0.18,
                interactive: true,
              }}
            >
              <Tooltip direction="top">
                Overlap: {ov.drone_a} & {ov.drone_b} ({ov.overlap_width_m}m)
              </Tooltip>
            </Circle>
          ))}

        {/* Dynamic Coverage Reassignment Links */}
        {showCoverageZones &&
          coverage?.reassignments &&
          coverage.reassignments.map((re, idx) => {
            const orig = byId.get(re.original_owner);
            const assignee = byId.get(re.assigned_to);
            if (!orig || !assignee) return null;
            return (
              <Polyline
                key={`reassign-route-${idx}`}
                positions={[[assignee.lat, assignee.lng], [orig.lat, orig.lng]]}
                pathOptions={{
                  color: "#c084fc",
                  weight: 2,
                  opacity: 0.85,
                  dashArray: "4 5",
                  interactive: true,
                }}
              >
                <Tooltip direction="top">
                  Reassigned Patrol: {re.assigned_to} covering {re.sector_name}
                </Tooltip>
              </Polyline>
            );
          })}

        {/* Hazard zones (simulated ground truth) */}
        {showHazardZones &&
          incidents
            .filter((i) => i.physical && !["RESOLVED", "REJECTED"].includes(i.status))
            .map((i) => {
            const color = HAZARD_COLOR[i.type];
            const selected = i.id === selectedIncidentId;
            return (
              <Circle
                key={`zone-${i.id}`}
                center={[i.lat, i.lng]}
                radius={i.radius_m}
                eventHandlers={{ click: (e) => { L.DomEvent.stopPropagation(e); onSelectIncident?.(i.id); } }}
                pathOptions={{
                  color,
                  weight: selected ? 2.5 : 1.5,
                  opacity: 0.9,
                  dashArray: i.status === "UNDETECTED" ? "6 6" : undefined,
                  fillColor: color,
                  fillOpacity: 0.06 + (i.severity / 100) * 0.26,
                }}
              />
            );
          })}

        {/* Communication links */}
        {showLinks &&
          links.map((l) => {
            const a = byId.get(l.source);
            const b = byId.get(l.target);
            if (!a || !b) return null;
            return (
              <Polyline
                key={`${l.source}-${l.target}`}
                positions={[[a.lat, a.lng], [b.lat, b.lng]]}
                pathOptions={{
                  color: l.kind === "relay" ? "#E0A43A" : "#6E9CC4",
                  weight: l.kind === "relay" ? 1.5 : 1,
                  opacity: l.kind === "relay" ? 0.8 : 0.35,
                  dashArray: l.kind === "relay" ? "5 5" : undefined,
                  interactive: false,
                }}
              />
            );
          })}

        {/* Movement trails */}
        {showTrails &&
          agents
            .filter((a) => a.mobile && a.trail.length > 1 && a.status !== "FAILED")
            .map((a) => (
              <Polyline
                key={`trail-${a.id}`}
                positions={[...a.trail, [a.lat, a.lng]] as [number, number][]}
                pathOptions={{ color: STATUS_COLOR[a.status] ?? "#76807B", weight: 1.5, opacity: 0.35, interactive: false }}
              />
            ))}

        {/* Where tasked agents are heading */}
        {agents
          .filter((a) => a.task_id && a.destination && a.mobile)
          .map((a) => (
            <Polyline
              key={`dest-${a.id}`}
              positions={[[a.lat, a.lng], a.destination as [number, number]]}
              pathOptions={{ color: "#A98BE0", weight: 1.5, opacity: 0.8, dashArray: "2 5", interactive: false }}
            />
          ))}

        {/* Incident labels and the agents' estimated position */}
        {incidents
          .filter((i) => !["RESOLVED", "REJECTED"].includes(i.status))
          .map((i) => (
            <Marker
              key={`label-${i.id}`}
              position={[i.lat, i.lng]}
              icon={incidentLabelIcon(i)}
              eventHandlers={{ click: () => onSelectIncident?.(i.id) }}
              zIndexOffset={-500}
            />
          ))}
        {incidents
          .filter((i) => i.estimated_location && !["RESOLVED", "REJECTED", "UNDETECTED"].includes(i.status))
          .map((i) => (
            <Marker key={`est-${i.id}`} position={i.estimated_location as [number, number]} icon={estimateIcon} interactive>
              <Tooltip direction="top" offset={[0, -8]}>
                Agents&apos; estimate of {i.id}
                {i.estimate_error_m !== null ? ` (${i.estimate_error_m} m from the true centre)` : ""}
              </Tooltip>
            </Marker>
          ))}

        {pickPreview && (
          <Circle
            center={[pickPreview.lat, pickPreview.lng]}
            radius={pickPreview.radius_m}
            pathOptions={{ color: pickPreview.color, weight: 1.5, dashArray: "4 4", fillOpacity: 0.08, interactive: false }}
          />
        )}

        {/* Agents */}
        {agents.map((a) => (
          <Marker
            key={a.id}
            position={[a.lat, a.lng]}
            icon={agentIcon(a, a.id === selectedAgentId, showLabels)}
            zIndexOffset={a.id === selectedAgentId ? 1000 : a.status === "FAILED" ? -100 : 0}
            eventHandlers={{ click: () => onSelectAgent?.(a.id) }}
            keyboard
            title={`${a.id} - ${a.type_label} - ${a.status}`}
          />
        ))}
      </MapContainer>

      {tilesFailed && (
        <div className="pointer-events-none absolute left-1/2 top-3 z-[500] -translate-x-1/2 rounded-md border border-[#5a4a29] bg-[#2a2418]/95 px-3 py-1.5 text-xs text-[#ecd29b]">
          Map tiles could not load (offline?). Agent positions and distances are still accurate.
        </div>
      )}
    </div>
  );
}
