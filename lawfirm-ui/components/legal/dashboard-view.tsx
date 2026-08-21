"use client"

import { CaseRow } from "@/components/legal/case-row"
import type { LegalCase } from "@/lib/legal-data"
import { cn } from "@/lib/utils"
import { FileInput, ShieldAlert, UserCheck, CircleCheckBig, ArrowUpRight } from "lucide-react"

function Stat({
  label,
  value,
  sub,
  icon: Icon,
  tone,
}: {
  label: string
  value: string | number
  sub: string
  icon: typeof FileInput
  tone: "primary" | "warning" | "danger" | "success"
}) {
  const toneMap = {
    primary: "bg-info-muted text-info",
    warning: "bg-warning-muted text-warning-foreground",
    danger: "bg-danger-muted text-danger",
    success: "bg-success-muted text-success",
  }
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="flex items-center justify-between">
        <span className={cn("flex size-9 items-center justify-center rounded-lg", toneMap[tone])}>
          <Icon className="size-5" />
        </span>
        <ArrowUpRight className="size-4 text-muted-foreground/50" />
      </div>
      <p className="mt-4 font-mono text-3xl font-semibold tabular-nums text-foreground">{value}</p>
      <p className="text-sm font-medium text-foreground">{label}</p>
      <p className="mt-0.5 text-xs text-muted-foreground">{sub}</p>
    </div>
  )
}

export function DashboardView({
  cases,
  onOpen,
}: {
  cases: LegalCase[]
  onOpen: (id: string) => void
}) {
  const pending = cases.filter((c) => c.status === "pending")
  const conflicts = cases.filter((c) => c.conflictFlag && c.status === "pending")
  const cleared = cases.filter((c) => c.status === "approved" || c.status === "override")

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Cases in intake" value={cases.length} sub="Across all practice areas" icon={FileInput} tone="primary" />
        <Stat label="Awaiting review" value={pending.length} sub="Human-in-the-loop queue" icon={UserCheck} tone="warning" />
        <Stat label="Conflict flags" value={conflicts.length} sub="Require clearance" icon={ShieldAlert} tone="danger" />
        <Stat label="Cleared today" value={cleared.length} sub="Approved or overridden" icon={CircleCheckBig} tone="success" />
      </div>

      <section aria-labelledby="queue-heading" className="rounded-xl border border-border bg-card">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div>
            <h2 id="queue-heading" className="text-sm font-semibold text-foreground">
              HITL Approval Queue
            </h2>
            <p className="text-xs text-muted-foreground">Pending cases waiting for human review</p>
          </div>
          <span className="rounded-full bg-warning-muted px-2.5 py-1 text-xs font-semibold text-warning-foreground">
            {pending.length} pending
          </span>
        </div>
        <div className="space-y-2 p-3">
          {pending.length === 0 ? (
            <EmptyQueue />
          ) : (
            pending.map((c) => <CaseRow key={c.id} legalCase={c} onOpen={onOpen} />)
          )}
        </div>
      </section>

      <section aria-labelledby="recent-heading" className="rounded-xl border border-border bg-card">
        <div className="border-b border-border px-5 py-4">
          <h2 id="recent-heading" className="text-sm font-semibold text-foreground">
            Recently Decided
          </h2>
          <p className="text-xs text-muted-foreground">Cases with a recorded human decision</p>
        </div>
        <div className="space-y-2 p-3">
          {cases.filter((c) => c.status !== "pending").length === 0 ? (
            <p className="px-2 py-6 text-center text-sm text-muted-foreground">No decisions recorded yet.</p>
          ) : (
            cases
              .filter((c) => c.status !== "pending")
              .map((c) => <CaseRow key={c.id} legalCase={c} onOpen={onOpen} />)
          )}
        </div>
      </section>
    </div>
  )
}

function EmptyQueue() {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-4 py-12 text-center">
      <span className="flex size-11 items-center justify-center rounded-full bg-success-muted text-success">
        <CircleCheckBig className="size-5" />
      </span>
      <p className="text-sm font-medium text-foreground">Queue is clear</p>
      <p className="text-xs text-muted-foreground">All cases have been reviewed by a human.</p>
    </div>
  )
}
