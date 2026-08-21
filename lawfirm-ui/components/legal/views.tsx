"use client"

import { CaseRow } from "@/components/legal/case-row"
import { RiskTag } from "@/components/legal/primitives"
import { Button } from "@/components/ui/button"
import type { CaseStatus, LegalCase, SystemLogEntry } from "@/lib/legal-data"
import { cn } from "@/lib/utils"
import { ShieldAlert, ShieldCheck, TriangleAlert, CircleCheckBig, CircleX, UserCheck, ScrollText } from "lucide-react"

function ViewHeader({ title, description }: { title: string; description: string }) {
  return (
    <div className="mb-5">
      <h1 className="text-lg font-semibold text-foreground">{title}</h1>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  )
}

export function IntakeView({ cases, onOpen }: { cases: LegalCase[]; onOpen: (id: string) => void }) {
  return (
    <div>
      <ViewHeader title="Case Intake" description="All matters ingested by the AI intake agent, newest first." />
      <div className="rounded-xl border border-border bg-card">
        <div className="hidden items-center gap-4 border-b border-border px-4 py-2.5 text-xs font-medium uppercase tracking-wide text-muted-foreground md:flex">
          <span className="flex-1">Matter</span>
          <span className="w-32">Suggested</span>
          <span className="w-24">Risk</span>
          <span className="w-36">Status</span>
          <span className="w-4" />
        </div>
        <div className="space-y-2 p-3">
          {cases.map((c) => (
            <CaseRow key={c.id} legalCase={c} onOpen={onOpen} />
          ))}
        </div>
      </div>
    </div>
  )
}

export function ConflictsView({
  cases,
  onOpen,
  onAction,
}: {
  cases: LegalCase[]
  onOpen: (id: string) => void
  onAction: (id: string, status: CaseStatus) => void
}) {
  const flagged = cases.filter((c) => c.conflictFlag)
  return (
    <div>
      <ViewHeader
        title="Conflict Clearance"
        description="Matters with AI-detected conflicts of interest requiring human clearance."
      />
      {flagged.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-xl border border-border bg-card px-4 py-14 text-center">
          <ShieldCheck className="size-6 text-success" />
          <p className="text-sm font-medium text-foreground">No open conflicts</p>
        </div>
      ) : (
        <div className="space-y-4">
          {flagged.map((c) => (
            <div key={c.id} className="rounded-xl border border-border bg-card p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-muted-foreground">{c.id}</span>
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-danger">
                      <TriangleAlert className="size-3.5" /> Conflict flagged
                    </span>
                  </div>
                  <button
                    onClick={() => onOpen(c.id)}
                    className="mt-0.5 text-left text-base font-semibold text-foreground hover:underline"
                  >
                    {c.title}
                  </button>
                  <p className="text-sm text-muted-foreground">{c.client}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded-md bg-danger-muted px-2 py-1 text-xs font-semibold text-danger">
                    Risk {c.riskScore}
                  </span>
                </div>
              </div>

              <div className="mt-4 space-y-2">
                {c.conflicts.map((h, i) => (
                  <div key={i} className="flex items-start justify-between gap-4 rounded-lg border border-border bg-muted/40 px-3 py-2.5">
                    <div>
                      <p className="text-sm font-medium text-foreground">{h.party}</p>
                      <p className="text-xs text-muted-foreground">{h.relation}</p>
                    </div>
                    <RiskTag risk={h.severity} />
                  </div>
                ))}
              </div>

              <div className="mt-4 flex flex-wrap items-center justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => onAction(c.id, "rejected")}
                  disabled={c.status === "rejected"}
                  className="gap-1.5 border-danger/30 text-danger hover:bg-danger-muted hover:text-danger"
                >
                  <CircleX className="size-4" /> Reject
                </Button>
                <Button
                  variant="outline"
                  onClick={() => onAction(c.id, "override")}
                  disabled={c.status === "override"}
                  className="gap-1.5 border-info/30 text-info hover:bg-info-muted hover:text-info"
                >
                  <ShieldAlert className="size-4" /> Override Conflict
                </Button>
                <Button
                  onClick={() => onAction(c.id, "approved")}
                  disabled={c.status === "approved"}
                  className="gap-1.5 bg-success text-success-foreground hover:bg-success/90"
                >
                  <CircleCheckBig className="size-4" /> Approve
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function AssignmentView({
  cases,
  onOpen,
  onAction,
}: {
  cases: LegalCase[]
  onOpen: (id: string) => void
  onAction: (id: string, status: CaseStatus) => void
}) {
  return (
    <div>
      <ViewHeader
        title="Lawyer Assignment"
        description="AI-recommended lawyer assignments awaiting approval or already confirmed."
      />
      <div className="grid gap-4 lg:grid-cols-2">
        {cases.map((c) => (
          <div key={c.id} className="flex flex-col rounded-xl border border-border bg-card p-5">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <span className="font-mono text-xs text-muted-foreground">{c.id}</span>
                <button
                  onClick={() => onOpen(c.id)}
                  className="block text-left text-sm font-semibold text-foreground hover:underline"
                >
                  {c.title}
                </button>
              </div>
              <span className="font-mono text-xs font-semibold tabular-nums text-muted-foreground">
                {c.aiConfidence}% conf.
              </span>
            </div>

            <div className="mt-4 flex items-center gap-3 rounded-lg border border-border bg-muted/40 p-3">
              <span className="flex size-9 items-center justify-center rounded-full bg-info-muted text-sm font-semibold text-info">
                {c.suggestedLawyer.split(" ").map((n) => n[0]).join("")}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">{c.suggestedLawyer}</p>
                <p className="truncate text-xs text-muted-foreground">{c.suggestedLawyerRole}</p>
              </div>
              <UserCheck className="size-4 text-muted-foreground" />
            </div>

            <div className="mt-4 flex items-center justify-between gap-2">
              <span className={cn("inline-flex items-center gap-1.5 text-xs font-medium", c.conflictFlag ? "text-danger" : "text-success")}>
                {c.conflictFlag ? <TriangleAlert className="size-3.5" /> : <ShieldCheck className="size-3.5" />}
                {c.conflictFlag ? "Conflict pending" : "Conflict clear"}
              </span>
              <Button
                size="sm"
                onClick={() => onAction(c.id, "approved")}
                disabled={c.status === "approved" || c.status === "rejected"}
                className="gap-1.5 bg-success text-success-foreground hover:bg-success/90"
              >
                <CircleCheckBig className="size-4" />
                {c.status === "approved" ? "Assigned" : "Approve Assignment"}
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

const logTone: Record<SystemLogEntry["level"], string> = {
  info: "bg-info",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
}

export function LogsView({ logs }: { logs: SystemLogEntry[] }) {
  return (
    <div>
      <ViewHeader title="System Logs" description="Immutable audit trail of AI and human actions." />
      <div className="rounded-xl border border-border bg-card">
        <div className="flex items-center gap-2 border-b border-border px-5 py-3">
          <ScrollText className="size-4 text-muted-foreground" />
          <p className="text-sm font-medium text-foreground">Activity stream</p>
        </div>
        <ol className="divide-y divide-border">
          {logs.map((log) => (
            <li key={log.id} className="flex items-start gap-3 px-5 py-3">
              <span className={cn("mt-1.5 size-2 shrink-0 rounded-full", logTone[log.level])} aria-hidden />
              <div className="min-w-0 flex-1">
                <p className="text-sm text-foreground">
                  <span className="font-medium">{log.actor}</span> {log.action}
                </p>
                <p className="text-xs text-muted-foreground">
                  <span className="font-mono">{log.target}</span>
                </p>
              </div>
              <time className="shrink-0 font-mono text-xs text-muted-foreground tabular-nums">{log.time}</time>
            </li>
          ))}
        </ol>
      </div>
    </div>
  )
}
