"use client";

import React, { useEffect, useRef, useState } from "react";
import { glyphSvg } from "@/components/AgentGlyph";
import { HAZARD_COLOR, STATUS_COLOR } from "@/lib/format";
import type { Agent, Incident, Link, Site, CoverageSummary } from "@/lib/types";

export type GoogleMapType = "roadmap" | "satellite" | "terrain" | "hybrid" | "tactical";

export interface GoogleAreaMapProps {
  site: Site;
  agents: Agent[];
  incidents: Incident[];
  links: Link[];
  tickMs: number;
  selectedAgentId?: string | null;
  selectedIncidentId?: string | null;
  onSelectAgent?: (id: string | null) => void;
  onSelectIncident?: (id: string | null) => void;
  pickMode?: "incident" | "location" | "move" | null;
  onPick?: (lat: number, lng: number) => void;
  pickPreview?: { lat: number; lng: number; radius_m: number; color: string } | null;
  showLinks?: boolean;
  showTrails?: boolean;
  showRanges?: boolean;
  showLabels?: boolean;
  showCoverageZones?: boolean;
  showHazardZones?: boolean;
  coverage?: CoverageSummary;
  mapType: GoogleMapType;
  onMapTypeChange?: (type: GoogleMapType) => void;
  className?: string;
}

export function GoogleAreaMap({
  site,
  agents,
  incidents,
  links,
  selectedAgentId,
  selectedIncidentId,
  onSelectAgent,
  onSelectIncident,
  pickMode,
  onPick,
  pickPreview,
  showLinks = false,
  showTrails = true,
  showRanges = false,
  showCoverageZones = false,
  showHazardZones = true,
  coverage,
  mapType,
  className,
}: GoogleAreaMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<google.maps.Map | null>(null);
  const [loaded, setLoaded] = useState(false);

  // Overlay references to update rather than recreate
  const markersRef = useRef<Map<string, google.maps.Marker>>(new Map());
  const linkLinesRef = useRef<google.maps.Polyline[]>([]);
  const incidentCirclesRef = useRef<Map<string, google.maps.Circle>>(new Map());
  const siteCircleRef = useRef<google.maps.Circle | null>(null);
  const coverageCirclesRef = useRef<google.maps.Circle[]>([]);
  const coveragePolygonsRef = useRef<google.maps.Polygon[]>([]);
  const reassignmentLinesRef = useRef<google.maps.Polyline[]>([]);

  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

  // 1. Load Google Maps Script
  useEffect(() => {
    if (!apiKey) return;
    if (typeof window === "undefined") return;

    if (window.google?.maps) {
      setLoaded(true);
      return;
    }

    const scriptId = "google-maps-js-sdk";
    let script = document.getElementById(scriptId) as HTMLScriptElement | null;
    if (!script) {
      script = document.createElement("script");
      script.id = scriptId;
      script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=geometry`;
      script.async = true;
      script.defer = true;
      script.onload = () => setLoaded(true);
      document.head.appendChild(script);
    } else {
      script.addEventListener("load", () => setLoaded(true));
    }
  }, [apiKey]);

  // 2. Initialize Map once
  useEffect(() => {
    if (!loaded || !containerRef.current || mapRef.current || !window.google?.maps) return;

    const map = new google.maps.Map(containerRef.current, {
      center: { lat: site.lat, lng: site.lng },
      zoom: 15,
      mapTypeId: mapType === "tactical" ? "roadmap" : mapType,
      disableDefaultUI: true,
      zoomControl: true,
      rotateControl: false,
      mapTypeControl: false,
      scaleControl: true,
      streetViewControl: false,
      backgroundColor: "#DCEAF5",
    });

    map.addListener("click", (e: google.maps.MapMouseEvent) => {
      if (e.latLng && onPick) {
        onPick(e.latLng.lat(), e.latLng.lng());
      } else {
        onSelectAgent?.(null);
        onSelectIncident?.(null);
      }
    });

    mapRef.current = map;
  }, [loaded, site.lat, site.lng, mapType, onPick, onSelectAgent, onSelectIncident]);

  // Handle container resize when side panel toggles
  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver(() => {
      if (mapRef.current && window.google?.maps) {
        google.maps.event.trigger(mapRef.current, "resize");
      }
    });
    ro.observe(containerRef.current);
    if (containerRef.current.parentElement) {
      ro.observe(containerRef.current.parentElement);
    }
    return () => ro.disconnect();
  }, [loaded]);

  // 3. Handle mapType changes seamlessly without reloading
  useEffect(() => {
    if (mapRef.current && window.google?.maps) {
      mapRef.current.setMapTypeId(mapType === "tactical" ? "roadmap" : mapType);
    }
  }, [mapType]);

  // 4. Update Site Boundary Circle
  useEffect(() => {
    if (!mapRef.current || !window.google?.maps) return;
    const map = mapRef.current;

    if (!siteCircleRef.current) {
      siteCircleRef.current = new google.maps.Circle({
        strokeColor: "#38bdf8",
        strokeOpacity: 0.8,
        strokeWeight: 2,
        fillColor: "#38bdf8",
        fillOpacity: 0.02,
        map,
        center: { lat: site.lat, lng: site.lng },
        radius: site.radius_m,
      });
    } else {
      siteCircleRef.current.setCenter({ lat: site.lat, lng: site.lng });
      siteCircleRef.current.setRadius(site.radius_m);
    }
  }, [site.lat, site.lng, site.radius_m, loaded]);

  // 5. Update Hazard Zones
  useEffect(() => {
    if (!mapRef.current || !window.google?.maps) return;
    const map = mapRef.current;
    const existing = incidentCirclesRef.current;
    const currentIds = new Set<string>();

    incidents
      .filter((i) => i.physical && !["RESOLVED", "REJECTED"].includes(i.status))
      .forEach((inc) => {
        currentIds.add(inc.id);
        const color = HAZARD_COLOR[inc.type] || "#ef4444";
        const selected = inc.id === selectedIncidentId;
        const opacity = 0.08 + (inc.severity / 100) * 0.28;

        let circle = existing.get(inc.id);
        if (!circle) {
          circle = new google.maps.Circle({
            map,
            center: { lat: inc.lat, lng: inc.lng },
            radius: inc.radius_m,
            strokeColor: color,
            strokeOpacity: 0.9,
            strokeWeight: selected ? 3 : 1.5,
            fillColor: color,
            fillOpacity: opacity,
          });
          circle.addListener("click", () => onSelectIncident?.(inc.id));
          existing.set(inc.id, circle);
        } else {
          circle.setCenter({ lat: inc.lat, lng: inc.lng });
          circle.setRadius(inc.radius_m);
          circle.setOptions({
            strokeColor: color,
            strokeWeight: selected ? 3 : 1.5,
            fillColor: color,
            fillOpacity: opacity,
          });
        }
      });

    // Remove deleted incidents
    for (const [id, circle] of existing.entries()) {
      if (!currentIds.has(id)) {
        circle.setMap(null);
        existing.delete(id);
      }
    }
  }, [incidents, selectedIncidentId, loaded, onSelectIncident]);

  // 6. Update Radio Links
  useEffect(() => {
    if (!mapRef.current || !window.google?.maps || !showLinks) {
      linkLinesRef.current.forEach((l) => l.setMap(null));
      linkLinesRef.current = [];
      return;
    }
    const map = mapRef.current;
    linkLinesRef.current.forEach((l) => l.setMap(null));
    linkLinesRef.current = [];

    const byId = new Map(agents.map((a) => [a.id, a]));
    links.forEach((link) => {
      const a = byId.get(link.source);
      const b = byId.get(link.target);
      if (!a || !b) return;

      const isRelay = link.kind === "relay";
      const line = new google.maps.Polyline({
        path: [
          { lat: a.lat, lng: a.lng },
          { lat: b.lat, lng: b.lng },
        ],
        strokeColor: isRelay ? "#E0A43A" : "#6E9CC4",
        strokeOpacity: isRelay ? 0.85 : 0.4,
        strokeWeight: isRelay ? 2 : 1,
        map,
      });
      linkLinesRef.current.push(line);
    });
  }, [links, agents, showLinks, loaded]);

  // 7. Update Coverage Zones (Nominal, Tolerance Buffer, Uncovered, Reassignments)
  useEffect(() => {
    if (!mapRef.current || !window.google?.maps || !showCoverageZones) {
      coverageCirclesRef.current.forEach((c) => c.setMap(null));
      coverageCirclesRef.current = [];
      coveragePolygonsRef.current.forEach((p) => p.setMap(null));
      coveragePolygonsRef.current = [];
      reassignmentLinesRef.current.forEach((l) => l.setMap(null));
      reassignmentLinesRef.current = [];
      return;
    }
    const map = mapRef.current;
    coverageCirclesRef.current.forEach((c) => c.setMap(null));
    coverageCirclesRef.current = [];
    coveragePolygonsRef.current.forEach((p) => p.setMap(null));
    coveragePolygonsRef.current = [];
    reassignmentLinesRef.current.forEach((l) => l.setMap(null));
    reassignmentLinesRef.current = [];

    const nominalR = coverage?.nominal_radius_m ?? 450;
    const bufferR = coverage?.boundary_tolerance_m ?? 80;
    const effectiveR = nominalR + bufferR;

    // Active Monitor Drones: Nominal & Tolerance Zones
    agents
      .filter((a) => a.type === "MONITOR_DRONE" && a.status !== "FAILED")
      .forEach((drone) => {
        // Nominal radius circle
        const nomCircle = new google.maps.Circle({
          center: { lat: drone.lat, lng: drone.lng },
          radius: nominalR,
          strokeColor: "#38bdf8",
          strokeOpacity: 0.65,
          strokeWeight: 1.2,
          fillColor: "#38bdf8",
          fillOpacity: 0.04,
          map,
        });
        coverageCirclesRef.current.push(nomCircle);

        // Boundary tolerance circle
        const tolCircle = new google.maps.Circle({
          center: { lat: drone.lat, lng: drone.lng },
          radius: effectiveR,
          strokeColor: "#0284c7",
          strokeOpacity: 0.45,
          strokeWeight: 1,
          fillOpacity: 0,
          map,
        });
        coverageCirclesRef.current.push(tolCircle);
      });

    // Failed Drones Former Surveillance Area
    agents
      .filter((a) => a.type === "MONITOR_DRONE" && a.status === "FAILED")
      .forEach((drone) => {
        const failCircle = new google.maps.Circle({
          center: { lat: drone.lat, lng: drone.lng },
          radius: nominalR,
          strokeColor: "#ef4444",
          strokeOpacity: 0.85,
          strokeWeight: 2,
          fillColor: "#ef4444",
          fillOpacity: 0.1,
          map,
        });
        coverageCirclesRef.current.push(failCircle);
      });

    // Uncovered Sectors (Blind Spots)
    if (coverage?.uncovered_areas) {
      coverage.uncovered_areas.forEach((sec) => {
        const numPts = 12;
        const pts: google.maps.LatLngLiteral[] = [{ lat: site.lat, lng: site.lng }];
        const step = (sec.end_angle - sec.start_angle) / numPts;
        const latDegPerM = 1 / 111139;
        const lngDegPerM = 1 / (111139 * Math.cos((site.lat * Math.PI) / 180));

        for (let i = 0; i <= numPts; i++) {
          const ang = sec.start_angle + i * step;
          pts.push({
            lat: site.lat + sec.radius_m * Math.sin(ang) * latDegPerM,
            lng: site.lng + sec.radius_m * Math.cos(ang) * lngDegPerM,
          });
        }

        const poly = new google.maps.Polygon({
          paths: pts,
          strokeColor: "#f97316",
          strokeOpacity: 0.8,
          strokeWeight: 1.5,
          fillColor: "#f97316",
          fillOpacity: 0.14,
          map,
        });
        coveragePolygonsRef.current.push(poly);
      });
    }

    // Dynamic Reassignment Lines
    if (coverage?.reassignments) {
      const byId = new Map(agents.map((a) => [a.id, a]));
      coverage.reassignments.forEach((re) => {
        const orig = byId.get(re.original_owner);
        const assignee = byId.get(re.assigned_to);
        if (!orig || !assignee) return;

        const line = new google.maps.Polyline({
          path: [
            { lat: assignee.lat, lng: assignee.lng },
            { lat: orig.lat, lng: orig.lng },
          ],
          strokeColor: "#c084fc",
          strokeOpacity: 0.85,
          strokeWeight: 2,
          map,
        });
        reassignmentLinesRef.current.push(line);
      });
    }
  }, [agents, site.lat, site.lng, coverage, showCoverageZones, loaded]);

  // 8. Update Drone Markers
  useEffect(() => {
    if (!mapRef.current || !window.google?.maps) return;
    const map = mapRef.current;
    const existing = markersRef.current;
    const currentIds = new Set<string>();

    agents.forEach((agent) => {
      currentIds.add(agent.id);
      const isSelected = agent.id === selectedAgentId;
      const isFailed = agent.status === "FAILED";
      const color = STATUS_COLOR[agent.status] ?? "#76807B";
      const size = isSelected ? 22 : 18;

      const svgString = glyphSvg(agent.type, color, {
        failed: isFailed,
        ring: isSelected ? "#E4E8E5" : null,
        size,
      });

      const iconUrl = `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(
        `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">${svgString}</svg>`
      )}`;

      let marker = existing.get(agent.id);
      if (!marker) {
        marker = new google.maps.Marker({
          position: { lat: agent.lat, lng: agent.lng },
          map,
          title: `${agent.id} (${agent.type_label})`,
          icon: {
            url: iconUrl,
            scaledSize: new google.maps.Size(size, size),
            anchor: new google.maps.Point(size / 2, size / 2),
          },
        });
        marker.addListener("click", () => onSelectAgent?.(agent.id));
        existing.set(agent.id, marker);
      } else {
        marker.setPosition({ lat: agent.lat, lng: agent.lng });
        marker.setIcon({
          url: iconUrl,
          scaledSize: new google.maps.Size(size, size),
          anchor: new google.maps.Point(size / 2, size / 2),
        });
      }
    });

    for (const [id, marker] of existing.entries()) {
      if (!currentIds.has(id)) {
        marker.setMap(null);
        existing.delete(id);
      }
    }
  }, [agents, selectedAgentId, loaded, onSelectAgent]);

  if (!apiKey) {
    return (
      <div className="flex h-full w-full items-center justify-center p-6 text-center text-ink-3">
        Google Maps API key not found in environment variables.
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`h-full w-full bg-[#101416] ${className ?? ""}`}
    />
  );
}
