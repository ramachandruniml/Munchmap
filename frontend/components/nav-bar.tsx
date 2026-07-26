"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const LINKS = [
  { href: "/plan", label: "Meal Plan" },
  { href: "/pantry", label: "Pantry" },
  { href: "/recipes", label: "Discover Recipes" },
];

export function NavBar() {
  const pathname = usePathname();

  return (
    <nav className="flex items-center justify-between gap-4 border-b border-border bg-card px-6 py-3">
      <Link href="/plan" className="font-heading text-lg font-bold text-foreground">
        Munchmap
      </Link>
      <div className="flex items-center gap-2">
        {LINKS.map((link) => {
          const active = pathname === link.href || pathname?.startsWith(`${link.href}/`);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-foreground hover:bg-muted",
              )}
            >
              {link.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
