"use client";

import React, { useEffect, useRef, useState } from "react";
import { Agent, AgentDeployment, Incident } from "@/lib/types";
import { api } from "@/lib/api";
import {
  Compass,
  Layers,
  Maximize2,
  Play,
  RotateCcw,
  Shield,
  ShieldAlert,
  Flame,
  Wind,
  Thermometer,
  Cpu,
  PowerOff,
  CheckCircle2,
  X,
  AlertTriangle,
  Info,
  Activity,
  Radio,
  Sliders,
  Battery,
  LocateFixed,
  MapPin
} from "lucide-react";

interface Props {
  agents: Agent[];
  lastEvent?: Incident | null;
  onSelectAgent?: (agent: Agent) => void;
  selectedAgentId?: string | null;
  onRefresh?: () => void;
}

// Deterministic simulation transect coordinates: Cascade Biosphere Reserve Transect
const BASE_LAT = 45.3820;
const BASE_LNG = -121.7530;
const LAT_STEP = 0.0065;
const LNG_STEP = 0.0090;
const DEFAULT_PATROL_RADIUS_KM = 3;

interface PatrolCenter {
  latitude: number;
  longitude: number;
  label: string;
}

export const getAgentCoordinates = (agent: Agent): [number, number] => {
  if (agent.latitude != null && agent.longitude != null) {
    return [agent.latitude, agent.longitude];
  }
  const x = agent.position ? agent.position[0] : 10;
  const y = agent.position ? agent.position[1] : 10;
  const lat = Math.round((BASE_LAT + (y - 10) * LAT_STEP) * 1000000) / 1000000;
  const lng = Math.round((BASE_LNG + (x - 10) * LNG_STEP) * 1000000) / 1000000;
  return [lat, lng];
};

export const getEventCoordinates = (evt: Incident): [number, number] => {
  if (evt.latitude != null && evt.longitude != null) {
    return [evt.latitude, evt.longitude];
  }
  const x = evt.location?.x ?? 10;
  const y = evt.location?.y ?? 10;
  const lat = Math.round((BASE_LAT + (y - 10) * LAT_STEP) * 1000000) / 1000000;
  const lng = Math.round((BASE_LNG + (x - 10) * LNG_STEP) * 1000000) / 1000000;
  return [lat, lng];
};

const getDronePatrolCoordinates = (
  index: number,
  droneCount: number,
  center: PatrolCenter,
  radiusKm: number,
  elapsedSeconds: number
): [number, number] => {
  const orbitFraction = 0.45 + (index % 3) * 0.15;
  const orbitRadiusMeters = radiusKm * 1000 * orbitFraction;
  const angle = (index / Math.max(droneCount, 1)) * Math.PI * 2 + elapsedSeconds * 0.45;
  const latitudeOffset = (Math.sin(angle) * orbitRadiusMeters) / 111320;
  const longitudeScale = Math.max(Math.cos((center.latitude * Math.PI) / 180), 0.01);
  const longitudeOffset =
    (Math.cos(angle) * orbitRadiusMeters) / (111320 * longitudeScale);

  return [
    center.latitude + latitudeOffset,
    center.longitude + longitudeOffset,
  ];
};

export default function LiveMonitoringMap({
  agents,
  lastEvent,
  onSelectAgent,
  selectedAgentId,
  onRefresh,
}: Props) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const leafletRef = useRef<any>(null);

  // Layer groups refs
  const zonesLayerRef = useRef<any>(null);
  const linksLayerRef = useRef<any>(null);
  const incidentsLayerRef = useRef<any>(null);
  const agentsLayerRef = useRef<any>(null);
  const patrolAreaLayerRef = useRef<any>(null);
  const selectingLocationRef = useRef(false);

  // Layer toggles
  const [showAgents, setShowAgents] = useState(true);
  const [showLinks, setShowLinks] = useState(true);
  const [showIncidents, setShowIncidents] = useState(true);
  const [showZones, setShowZones] = useState(true);

  // States
  const [isPatrolling, setIsPatrolling] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [feedbackNotice, setFeedbackNotice] = useState<string>("");
  const [tileError, setTileError] = useState(false);
  const [isMapReady, setIsMapReady] = useState(false);
  const [patrolCenter, setPatrolCenter] = useState<PatrolCenter>({
    latitude: BASE_LAT,
    longitude: BASE_LNG,
    label: "Demo transect",
  });
  const [deployedSite, setDeployedSite] = useState<AgentDeployment | null>(null);
  const [patrolRadiusKm, setPatrolRadiusKm] = useState(DEFAULT_PATROL_RADIUS_KM);
  const [isSelectingLocation, setIsSelectingLocation] = useState(false);
  const [patrolElapsedSeconds, setPatrolElapsedSeconds] = useState(0);
  const [locationError, setLocationError] = useState("");

  // Patrol loop
  useEffect(() => {
    if (!isPatrolling) return;
    const interval = setInterval(async () => {
      try {
        await api.stepPatrol();
        if (onRefresh) onRefresh();
      } catch (err) {
        console.error("Patrol step error:", err);
        setFeedbackNotice("Could not advance the simulation patrol. Check the API connection.");
      }
    }, 2400);
    return () => clearInterval(interval);
  }, [isPatrolling, onRefresh]);

  useEffect(() => {
    if (!isPatrolling) return;
    const interval = setInterval(() => {
      setPatrolElapsedSeconds((elapsed) => elapsed + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [isPatrolling]);

  const activeDrones = React.useMemo(
    () =>
      agents.filter(
        (agent) =>
          agent.status === "ACTIVE" && /drone/i.test(agent.agent_type || "")
      ),
    [agents]
  );
  const droneCoordinates = React.useMemo(
    () =>
      new Map(
        isPatrolling
          ? activeDrones.map((agent, index) => [
              agent.id,
              getDronePatrolCoordinates(
                index,
                activeDrones.length,
                patrolCenter,
                patrolRadiusKm,
                patrolElapsedSeconds
              ),
            ])
          : []
      ),
    [
      activeDrones,
      patrolCenter,
      patrolRadiusKm,
      isPatrolling,
      patrolElapsedSeconds,
    ]
  );
  const getRenderedAgentCoordinates = React.useCallback(
    (agent: Agent): [number, number] =>
      droneCoordinates.get(agent.id) || getAgentCoordinates(agent),
    [droneCoordinates]
  );

  // Initialize Leaflet Map
  useEffect(() => {
    let isMounted = true;

    async function initMap() {
      if (typeof window === "undefined" || !mapContainerRef.current) return;
      if (mapInstanceRef.current) return;

      try {
        const L = await import("leaflet");
        leafletRef.current = L;

        // Fix default icons
        delete (L.Icon.Default.prototype as any)._getIconUrl;

        const map = L.map(mapContainerRef.current, {
          center: [BASE_LAT, BASE_LNG],
          zoom: 13,
          zoomControl: false,
          attributionControl: false,
        });

        // Add Zoom Control to top-right
        L.control.zoom({ position: "topright" }).addTo(map);
        L.control.attribution({ position: "bottomleft" }).addTo(map);

        // Use Esri's public street map tiles; the previous Carto endpoint now requires an API key.
        const tileLayer = L.tileLayer(
          "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
          {
            maxZoom: 18,
            attribution:
              "Tiles &copy; Esri — Sources: Esri, TomTom, Garmin, FAO, NOAA, USGS, and the GIS User Community",
          }
        );

        tileLayer.on("tileerror", () => {
          if (isMounted) setTileError(true);
        });

        tileLayer.addTo(map);

        // Create dedicated Layer Groups
        zonesLayerRef.current = L.layerGroup().addTo(map);
        linksLayerRef.current = L.layerGroup().addTo(map);
        incidentsLayerRef.current = L.layerGroup().addTo(map);
        agentsLayerRef.current = L.layerGroup().addTo(map);
        patrolAreaLayerRef.current = L.layerGroup().addTo(map);

        map.on("click", (event: { latlng: { lat: number; lng: number } }) => {
          if (!selectingLocationRef.current) return;
          const center = {
            latitude: event.latlng.lat,
            longitude: event.latlng.lng,
            label: "Selected map location",
          };
          setPatrolCenter(center);
          setLocationError("");
          setPatrolElapsedSeconds(0);
          setIsPatrolling(false);
          selectingLocationRef.current = false;
          setIsSelectingLocation(false);
          map.setView([center.latitude, center.longitude], Math.max(map.getZoom(), 13));
        });

        mapInstanceRef.current = map;
        if (isMounted) setIsMapReady(true);
      } catch (err) {
        console.error("Leaflet initialization failed:", err);
        if (isMounted) setTileError(true);
      }
    }

    initMap();

    return () => {
      isMounted = false;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!isMapReady) return;
    api
      .getAgentDeployment()
      .then((deployment) => {
        if (!deployment) return;
        setPatrolCenter({
          latitude: deployment.latitude,
          longitude: deployment.longitude,
          label: deployment.area_label,
        });
        setDeployedSite(deployment);
        setPatrolRadiusKm(deployment.radius_km);
        mapInstanceRef.current?.setView(
          [deployment.latitude, deployment.longitude],
          Math.max(mapInstanceRef.current.getZoom(), 13)
        );
      })
      .catch((error) => {
        console.error("Failed to load saved agent deployment:", error);
        setLocationError("Could not load the saved deployment location from the API.");
      });
  }, [isMapReady]);

  useEffect(() => {
    if (!mapInstanceRef.current || !leafletRef.current || !patrolAreaLayerRef.current) return;
    const L = leafletRef.current;
    const layer = patrolAreaLayerRef.current;
    layer.clearLayers();

    const center: [number, number] = [patrolCenter.latitude, patrolCenter.longitude];
    const circle = L.circle(center, {
      radius: patrolRadiusKm * 1000,
      color: "#456B57",
      weight: 2,
      dashArray: "7, 7",
      fillColor: "#C7F36B",
      fillOpacity: 0.12,
      interactive: false,
    });
    layer.addLayer(circle);
    mapInstanceRef.current.fitBounds(circle.getBounds(), {
      padding: [48, 48],
      maxZoom: 13,
    });

    const centerIcon = L.divIcon({
      className: "patrol-center-marker",
      html: `<div style="width:24px;height:24px;margin-left:-12px;margin-top:-12px;border:2px solid white;border-radius:50%;background:#193B32;box-shadow:0 0 0 3px #C7F36B;display:flex;align-items:center;justify-content:center;color:white;font-size:12px;">◎</div>`,
    });
    layer.addLayer(L.marker(center, { icon: centerIcon, interactive: false }));
  }, [patrolCenter, patrolRadiusKm, isMapReady]);

  // Update Ecological Sectors Layer
  useEffect(() => {
    if (!mapInstanceRef.current || !leafletRef.current || !zonesLayerRef.current) return;
    const L = leafletRef.current;
    const layer = zonesLayerRef.current;
    layer.clearLayers();

    if (!showZones) return;

    // 4 Transect Zones with scientific naming
    const sectors = [
      {
        name: "North Ridge Transect",
        bounds: [
          [BASE_LAT + 4 * LAT_STEP, BASE_LNG - 10 * LNG_STEP],
          [BASE_LAT + 10 * LAT_STEP, BASE_LNG + 10 * LNG_STEP],
        ],
        type: "Canopy & Montane Sector",
      },
      {
        name: "Central Riparian River Basin",
        bounds: [
          [BASE_LAT - 4 * LAT_STEP, BASE_LNG - 4 * LNG_STEP],
          [BASE_LAT + 4 * LAT_STEP, BASE_LNG + 4 * LNG_STEP],
        ],
        type: "Core Watershed Basin",
      },
      {
        name: "South Lowland Scrub",
        bounds: [
          [BASE_LAT - 10 * LAT_STEP, BASE_LNG - 10 * LNG_STEP],
          [BASE_LAT - 4 * LAT_STEP, BASE_LNG + 10 * LNG_STEP],
        ],
        type: "Dry Sub-Canopy Edge",
      },
      {
        name: "West Wetland Ecological Sanctuary",
        bounds: [
          [BASE_LAT - 4 * LAT_STEP, BASE_LNG - 10 * LNG_STEP],
          [BASE_LAT + 4 * LAT_STEP, BASE_LNG - 4 * LNG_STEP],
        ],
        type: "Hydrological Marshland",
      },
    ];

    sectors.forEach((sec) => {
      const rect = L.rectangle(sec.bounds as any, {
        color: "#456B57",
        weight: 1,
        dashArray: "4, 6",
        fillColor: "#DCE5D8",
        fillOpacity: 0.12,
      });

      rect.bindTooltip(
        `<div style="font-family: var(--font-sans); font-size: 10px; color: #193B32; font-weight: 600;">
          <span style="font-size: 8px; text-transform: uppercase; color: #69786D; letter-spacing: 0.05em; display: block;">ZONE SECTOR</span>
          ${sec.name}
          <div style="font-size: 9px; color: #456B57; font-weight: normal;">${sec.type}</div>
        </div>`,
        { permanent: false, direction: "center", className: "editorial-leaflet-tooltip" }
      );

      layer.addLayer(rect);
    });
  }, [showZones, isMapReady]);

  // Update Communication Links Layer
  useEffect(() => {
    if (!mapInstanceRef.current || !leafletRef.current || !linksLayerRef.current) return;
    const L = leafletRef.current;
    const layer = linksLayerRef.current;
    layer.clearLayers();

    if (!showLinks || agents.length === 0) return;

    const agentCoordsMap = new Map<string, [number, number]>();
    agents.forEach((a) => {
      agentCoordsMap.set(a.id, getRenderedAgentCoordinates(a));
    });

    const renderedPairs = new Set<string>();

    agents.forEach((agent) => {
      if (agent.status === "FAILED" || droneCoordinates.has(agent.id)) return;
      const origin = agentCoordsMap.get(agent.id);
      if (!origin) return;

      const isSelected = selectedAgentId === agent.id;

      (agent.neighbors || []).forEach((nId) => {
        const dest = agentCoordsMap.get(nId);
        if (!dest) return;

        const neighborObj = agents.find((a) => a.id === nId);
        if (
          neighborObj &&
          (neighborObj.status === "FAILED" || droneCoordinates.has(neighborObj.id))
        ) return;

        const pairKey = [agent.id, nId].sort().join("-");
        if (renderedPairs.has(pairKey)) return;
        renderedPairs.add(pairKey);

        const isHighlighted = isSelected || selectedAgentId === nId;

        const line = L.polyline([origin, dest], {
          color: isHighlighted ? "#193B32" : "#69786D",
          weight: isHighlighted ? 2.5 : 1.2,
          opacity: isHighlighted ? 0.9 : 0.45,
          dashArray: isHighlighted ? undefined : "4, 6",
        });

        layer.addLayer(line);
      });
    });
  }, [
    agents,
    showLinks,
    selectedAgentId,
    isMapReady,
    getRenderedAgentCoordinates,
    droneCoordinates,
  ]);

  // Update Environmental Hazards / Incidents Layer
  useEffect(() => {
    if (!mapInstanceRef.current || !leafletRef.current || !incidentsLayerRef.current) return;
    const L = leafletRef.current;
    const layer = incidentsLayerRef.current;
    layer.clearLayers();

    if (!showIncidents || !lastEvent || lastEvent.status !== "ACTIVE") return;

    const [lat, lng] = getEventCoordinates(lastEvent);
    const radiusMeters = lastEvent.geo_radius_meters || (lastEvent.radius || 3) * 650;

    // Outer hazard zone circle
    const circle = L.circle([lat, lng], {
      radius: radiusMeters,
      color: "#C95B48",
      weight: 1.5,
      dashArray: "6, 6",
      fillColor: "#C95B48",
      fillOpacity: 0.14,
    });

    circle.bindTooltip(
      `<div style="font-family: var(--font-sans); font-size: 11px; padding: 2px;">
        <span style="color: #C95B48; font-weight: bold; font-family: var(--font-mono);">${lastEvent.event_type}</span>
        <div style="font-size: 9px; color: #69786D;">Consensus: ${lastEvent.consensus_state} (${Math.round(lastEvent.confidence * 100)}%)</div>
      </div>`,
      { permanent: false, direction: "top" }
    );

    layer.addLayer(circle);

    // Center icon marker
    const centerIcon = L.divIcon({
      className: "incident-center-marker",
      html: `
        <div style="
          width: 32px;
          height: 32px;
          margin-left: -16px;
          margin-top: -16px;
          border-radius: 50%;
          background: #C95B48;
          border: 2px solid #FFFFFF;
          box-shadow: 0 0 16px rgba(201, 91, 72, 0.6);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          font-size: 14px;
        ">
          ⚡
        </div>
      `,
    });

    const marker = L.marker([lat, lng], { icon: centerIcon });
    layer.addLayer(marker);
  }, [lastEvent, showIncidents, isMapReady]);

  // Update Autonomous Agents Markers Layer
  useEffect(() => {
    if (!mapInstanceRef.current || !leafletRef.current || !agentsLayerRef.current) return;
    const L = leafletRef.current;
    const layer = agentsLayerRef.current;
    layer.clearLayers();

    if (!showAgents || agents.length === 0) return;

    agents.forEach((agent) => {
      const [lat, lng] = getRenderedAgentCoordinates(agent);
      const isSelected = selectedAgentId === agent.id;
      const isFailed = agent.status === "FAILED";
      const isPatrollingDrone = droneCoordinates.has(agent.id);
      const hasAnomaly =
        agent.ai_result && agent.ai_result.status === "ANOMALY";
      const isWarning =
        !hasAnomaly &&
        (agent.battery < 30 ||
          agent.readings?.temperature > 35 ||
          agent.readings?.smoke > 0.25 ||
          agent.readings?.co2 > 650);

      // Determine visual marker style
      let borderColor = "#193B32";
      let bgColor = "#FFFFFF";
      let dotColor = "#456B57";
      let statusTag = isPatrollingDrone && isPatrolling ? "PATROLLING" : "HEALTHY";

      if (isFailed) {
        borderColor = "#8A978E";
        bgColor = "#F5F4ED";
        dotColor = "#8A978E";
        statusTag = "OFFLINE";
      } else if (hasAnomaly) {
        borderColor = "#C95B48";
        bgColor = "#FFFFFF";
        dotColor = "#C95B48";
        statusTag = "ANOMALY";
      } else if (isWarning) {
        borderColor = "#D9A441";
        bgColor = "#FFFFFF";
        dotColor = "#D9A441";
        statusTag = "WARNING";
      }

      const ringClass = isSelected
        ? "outline: 3px solid #C7F36B; outline-offset: 2px; box-shadow: 0 0 14px rgba(199, 243, 107, 0.8);"
        : "box-shadow: 0 2px 6px rgba(25, 59, 50, 0.15);";

      const icon = L.divIcon({
        className: "agent-custom-marker",
        html: `
          <div style="
            width: 30px;
            height: 30px;
            margin-left: -15px;
            margin-top: -15px;
            border-radius: 50%;
            background: ${bgColor};
            border: 2px solid ${borderColor};
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: var(--font-mono);
            font-size: 10px;
            font-weight: 700;
            color: ${borderColor};
            cursor: pointer;
            transition: transform 0.15s ease;
            position: relative;
            ${ringClass}
          ">
            <span>${agent.id}</span>
            <span style="
              position: absolute;
              bottom: -2px;
              right: -2px;
              width: 8px;
              height: 8px;
              border-radius: 50%;
              background: ${dotColor};
              border: 1.5px solid #FFFFFF;
            "></span>
          </div>
        `,
      });

      const marker = L.marker([lat, lng], { icon });

      marker.on("click", () => {
        if (onSelectAgent) {
          onSelectAgent(agent);
        }
      });

      // Accessible tooltip with scientific telemetry
      marker.bindTooltip(
        `<div style="font-family: var(--font-sans); font-size: 11px; padding: 3px 6px;">
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
            <strong style="color: #193B32; font-family: var(--font-mono);">${agent.id}</strong>
            <span style="font-size: 9px; font-weight: 600; color: ${borderColor};">${statusTag}</span>
          </div>
          <div style="font-size: 10px; color: #456B57; margin-bottom: 2px;">${agent.agent_type || "Autonomous Sensor Node"}${isPatrollingDrone ? " · SIMULATED PATROL" : ""}</div>
          <div style="font-size: 9px; color: #69786D; font-family: var(--font-mono);">
            ${agent.readings?.temperature}°C | SMOKE: ${agent.readings?.smoke} | BAT: ${agent.battery}%
          </div>
        </div>`,
        { direction: "top", offset: [0, -12] }
      );

      layer.addLayer(marker);
    });
  }, [
    agents,
    showAgents,
    selectedAgentId,
    onSelectAgent,
    isMapReady,
    getRenderedAgentCoordinates,
    droneCoordinates,
    isPatrolling,
  ]);

  // Fit bounds helper
  const handleFitBounds = () => {
    if (!mapInstanceRef.current || !leafletRef.current) return;
    const L = leafletRef.current;
    const bounds = L.circle(
      [patrolCenter.latitude, patrolCenter.longitude],
      { radius: patrolRadiusKm * 1000 }
    ).getBounds();
    mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50], maxZoom: 13 });
  };

  // Center on selected agent
  const selectedAgent = agents.find((a) => a.id === selectedAgentId);
  useEffect(() => {
    if (!selectedAgent || !mapInstanceRef.current) return;
    const [lat, lng] = getRenderedAgentCoordinates(selectedAgent);
    mapInstanceRef.current.panTo([lat, lng], { animate: true, duration: 0.8 });
  }, [selectedAgent, getRenderedAgentCoordinates]);

  // Selected agent quick actions
  const handleQuickRestart = async (agentId: string) => {
    setActionLoading(true);
    try {
      await api.restartAgent(agentId);
      setFeedbackNotice(`Agent ${agentId} rebooted & reconnected.`);
      setTimeout(() => setFeedbackNotice(""), 3500);
      if (onRefresh) onRefresh();
    } catch (e: any) {
      alert(`Restart failed: ${e.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleQuickFail = async (agentId: string) => {
    setActionLoading(true);
    try {
      await api.failAgent(agentId);
      setFeedbackNotice(`Agent ${agentId} disconnected from network.`);
      setTimeout(() => setFeedbackNotice(""), 3500);
      if (onRefresh) onRefresh();
    } catch (e: any) {
      alert(`Failure trigger error: ${e.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleQuickRestore = async (agentId: string) => {
    setActionLoading(true);
    try {
      await api.restoreAgent(agentId);
      setFeedbackNotice(`Agent ${agentId} signal restored to ACTIVE.`);
      setTimeout(() => setFeedbackNotice(""), 3500);
      if (onRefresh) onRefresh();
    } catch (e: any) {
      alert(`Restore failed: ${e.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const deployAgentsAt = async (center: PatrolCenter) => {
    setActionLoading(true);
    setLocationError("");
    setIsPatrolling(false);
    try {
      const result = await api.deployAgents({
        latitude: center.latitude,
        longitude: center.longitude,
        radius_km: patrolRadiusKm,
        area_label: center.label,
      });
      setPatrolCenter({
        latitude: result.deployment.latitude,
        longitude: result.deployment.longitude,
        label: result.deployment.area_label,
      });
      setDeployedSite(result.deployment);
      setPatrolElapsedSeconds(0);
      setIsPatrolling(true);
      setFeedbackNotice(`${result.deployed_count} agents deployed to ${result.deployment.area_label}.`);
      setTimeout(() => setFeedbackNotice(""), 5000);
      if (onRefresh) await onRefresh();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "The agent deployment request failed.";
      console.error("Agent deployment failed:", error);
      setLocationError(`Could not deploy agents: ${message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleUseCurrentLocation = () => {
    setLocationError("");
    if (!navigator.geolocation) {
      setLocationError("Location detection is not available in this browser.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const center = {
          latitude: coords.latitude,
          longitude: coords.longitude,
          label: "Your current location",
        };
        setPatrolCenter(center);
        setIsSelectingLocation(false);
        selectingLocationRef.current = false;
        mapInstanceRef.current?.setView(
          [center.latitude, center.longitude],
          Math.max(mapInstanceRef.current.getZoom(), 13)
        );
        void deployAgentsAt(center);
      },
      (error) => {
        const message =
          error.code === error.PERMISSION_DENIED
            ? "Location permission was denied. Allow it in your browser or choose a point on the map."
            : error.code === error.POSITION_UNAVAILABLE
            ? "Your current location is unavailable. Choose a point on the map instead."
            : "Location detection timed out. Try again or choose a point on the map.";
        setLocationError(message);
      },
      { enableHighAccuracy: false, maximumAge: 60000, timeout: 12000 }
    );
  };

  const handleChooseMapLocation = () => {
    const selecting = !isSelectingLocation;
    selectingLocationRef.current = selecting;
    setIsSelectingLocation(selecting);
    setLocationError("");
  };
  const deploymentChanged =
    deployedSite !== null &&
    (deployedSite.latitude !== patrolCenter.latitude ||
      deployedSite.longitude !== patrolCenter.longitude ||
      deployedSite.radius_km !== patrolRadiusKm);

  return (
    <div className="relative bg-surface rounded border border-border shadow-editorial overflow-hidden flex flex-col h-[620px]">
      {/* Top Map Control Bar */}
      <div className="px-4 py-2.5 bg-surface-muted border-b border-border flex items-center justify-between text-xs z-10 select-none">
        {/* Left: Transect Identification & Simulation Watermark */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 font-medium text-forest-green">
            <Compass className="w-3.5 h-3.5 text-secondary-green" />
            <span className="font-serif font-bold text-sm">Drone Patrol Area</span>
            <span className="text-[10px] text-secondary-text font-mono">
              ({patrolCenter.latitude.toFixed(2)}°, {patrolCenter.longitude.toFixed(2)}°)
            </span>
          </div>
          <div className="h-3 w-px bg-border"></div>
          <span className="editorial-tag text-[9px] px-2 py-0.5 rounded bg-muted-sage/70 text-forest-green border border-border">
            SIMULATED DRONE PATROL
          </span>
        </div>

        {/* Right: Layer Toggles & Actions */}
        <div className="flex items-center gap-3">
          {/* Layer toggles */}
          <div className="hidden lg:flex items-center gap-2 text-[11px] text-secondary-text">
            <label className="flex items-center gap-1 cursor-pointer hover:text-forest-green">
              <input
                type="checkbox"
                checked={showAgents}
                onChange={(e) => setShowAgents(e.target.checked)}
                className="rounded border-border text-forest-green focus:ring-0 w-3 h-3"
              />
              <span>Agents</span>
            </label>
            <label className="flex items-center gap-1 cursor-pointer hover:text-forest-green">
              <input
                type="checkbox"
                checked={showLinks}
                onChange={(e) => setShowLinks(e.target.checked)}
                className="rounded border-border text-forest-green focus:ring-0 w-3 h-3"
              />
              <span>Mesh</span>
            </label>
            <label className="flex items-center gap-1 cursor-pointer hover:text-forest-green">
              <input
                type="checkbox"
                checked={showIncidents}
                onChange={(e) => setShowIncidents(e.target.checked)}
                className="rounded border-border text-forest-green focus:ring-0 w-3 h-3"
              />
              <span>Hazards</span>
            </label>
            <label className="flex items-center gap-1 cursor-pointer hover:text-forest-green">
              <input
                type="checkbox"
                checked={showZones}
                onChange={(e) => setShowZones(e.target.checked)}
                className="rounded border-border text-forest-green focus:ring-0 w-3 h-3"
              />
              <span>Sectors</span>
            </label>
          </div>

          <div className="h-3 w-px bg-border hidden lg:block"></div>

          {/* Action buttons */}
          <button
            onClick={() => {
              setIsPatrolling((patrolling) => !patrolling);
              setPatrolElapsedSeconds(0);
            }}
            className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-mono transition border ${
              isPatrolling
                ? "bg-botanical/20 text-forest-green border-botanical/50 font-bold"
                : "bg-surface hover:bg-surface-muted text-forest-green border-border"
            }`}
            title="Start or stop the simulated drone patrol"
          >
            <Play className={`w-3 h-3 ${isPatrolling ? "fill-current text-forest-green" : ""}`} />
            <span>{isPatrolling ? "Drones Patrolling" : "Start Drone Patrol"}</span>
          </button>

          <button
            onClick={handleFitBounds}
            className="flex items-center gap-1 px-2 py-1 rounded bg-surface hover:bg-surface-muted text-secondary-text hover:text-forest-green border border-border transition text-xs"
            title="Fit the selected drone patrol area"
          >
            <Maximize2 className="w-3 h-3" />
            <span className="hidden sm:inline">Fit Patrol Area</span>
          </button>
        </div>
      </div>

      {/* Main Map View Area */}
      <div className="relative flex-1 w-full h-full bg-[#EDECE4]">
        <div className="absolute top-3 left-4 z-20 max-w-[calc(100%-2rem)] rounded border border-border bg-surface/95 p-3 shadow-elevated backdrop-blur">
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={handleUseCurrentLocation}
              disabled={actionLoading}
              className="flex items-center gap-1.5 rounded border border-border bg-surface px-2.5 py-1.5 text-[11px] font-mono text-forest-green transition hover:bg-surface-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest-green"
            >
              <LocateFixed className="h-3.5 w-3.5" aria-hidden="true" />
              {actionLoading ? "Deploying…" : "Deploy at my location"}
            </button>
            <button
              type="button"
              onClick={handleChooseMapLocation}
              disabled={actionLoading}
              aria-pressed={isSelectingLocation}
              className={`flex items-center gap-1.5 rounded border px-2.5 py-1.5 text-[11px] font-mono transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest-green ${
                isSelectingLocation
                  ? "border-forest-green bg-forest-green text-surface"
                  : "border-border bg-surface text-forest-green hover:bg-surface-muted"
              }`}
            >
              <MapPin className="h-3.5 w-3.5" aria-hidden="true" />
              {isSelectingLocation ? "Click map to place drones…" : "Choose on map"}
            </button>
            <label className="flex items-center gap-2 text-[10px] font-mono text-secondary-text">
              <span>Patrol range</span>
              <input
                type="range"
                min="0.5"
                max="10"
                step="0.5"
                value={patrolRadiusKm}
                onChange={(event) => {
                  setPatrolRadiusKm(Number(event.target.value));
                  setIsPatrolling(false);
                }}
                aria-label="Drone patrol radius in kilometers"
                className="w-20 accent-forest-green"
              />
              <span className="w-10 text-forest-green">{patrolRadiusKm.toFixed(1)} km</span>
            </label>
            <button
              type="button"
              onClick={() => void deployAgentsAt(patrolCenter)}
              disabled={actionLoading}
              className="rounded bg-forest-green px-2.5 py-1.5 text-[11px] font-mono text-surface transition hover:bg-forest-green-light focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest-green disabled:cursor-wait disabled:opacity-60"
            >
              {actionLoading ? "Deploying…" : "Deploy agents here"}
            </button>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] font-mono text-secondary-text">
            <span>
              {patrolCenter.label}: {patrolCenter.latitude.toFixed(4)}, {patrolCenter.longitude.toFixed(4)}
            </span>
            <span>
              {agents.filter((agent) => agent.deployed).length} of {agents.length} agents deployed
            </span>
            <span>{activeDrones.length} active drone{activeDrones.length === 1 ? "" : "s"} detected</span>
            <span>
              {isPatrolling
                ? "SIMULATED DRONE PATROL RUNNING"
                : deploymentChanged
                ? "DEPLOYMENT CHANGED — APPLY TO UPDATE"
                : deployedSite
                ? "AGENT POSITIONS SAVED"
                : "READY TO DEPLOY"}
            </span>
          </div>
          {locationError && (
            <p role="alert" className="mt-2 text-[11px] text-critical-incident">
              {locationError}
            </p>
          )}
          <p className="mt-1 text-[9px] text-secondary-text">
            This updates simulated agent coordinates in the app backend; it does not control physical drones. Esri receives map tile requests for the displayed area.
          </p>
        </div>

        {/* Tile error or fallback banner */}
        {tileError && (
          <div className="absolute top-3 left-4 right-4 z-20 bg-warning-amber/10 border border-warning-amber/40 text-warning-amber p-2.5 rounded text-xs flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>
                Cartographic map tiles unavailable — displaying active vector mesh overlay. Full telemetry and agent controls remain operational.
              </span>
            </div>
            <button
              onClick={() => setTileError(false)}
              className="text-secondary-text hover:text-forest-green text-xs font-mono"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Action feedback notice */}
        {feedbackNotice && (
          <div className="absolute top-3 left-1/2 -translate-x-1/2 z-20 bg-forest-green text-surface px-3 py-1.5 rounded shadow-elevated text-xs font-mono flex items-center gap-2 animate-fade-in">
            <CheckCircle2 className="w-3.5 h-3.5 text-botanical" />
            <span>{feedbackNotice}</span>
          </div>
        )}

        {/* The Leaflet Container */}
        <div ref={mapContainerRef} className="w-full h-full" />

        {/* Selected Agent Inspector Panel Overlay on Map (Top-Left) */}
        {selectedAgent && (
          <div className="absolute bottom-10 left-4 z-20 w-80 bg-surface/95 backdrop-blur border border-border rounded shadow-elevated p-4 text-xs select-none">
            {/* Header */}
            <div className="flex items-center justify-between pb-2 border-b border-border">
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-sm text-forest-green">
                  {selectedAgent.id}
                </span>
                <span
                  className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-semibold ${
                    selectedAgent.status === "ACTIVE"
                      ? "bg-muted-sage text-forest-green"
                      : "bg-critical-incident/15 text-critical-incident"
                  }`}
                >
                  {selectedAgent.status}
                </span>
              </div>
              <button
                onClick={() => onSelectAgent && onSelectAgent(null as any)}
                className="text-secondary-text hover:text-forest-green"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Sub-header: Type & Assignment */}
            <div className="py-2 space-y-1">
              <div className="font-medium text-forest-green text-[11px]">
                {selectedAgent.agent_type || "Autonomous Sensor Node"}
              </div>
              <div className="text-[10px] text-secondary-text italic leading-tight">
                {selectedAgent.assignment || "Transect Ecological Surveillance"}
              </div>
            </div>

            {/* Telemetry Metrics Grid */}
            <div className="grid grid-cols-3 gap-1.5 py-2 my-1 bg-surface-muted rounded p-2 border border-border/60">
              <div>
                <span className="text-[9px] text-secondary-text block">TEMP</span>
                <span className="font-mono font-semibold text-forest-green tabular-nums">
                  {selectedAgent.readings?.temperature}°C
                </span>
              </div>
              <div>
                <span className="text-[9px] text-secondary-text block">SMOKE</span>
                <span className="font-mono font-semibold text-forest-green tabular-nums">
                  {selectedAgent.readings?.smoke}
                </span>
              </div>
              <div>
                <span className="text-[9px] text-secondary-text block">CO2</span>
                <span className="font-mono font-semibold text-forest-green tabular-nums">
                  {Math.round(selectedAgent.readings?.co2)} ppm
                </span>
              </div>
              <div>
                <span className="text-[9px] text-secondary-text block">HUMIDITY</span>
                <span className="font-mono font-semibold text-forest-green tabular-nums">
                  {selectedAgent.readings?.humidity}%
                </span>
              </div>
              <div>
                <span className="text-[9px] text-secondary-text block">AIR QUAL</span>
                <span className="font-mono font-semibold text-forest-green tabular-nums">
                  {Math.round(selectedAgent.readings?.air_quality)} AQI
                </span>
              </div>
              <div>
                <span className="text-[9px] text-secondary-text block">BATTERY</span>
                <span className="font-mono font-semibold text-forest-green tabular-nums">
                  {selectedAgent.battery}%
                </span>
              </div>
            </div>

            {/* Neighbors and Risk Score */}
            <div className="pt-2 text-[10px] text-secondary-text flex items-center justify-between">
              <span>
                Mesh Neighbors: <strong className="text-forest-green font-mono">{selectedAgent.neighbors?.length || 0}</strong>
              </span>
              <span>
                Local Risk: <strong className="text-forest-green font-mono">{selectedAgent.risk_score || 8}%</strong>
              </span>
            </div>

            {/* Agent Operational Controls */}
            <div className="mt-3 pt-2 border-t border-border flex items-center gap-2">
              {selectedAgent.status === "ACTIVE" ? (
                <button
                  onClick={() => handleQuickFail(selectedAgent.id)}
                  disabled={actionLoading}
                  className="flex-1 flex items-center justify-center gap-1.5 py-1 px-2 rounded bg-surface hover:bg-critical-incident/10 text-critical-incident border border-critical-incident/30 transition text-[10px] font-mono"
                >
                  <PowerOff className="w-3 h-3" />
                  <span>Simulate Fail</span>
                </button>
              ) : (
                <button
                  onClick={() => handleQuickRestore(selectedAgent.id)}
                  disabled={actionLoading}
                  className="flex-1 flex items-center justify-center gap-1.5 py-1 px-2 rounded bg-forest-green text-surface transition text-[10px] font-mono"
                >
                  <CheckCircle2 className="w-3 h-3 text-botanical" />
                  <span>Restore Signal</span>
                </button>
              )}

              <button
                onClick={() => handleQuickRestart(selectedAgent.id)}
                disabled={actionLoading}
                className="flex items-center justify-center gap-1 py-1 px-2 rounded bg-surface hover:bg-surface-muted text-forest-green border border-border transition text-[10px] font-mono"
                title="Reboot node and re-link mesh"
              >
                <RotateCcw className="w-3 h-3 text-secondary-green" />
                <span>Reboot</span>
              </button>
            </div>
          </div>
        )}

        {/* Compact Bottom Legend */}
        <div className="absolute bottom-3 right-4 z-10 bg-surface/90 backdrop-blur border border-border px-3 py-1.5 rounded text-[10px] flex items-center gap-3 text-secondary-text shadow-sm">
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-forest-green inline-block"></span>
            <span>Active</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-warning-amber inline-block"></span>
            <span>Warning</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-critical-incident inline-block"></span>
            <span>Hazard</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-border-dark inline-block"></span>
            <span>Offline</span>
          </div>
          <div className="flex items-center gap-1 border-l border-border pl-2">
            <span className="w-3 h-0.5 border-t border-dashed border-secondary-green inline-block"></span>
            <span>P2P Mesh</span>
          </div>
        </div>
      </div>
    </div>
  );
}
