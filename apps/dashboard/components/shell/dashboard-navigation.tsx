"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const navigation = [
  { href: "/", label: "Overview", shortLabel: "Overview" },
  { href: "/vehicle", label: "Vehicle Details", shortLabel: "Vehicle" },
  { href: "/market", label: "Market Overview", shortLabel: "Market" },
  { href: "/methodology", label: "About the Data", shortLabel: "Data" },
];

const selectionKeys = ["make", "model", "year", "region"];

export function DashboardNavigation({
  variant,
}: {
  variant: "desktop" | "mobile";
}) {
  const pathname = usePathname();
  const [selectionSuffix, setSelectionSuffix] = useState("");

  useEffect(() => {
    const current = new URLSearchParams(window.location.search);
    const selection = new URLSearchParams();

    for (const key of selectionKeys) {
      const value = current.get(key);
      if (value) selection.set(key, value);
    }

    const encoded = selection.toString();
    setSelectionSuffix(encoded ? `?${encoded}` : "");
  }, [pathname]);

  if (variant === "desktop") {
    return (
      <nav
        aria-label="Primary dashboard navigation"
        className="flex items-center gap-2"
      >
        {navigation.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={`${item.href}${selectionSuffix}`}
              aria-current={active ? "page" : undefined}
              className={`floating-nav-item ${
                active ? "floating-nav-item-active" : ""
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    );
  }

  return (
    <nav
      aria-label="Primary dashboard navigation"
      className="glass-floating grid grid-cols-4 gap-1 rounded-[1.4rem] p-1.5 shadow-[0_18px_45px_rgba(15,23,42,0.20)]"
    >
      {navigation.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={`${item.href}${selectionSuffix}`}
            aria-current={active ? "page" : undefined}
            aria-label={item.label}
            className={`flex min-h-12 min-w-0 items-center justify-center rounded-2xl border px-2 py-2 text-center text-[11px] font-black leading-tight transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-900 focus-visible:ring-offset-2 ${
              active
                ? "border-slate-950 bg-slate-950 text-white shadow-[0_7px_16px_rgba(15,23,42,0.28)]"
                : "border-transparent text-slate-950 hover:border-slate-300 hover:bg-white"
            }`}
          >
            {item.shortLabel}
          </Link>
        );
      })}
    </nav>
  );
}
