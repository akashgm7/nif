import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import TopNav from "@/components/TopNav";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "NIFTY SNIPER | Institutional AI Signal Engine",
  description: "Advanced AI-powered market scanning and institutional signal generation platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased dark">
      <body className={`${inter.className} bg-[#0a0e14] text-slate-200 min-h-full`}>
        <div className="flex">
          <Sidebar />
          <div className="flex-1 flex flex-col min-h-screen">
            <TopNav />
            <main className="p-8 relative">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
