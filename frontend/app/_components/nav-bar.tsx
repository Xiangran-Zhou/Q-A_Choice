"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { href: "/rag", label: "RAG" },
  { href: "/agentic", label: "Agentic" },
  { href: "/graphrag", label: "GraphRAG" },
  { href: "/compare", label: "Side-by-side" },
  { href: "/matrix", label: "Decision matrix" },
] as const;

export default function NavBar() {
  const pathname = usePathname();

  return (
    <header className="border-b border-foreground/10">
      <div className="mx-auto flex w-full max-w-5xl items-center gap-6 px-6 py-3">
        <Link href="/" className="font-semibold tracking-tight">
          Q&amp;A Paradigm Lab
        </Link>
        <nav className="flex gap-1 text-sm">
          {tabs.map((tab) => {
            const active = pathname === tab.href;
            return (
              <Link
                key={tab.href}
                href={tab.href}
                aria-current={active ? "page" : undefined}
                className={
                  "rounded-md px-3 py-1.5 transition-colors " +
                  (active
                    ? "bg-foreground/10 font-medium"
                    : "text-foreground/70 hover:bg-foreground/5")
                }
              >
                {tab.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
