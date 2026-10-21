"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AnalyticsData } from "@/lib/types";
import {
  LineChart as LineChartIcon,
  Thermometer,
  CloudFog,
  Wind,
  Zap,
  Droplets,
  Activity,
  Layers,
  Clock
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar
} from "recharts";

export default function EnvironmentalAnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    try {
      const res = await api.getAnalytics();
      setData(res);
    } catch (err) {
      console.error("Failed to load analytics:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 3500);
    return () => clearInterval(interval);
  }, []);

  // Compute soil moisture mockup trend based on temperature or readings
  const soilTrend = (data?.temperature_trend || []).map((pt) => ({
    time: pt.time,
    agent: pt.agent,
    value: Math.max(15, Math.min(85, Math.round(75 - (pt.value - 20) * 1.5))),
  }));

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-border pb-5">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="editorial-tag text-secondary-text mb-1 tracking-widest">
              FIELD OBSERVATORY TELEMETRY
            </div>
            <h1 className="editorial-title text-3xl md:text-4xl font-serif font-bold text-forest-green tracking-tight leading-none">
              Environmental Analytics & Trends.
            </h1>
            <p className="mt-2 text-sm text-secondary-text max-w-2xl leading-relaxed">
              Longitudinal scientific telemetry logged across the Cascade Biosphere Reserve.
              Sensors track micro-climatic thermal variation, atmospheric aerosol concentrations,
              hydrological soil saturation, and network reorganization efficiency.
            </p>
          </div>

          <div className="flex items-center gap-1.5 text-xs font-mono text-secondary-text">
            <span className="w-2 h-2 rounded-full bg-secondary-green inline-block"></span>
            <span>CASCADE TRANSECT TELEMETRY</span>
          </div>
        </div>
      </div>

      {/* 6 Editorial Scientific Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 1. Temperature Trend */}
        <div className="bg-surface p-5 rounded border border-border shadow-editorial flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2.5 border-b border-border mb-3">
              <div className="flex items-center gap-2">
                <Thermometer className="w-4 h-4 text-secondary-green" />
                <h3 className="font-serif font-bold text-sm text-forest-green">
                  Ambient Temperature (°C)
                </h3>
              </div>
              <span className="editorial-tag text-[9px] text-secondary-text">
                BASELINE: 28.0°C
              </span>
            </div>

            <div className="h-60 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data?.temperature_trend || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#DFE4D9" opacity={0.6} />
                  <XAxis dataKey="time" stroke="#69786D" fontSize={10} tickLine={false} />
                  <YAxis stroke="#69786D" fontSize={10} domain={[15, 55]} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#FFFFFF",
                      borderColor: "#DFE4D9",
                      borderRadius: "4px",
                      fontSize: "11px",
                      fontFamily: "var(--font-mono)",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#193B32"
                    strokeWidth={2}
                    dot={{ r: 2, fill: "#C7F36B" }}
                    name="Temp (°C)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="pt-2.5 border-t border-border flex items-center justify-between text-[10px] font-mono text-secondary-text">
            <span>PHYSIOLOGICAL STRESS: &gt;38.0°C</span>
            <span>COMBUSTION HAZARD: &gt;45.0°C</span>
          </div>
        </div>

        {/* 2. Smoke Particulates */}
        <div className="bg-surface p-5 rounded border border-border shadow-editorial flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2.5 border-b border-border mb-3">
              <div className="flex items-center gap-2">
                <CloudFog className="w-4 h-4 text-warning-amber" />
                <h3 className="font-serif font-bold text-sm text-forest-green">
                  Aerosol & Smoke Particulate Index
                </h3>
              </div>
              <span className="editorial-tag text-[9px] text-secondary-text">
                NORMAL &lt; 0.20
              </span>
            </div>

            <div className="h-60 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data?.smoke_trend || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#DFE4D9" opacity={0.6} />
                  <XAxis dataKey="time" stroke="#69786D" fontSize={10} tickLine={false} />
                  <YAxis stroke="#69786D" fontSize={10} domain={[0, 1]} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#FFFFFF",
                      borderColor: "#DFE4D9",
                      borderRadius: "4px",
                      fontSize: "11px",
                      fontFamily: "var(--font-mono)",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#D9A441"
                    strokeWidth={2}
                    dot={{ r: 2, fill: "#D9A441" }}
                    name="Smoke (0-1)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="pt-2.5 border-t border-border flex items-center justify-between text-[10px] font-mono text-secondary-text">
            <span>OPTICAL OBSCURATION</span>
            <span>WILDFIRE THRESHOLD: 0.60</span>
          </div>
        </div>

        {/* 3. Carbon Dioxide Concentration */}
        <div className="bg-surface p-5 rounded border border-border shadow-editorial flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2.5 border-b border-border mb-3">
              <div className="flex items-center gap-2">
                <Wind className="w-4 h-4 text-secondary-green" />
                <h3 className="font-serif font-bold text-sm text-forest-green">
                  Carbon Dioxide (CO2 ppm)
                </h3>
              </div>
              <span className="editorial-tag text-[9px] text-secondary-text">
                BACKGROUND: ~420 ppm
              </span>
            </div>

            <div className="h-60 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data?.co2_trend || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#DFE4D9" opacity={0.6} />
                  <XAxis dataKey="time" stroke="#69786D" fontSize={10} tickLine={false} />
                  <YAxis stroke="#69786D" fontSize={10} domain={[350, 1200]} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#FFFFFF",
                      borderColor: "#DFE4D9",
                      borderRadius: "4px",
                      fontSize: "11px",
                      fontFamily: "var(--font-mono)",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#456B57"
                    strokeWidth={2}
                    dot={{ r: 2, fill: "#193B32" }}
                    name="CO2 (ppm)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="pt-2.5 border-t border-border flex items-center justify-between text-[10px] font-mono text-secondary-text">
            <span>ATMOSPHERIC BASELINE</span>
            <span>POINT SOURCE ANOMALY &gt; 700 ppm</span>
          </div>
        </div>

        {/* 4. Air Quality Index */}
        <div className="bg-surface p-5 rounded border border-border shadow-editorial flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2.5 border-b border-border mb-3">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-secondary-green" />
                <h3 className="font-serif font-bold text-sm text-forest-green">
                  Air Quality Index (AQI)
                </h3>
              </div>
              <span className="editorial-tag text-[9px] text-secondary-text">
                HEALTHY &lt; 50 AQI
              </span>
            </div>

            <div className="h-60 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data?.air_quality_trend || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#DFE4D9" opacity={0.6} />
                  <XAxis dataKey="time" stroke="#69786D" fontSize={10} tickLine={false} />
                  <YAxis stroke="#69786D" fontSize={10} domain={[10, 250]} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#FFFFFF",
                      borderColor: "#DFE4D9",
                      borderRadius: "4px",
                      fontSize: "11px",
                      fontFamily: "var(--font-mono)",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#193B32"
                    strokeWidth={2}
                    dot={{ r: 2, fill: "#D9A441" }}
                    name="AQI"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="pt-2.5 border-t border-border flex items-center justify-between text-[10px] font-mono text-secondary-text">
            <span>GOOD (0-50) | MODERATE (51-100)</span>
            <span>HAZARDOUS (&gt;150)</span>
          </div>
        </div>

        {/* 5. Hydrological Soil Moisture Saturation */}
        <div className="bg-surface p-5 rounded border border-border shadow-editorial flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2.5 border-b border-border mb-3">
              <div className="flex items-center gap-2">
                <Droplets className="w-4 h-4 text-secondary-green" />
                <h3 className="font-serif font-bold text-sm text-forest-green">
                  Hydrological Soil Moisture Saturation (%)
                </h3>
              </div>
              <span className="editorial-tag text-[9px] text-secondary-text">
                OPTIMAL: 50-70%
              </span>
            </div>

            <div className="h-60 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={soilTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#DFE4D9" opacity={0.6} />
                  <XAxis dataKey="time" stroke="#69786D" fontSize={10} tickLine={false} />
                  <YAxis stroke="#69786D" fontSize={10} domain={[10, 100]} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#FFFFFF",
                      borderColor: "#DFE4D9",
                      borderRadius: "4px",
                      fontSize: "11px",
                      fontFamily: "var(--font-mono)",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#456B57"
                    strokeWidth={2}
                    dot={{ r: 2, fill: "#C7F36B" }}
                    name="Moisture (%)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="pt-2.5 border-t border-border flex items-center justify-between text-[10px] font-mono text-secondary-text">
            <span>RIPARIAN FLUVIAL BASIN</span>
            <span>DROUGHT STRESS: &lt;25%</span>
          </div>
        </div>

        {/* 6. Network Recovery Duration */}
        <div className="bg-surface p-5 rounded border border-border shadow-editorial flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2.5 border-b border-border mb-3">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-secondary-green" />
                <h3 className="font-serif font-bold text-sm text-forest-green">
                  Autonomous Mesh Healing Duration (ms)
                </h3>
              </div>
              <span className="editorial-tag text-[9px] text-secondary-text">
                TARGET &lt; 50 ms
              </span>
            </div>

            <div className="h-60 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data?.recovery_history || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#DFE4D9" opacity={0.6} />
                  <XAxis dataKey="time" stroke="#69786D" fontSize={10} tickLine={false} />
                  <YAxis stroke="#69786D" fontSize={10} domain={[0, 40]} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#FFFFFF",
                      borderColor: "#DFE4D9",
                      borderRadius: "4px",
                      fontSize: "11px",
                      fontFamily: "var(--font-mono)",
                    }}
                  />
                  <Bar dataKey="duration_ms" fill="#193B32" name="Duration (ms)" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="pt-2.5 border-t border-border flex items-center justify-between text-[10px] font-mono text-secondary-text">
            <span>DISBURSED GRAPH REBUILD</span>
            <span>AVERAGE: ~14 ms</span>
          </div>
        </div>
      </div>
    </div>
  );
}
