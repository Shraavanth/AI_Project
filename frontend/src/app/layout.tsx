import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Lora, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";

const sans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const serif = Lora({
  subsets: ["latin"],
  variable: "--font-serif",
  style: ["normal", "italic"],
  display: "swap",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Eco-Intelligence | Decentralized Environmental Monitoring",
  description:
    "Autonomous multi-agent environmental intelligence platform observing forest transects, sharing sensor evidence, and adapting without centralized authority.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${sans.variable} ${serif.variable} ${mono.variable}`}>
      <body className="bg-background text-primary-text flex h-screen overflow-hidden antialiased font-sans">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-background">
          <Header />
          <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-background">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
