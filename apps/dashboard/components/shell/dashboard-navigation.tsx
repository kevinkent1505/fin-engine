"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  { href: "/", label: "Overview", shortLabel: "Overview" },
  { href: "/vehicle", label: "Vehicle Intelligence", shortLabel: "Vehicle" },
  { href: "/market", label: "Market Intelligence", shortLabel: "Market" },
  { href: "/methodology", label: "Data & Methodology", shortLabel: "Data" },
];

export function DashboardNavigation({
  variant,
}: {
  variant: "desktop" | "mobile";
}) {
  const pathname = usePathname();

  if (variant === "desktop") {
    return (
      <nav
        aria-label="Primary dashboard navigation"
        className="glass-floating flex items-center gap-1 rounded-full p-1.5"
      >
        {navigation.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={`inline-flex min-h-11 items-center rounded-full px-4 py-2 text-sm font-bold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-800 focus-visible:ring-offset-2 ${
                active
                  ? "bg-slate-950 text-white shadow-[0_8px_20px_rgba(15,23,42,0.20)]"
                  : "text-slate-800 hover:bg-white hover:text-slate-950"
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
            href={item.href}
            aria-current={active ? "page" : undefined}
            aria-label={item.label}
            className={`flex min-h-12 min-w-0 items-center justify-center rounded-2xl px-2 py-2 text-center text-[11px] font-bold leading-tight transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-800 focus-visible:ring-offset-2 ${
              active
                ? "bg-blue-800 text-white shadow-[0_7px_16px_rgba(30,64,175,0.28)]"
                : "text-slate-900 hover:bg-white"
            }`}
          >
            {item.shortLabel}
          </Link>
        );
      })}
    </nav>
  );
}
