"use client";

import React, { useState, useEffect } from "react";
import { Agent } from "@/lib/types";
import { api } from "@/lib/api";
import {
  X,
  Battery,
  Heart,
  Wifi,
  Shield,
  Activity,
  Sliders,
  PowerOff,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  Compass,
  Cpu,
  Trash2
} from "lucide-react";
import { getAgentCoordinates } from "./LiveMonitoringMap";

interface Props {
  agent: Agent | null;
  onClose: () => void;
  onUpdate: () => void;
}

export default function AgentDetailModal({ agent, onClose, onUpdate }: Props) {
  const [sensors, setSensors] = useState({
    temperature: agent?.readings?.temperature ?? 28,
    humidity: agent?.readings?.humidity ?? 60,
    smoke: agent?.readings?.smoke ?? 0.1,
    co2: agent?.readings?.co2 ?? 420,
    air_quality: agent?.readings?.air_quality ?? 50,
    soil_moisture: agent?.readings?.soil_moisture ?? 55,
    battery: agent?.battery ?? 100,
  });

  const [coords, setCoords] = useState({
    x: agent?.position[0] ?? 0,
    y: agent?.position[1] ?? 0,
  });

  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    if (!agent) return;
    setSensors({
      temperature: agent.readings?.temperature ?? 28,
      humidity: agent.readings?.humidity ?? 60,
      smoke: agent.readings?.smoke ?? 0.1,
      co2: agent.readings?.co2 ?? 420,
      air_quality: agent.readings?.air_quality ?? 50,
      soil_moisture: agent.readings?.soil_moisture ?? 55,
      battery: agent.battery ?? 100,
    });
    setCoords({
      x: agent.position ? agent.position[0] : 0,
      y: agent.position ? agent.position[1] : 0,
    });
  }, [agent]);

  if (!agent) return null;

  const [lat, lng] = getAgentCoordinates(agent);

  const handleApplySensors = async () => {
    setLoading(true);
    try {
      await api.updateAgent(agent.id, sensors);
      setSuccessMsg("Telemetry calibrated & AI re-analyzed.");
      setTimeout(() => setSuccessMsg(""), 3000);
      onUpdate();
    } catch (e: any) {
      alert(`Update failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleMove = async () => {
    setLoading(true);
    try {
      await api.updateAgent(agent.id, { x: coords.x, y: coords.y });
      setSuccessMsg(`Node repositioned to grid (${coords.x}, ${coords.y}).`);
      setTimeout(() => setSuccessMsg(""), 3000);
      onUpdate();
    } catch (e: any) {
      alert(`Move failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleFail = async () => {
    setLoading(true);
    try {
      if (agent.status === "ACTIVE") {
        await api.failAgent(agent.id);
        setSuccessMsg(`Node ${agent.id} marked as FAILED`);
      } else {
        await api.restoreAgent(agent.id);
        setSuccessMsg(`Node ${agent.id} restored to ACTIVE`);
      }
      setTimeout(() => setSuccessMsg(""), 3000);
      onUpdate();
    } catch (e: any) {
      alert(`Action failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRestart = async () => {
    setLoading(true);
    try {
      await api.restartAgent(agent.id);
      setSuccessMsg(`Node ${agent.id} rebooted and mesh topology updated.`);
      setTimeout(() => setSuccessMsg(""), 3000);
      onUpdate();
    } catch (e: any) {
      alert(`Reboot failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm(`Permanently decommission agent node ${agent.id}?`)) return;
    setLoading(true);
    try {
      await api.deleteAgent(agent.id);
      onUpdate();
      onClose();
    } catch (e: any) {
      alert(`Delete failed: ${e.message}`);
      setLoading(false);
    }
  };

  const isAnomalous = agent.ai_result?.status === "ANOMALY";
  const event = agent.ai_result?.event || "None";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-forest-green/40 backdrop-blur-sm p-4 animate-fade-in select-none">
      <div className="bg-surface border border-border rounded w-full max-w-2xl max-h-[92vh] overflow-y-auto shadow-elevated p-6 relative">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-border mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded bg-forest-green text-botanical flex items-center justify-center font-mono font-bold text-sm shadow-sm">
              {agent.id}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-serif font-bold text-base text-forest-green">
                  {agent.agent_type || "Autonomous Sensor Node"}
                </h3>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold ${
                    agent.status === "ACTIVE"
                      ? "bg-muted-sage text-forest-green"
                      : "bg-critical-incident/15 text-critical-incident"
                  }`}
                >
                  {agent.status}
                </span>
              </div>
              <p className="text-xs text-secondary-text font-mono">
                Transect: {lat}° N, {lng}° W | Sector: {agent.zone || "Cascade Transect"}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-7 h-7 rounded hover:bg-surface-muted flex items-center justify-center text-secondary-text hover:text-forest-green transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Success Banner */}
        {successMsg && (
          <div className="mb-4 p-2.5 rounded bg-muted-sage text-forest-green text-xs font-mono flex items-center gap-2 animate-fade-in border border-border">
            <CheckCircle className="w-4 h-4 text-secondary-green" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Assignment & Status Callout */}
        <div className="mb-4 p-3 rounded bg-surface-muted border border-border">
          <div className="editorial-tag text-[9px] text-secondary-text mb-1">
            CURRENT MONITORING ASSIGNMENT
          </div>
          <div className="text-xs font-serif text-forest-green font-medium">
            {agent.assignment || "Routine Forest Ecological Transect Surveillance"}
          </div>
        </div>

        {/* 4 Health Gauges */}
        <div className="grid grid-cols-4 gap-3 mb-5">
          <div className="bg-surface-muted p-3 rounded border border-border">
            <div className="flex items-center justify-between text-secondary-text text-xs mb-1">
              <span className="flex items-center gap-1 text-[11px]">
                <Battery className="w-3.5 h-3.5 text-secondary-green" /> Battery
              </span>
            </div>
            <div className="text-base font-mono font-bold text-forest-green tabular-nums">
              {agent.battery}%
            </div>
            <div className="w-full h-1 bg-border rounded-full mt-1.5 overflow-hidden">
              <div
                className="h-full bg-secondary-green rounded-full"
                style={{ width: `${agent.battery}%` }}
              />
            </div>
          </div>

          <div className="bg-surface-muted p-3 rounded border border-border">
            <div className="flex items-center justify-between text-secondary-text text-xs mb-1">
              <span className="flex items-center gap-1 text-[11px]">
                <Heart className="w-3.5 h-3.5 text-secondary-green" /> Health
              </span>
            </div>
            <div className="text-base font-mono font-bold text-forest-green tabular-nums">
              {agent.health}%
            </div>
            <div className="w-full h-1 bg-border rounded-full mt-1.5 overflow-hidden">
              <div
                className="h-full bg-secondary-green rounded-full"
                style={{ width: `${agent.health}%` }}
              />
            </div>
          </div>

          <div className="bg-surface-muted p-3 rounded border border-border">
            <div className="flex items-center justify-between text-secondary-text text-xs mb-1">
              <span className="flex items-center gap-1 text-[11px]">
                <Wifi className="w-3.5 h-3.5 text-secondary-green" /> Mesh
              </span>
            </div>
            <div className="text-base font-mono font-bold text-forest-green tabular-nums">
              {agent.connectivity}%
            </div>
            <div className="w-full h-1 bg-border rounded-full mt-1.5 overflow-hidden">
              <div
                className="h-full bg-secondary-green rounded-full"
                style={{ width: `${agent.connectivity}%` }}
              />
            </div>
          </div>

          <div className="bg-surface-muted p-3 rounded border border-border">
            <div className="flex items-center justify-between text-secondary-text text-xs mb-1">
              <span className="flex items-center gap-1 text-[11px]">
                <Shield className="w-3.5 h-3.5 text-secondary-green" /> Reliability
              </span>
            </div>
            <div className="text-base font-mono font-bold text-forest-green tabular-nums">
              {agent.reliability}%
            </div>
            <div className="w-full h-1 bg-border rounded-full mt-1.5 overflow-hidden">
              <div
                className="h-full bg-secondary-green rounded-full"
                style={{ width: `${agent.reliability}%` }}
              />
            </div>
          </div>
        </div>

        {/* AI Anomaly Assessment */}
        <div
          className={`p-4 rounded border mb-5 ${
            isAnomalous
              ? "bg-critical-incident/10 border-critical-incident/30"
              : "bg-muted-sage/40 border-border"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span
              className={`editorial-tag text-[9px] font-bold ${
                isAnomalous ? "text-critical-incident" : "text-forest-green"
              }`}
            >
              {isAnomalous ? `HAZARD DETECTED: ${event}` : "AI TELEMETRY: NORMAL"}
            </span>
            <span className="text-[10px] font-mono text-secondary-text">
              Score: {agent.ai_result ? Math.round(agent.ai_result.score * 100) : 4}%
            </span>
          </div>

          <p className="text-xs text-secondary-text leading-relaxed">
            {agent.ai_explanation?.narrative ||
              "All environmental indicators remain within baseline physiological tolerances for this transect sector."}
          </p>
        </div>

        {/* Telemetry Calibration Sliders */}
        <div className="mb-5">
          <div className="flex items-center justify-between mb-3">
            <span className="editorial-tag text-[10px] text-secondary-text">
              CALIBRATE FIELD SENSOR TELEMETRY
            </span>
            <span className="text-[10px] text-secondary-text font-mono">
              Live In-Memory Adjustment
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs bg-surface-muted p-3 rounded border border-border">
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-secondary-text">Temperature</span>
                <span className="font-mono text-forest-green tabular-nums">
                  {sensors.temperature}°C
                </span>
              </div>
              <input
                type="range"
                min="15"
                max="55"
                step="0.5"
                value={sensors.temperature}
                onChange={(e) =>
                  setSensors({ ...sensors, temperature: parseFloat(e.target.value) })
                }
                className="w-full accent-forest-green"
              />
            </div>

            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-secondary-text">Smoke Index</span>
                <span className="font-mono text-forest-green tabular-nums">
                  {sensors.smoke}
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.02"
                value={sensors.smoke}
                onChange={(e) =>
                  setSensors({ ...sensors, smoke: parseFloat(e.target.value) })
                }
                className="w-full accent-forest-green"
              />
            </div>

            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-secondary-text">CO2 Concentration</span>
                <span className="font-mono text-forest-green tabular-nums">
                  {sensors.co2} ppm
                </span>
              </div>
              <input
                type="range"
                min="350"
                max="1500"
                step="10"
                value={sensors.co2}
                onChange={(e) =>
                  setSensors({ ...sensors, co2: parseFloat(e.target.value) })
                }
                className="w-full accent-forest-green"
              />
            </div>

            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-secondary-text">Air Quality Index</span>
                <span className="font-mono text-forest-green tabular-nums">
                  {sensors.air_quality} AQI
                </span>
              </div>
              <input
                type="range"
                min="10"
                max="300"
                step="5"
                value={sensors.air_quality}
                onChange={(e) =>
                  setSensors({ ...sensors, air_quality: parseFloat(e.target.value) })
                }
                className="w-full accent-forest-green"
              />
            </div>
          </div>

          <div className="mt-3 flex justify-end">
            <button
              onClick={handleApplySensors}
              disabled={loading}
              className="px-3.5 py-1.5 rounded bg-forest-green hover:bg-forest-green-light text-surface text-xs font-medium transition shadow-sm"
            >
              Apply Sensor Calibration
            </button>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="pt-4 border-t border-border flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <button
              onClick={handleToggleFail}
              disabled={loading}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded border transition font-mono text-[11px] ${
                agent.status === "ACTIVE"
                  ? "bg-surface text-critical-incident border-critical-incident/40 hover:bg-critical-incident/10"
                  : "bg-forest-green text-surface border-forest-green"
              }`}
            >
              <PowerOff className="w-3.5 h-3.5" />
              <span>{agent.status === "ACTIVE" ? "Simulate Failure" : "Restore Node"}</span>
            </button>

            <button
              onClick={handleRestart}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface hover:bg-surface-muted text-forest-green border border-border transition font-mono text-[11px]"
            >
              <RotateCcw className="w-3.5 h-3.5 text-secondary-green" />
              <span>Reboot & Sync</span>
            </button>
          </div>

          <button
            onClick={handleDelete}
            disabled={loading}
            className="flex items-center gap-1 text-secondary-text hover:text-critical-incident transition text-[11px]"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Decommission</span>
          </button>
        </div>
      </div>
    </div>
  );
}
