import type { Metadata } from "next";
import type { ReactNode } from "react";

import { DashboardShell } from "@/components/shell/dashboard-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "Fin Engine | Collateral Intelligence POC",
  description: "Business dashboard proof of concept for vehicle collateral intelligence.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <DashboardShell>{children}</DashboardShell>
      </body>
    </html>
  );
}
