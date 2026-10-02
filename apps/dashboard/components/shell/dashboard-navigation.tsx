"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  { href: "/", label: "Overview" },
  { href: "/vehicle", label: "Vehicle Intelligence" },
  { href: "/market", label: "Market Intelligence" },
  { href: "/methodology", label: "Data & Methodology" },
];

export function DashboardNavigation({
  variant,
}: {
  variant: "desktop" | "mobile";
}) {
  const pathname = usePathname();

  if (variant === "desktop") {
    return (
      <nav aria-label="Primary dashboard navigation" className="space-y-1.5">
        {navigation.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={`flex min-h-11 items-center rounded-xl px-3 py-2.5 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-300 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 ${
                active
                  ? "border border-white/20 bg-white/16 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.14)]"
                  : "border border-transparent text-slate-300 hover:border-white/10 hover:bg-white/10 hover:text-white"
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
      className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
    >
      {navigation.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={`inline-flex min-h-11 shrink-0 items-center whitespace-nowrap rounded-full border px-4 py-2 text-xs font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-700 focus-visible:ring-offset-2 ${
              active
                ? "border-blue-700 bg-blue-700 text-white shadow-sm"
                : "border-white/70 bg-white/70 text-slate-700 hover:bg-white"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
