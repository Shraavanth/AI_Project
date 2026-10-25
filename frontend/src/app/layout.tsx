import type { Metadata, Viewport } from "next";
import "@fontsource/barlow/400.css";
import "@fontsource/barlow/500.css";
import "@fontsource/barlow/600.css";
import "@fontsource/barlow-semi-condensed/500.css";
import "@fontsource/barlow-semi-condensed/600.css";
import "leaflet/dist/leaflet.css";
import "./globals.css";
import { SimulationProvider } from "@/components/SimulationProvider";
import { Sidebar } from "@/components/Sidebar";
import { Toasts } from "@/components/Toasts";
import { OfflineNotice } from "@/components/OfflineNotice";

export const metadata: Metadata = {
  title: "EnvMAS - Environmental Multi-Agent Monitoring",
  description: "Self-organizing multi-agent system for decentralized environmental monitoring and response.",
};

export const viewport: Viewport = { themeColor: "#DCEAF5", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-[#DCEAF5] text-[#18344D]">
        <SimulationProvider>
          <div className="flex min-h-screen flex-col lg:h-screen lg:flex-row lg:overflow-hidden bg-[#DCEAF5]">
            <Sidebar />
            <main className="flex min-w-0 flex-1 flex-col lg:overflow-hidden bg-[#DCEAF5]">
              <OfflineNotice />
              <div className="min-h-0 flex-1 lg:overflow-y-auto scroll-thin">{children}</div>
            </main>
          </div>
          <Toasts />
        </SimulationProvider>
      </body>
    </html>
  );
}
