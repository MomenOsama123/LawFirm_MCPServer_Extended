"use client"

import { StatusBadge } from "@/components/legal/primitives"
import type { LegalCase } from "@/lib/legal-data"
import { cn } from "@/lib/utils"
import { ChevronRight, TriangleAlert } from "lucide-react"

function riskDot(score: number) {
  if (score >= 70) return "bg-danger"
  if (score >= 40) return "bg-warning"
  return "bg-success"
}

export function CaseRow({ legalCase: c, onOpen }: { legalCase: LegalCase; onOpen: (id: string) => void }) {
  return (
    <button
      onClick={() => onOpen(c.id)}
      className="group flex w-full items-center gap-4 rounded-lg border border-border bg-card px-4 py-3.5 text-left transition-colors hover:border-ring/40 hover:bg-accent/40"
    >
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-muted-foreground">{c.id}</span>
          {c.conflictFlag && (
            <span className="inline-flex items-center gap-1 text-xs font-medium text-danger">
              <TriangleAlert className="size-3.5" />
              Conflict
            </span>
          )}
        </div>
        <p className="truncate text-sm font-semibold text-foreground">{c.title}</p>
        <p className="truncate text-xs text-muted-foreground">
          {c.client} · {c.practiceArea} · {c.value}
        </p>
      </div>

      <div className="hidden w-32 shrink-0 md:block">
        <p className="text-xs text-muted-foreground">Suggested</p>
        <p className="truncate text-sm font-medium text-foreground">{c.suggestedLawyer}</p>
      </div>

      <div className="hidden w-24 shrink-0 items-center gap-2 sm:flex">
        <span className={cn("size-2 rounded-full", riskDot(c.riskScore))} aria-hidden />
        <span className="font-mono text-sm font-semibold tabular-nums text-foreground">{c.riskScore}</span>
        <span className="text-xs text-muted-foreground">risk</span>
      </div>

      <div className="w-36 shrink-0">
        <StatusBadge status={c.status} />
      </div>

      <ChevronRight className="size-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
    </button>
  )
}
