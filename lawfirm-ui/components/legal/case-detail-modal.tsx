"use client"

import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { StatusBadge, RiskTag, ScoreBar, ScoreRing } from "@/components/legal/primitives"
import type { CaseStatus, LegalCase } from "@/lib/legal-data"
import { cn } from "@/lib/utils"
import { X, CircleCheckBig, CircleX, ShieldAlert, FileText, Users, TriangleAlert, Gavel } from "lucide-react"

export function CaseDetailModal({
  legalCase,
  busy = false,
  onClose,
  onAction,
}: {
  legalCase: LegalCase | null
  busy?: boolean
  onClose: () => void
  onAction: (id: string, status: CaseStatus) => void
}) {
  useEffect(() => {
    if (!legalCase) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", onKey)
    document.body.style.overflow = "hidden"
    return () => {
      window.removeEventListener("keydown", onKey)
      document.body.style.overflow = ""
    }
  }, [legalCase, onClose])

  if (!legalCase) return null

  const c = legalCase
  const decided = c.status !== "pending"

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center sm:p-4">
      <div
        className="absolute inset-0 bg-foreground/40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="case-modal-title"
        className="relative flex max-h-[92vh] w-full flex-col overflow-hidden rounded-t-2xl border border-border bg-card shadow-2xl sm:max-w-3xl sm:rounded-2xl"
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-border bg-card px-6 py-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-medium text-muted-foreground">{c.id}</span>
              <StatusBadge status={c.status} />
            </div>
            <h2 id="case-modal-title" className="mt-1 text-lg font-semibold text-balance text-foreground">
              {c.title}
            </h2>
            <p className="text-sm text-muted-foreground">
              {c.client} · {c.matterType}
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <X className="size-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {c.conflictFlag && (
            <div className="mb-5 flex items-start gap-3 rounded-lg border border-danger/30 bg-danger-muted px-4 py-3">
              <TriangleAlert className="mt-0.5 size-5 shrink-0 text-danger" />
              <div>
                <p className="text-sm font-semibold text-danger">Conflict of Interest flagged</p>
                <p className="text-sm text-danger/90">
                  AI detected potential adverse-party relationships. Human review required before assignment.
                </p>
              </div>
            </div>
          )}

          {/* Metadata + scores */}
          <div className="grid gap-5 sm:grid-cols-3">
            <div className="sm:col-span-2">
              <SectionLabel icon={FileText}>Case Metadata</SectionLabel>
              <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
                <Meta label="Practice Area" value={c.practiceArea} />
                <Meta label="Jurisdiction" value={c.jurisdiction} />
                <Meta label="Matter Value" value={c.value} />
                <Meta label="Received" value={c.receivedAt} mono />
                <Meta label="Suggested Lawyer" value={c.suggestedLawyer} />
                <Meta label="Role" value={c.suggestedLawyerRole} />
              </dl>
            </div>
            <div className="rounded-lg border border-border bg-muted/40 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Risk Score</p>
                  <p className="text-xs text-muted-foreground/70">AI computed</p>
                </div>
                <ScoreRing value={c.riskScore} variant="risk" />
              </div>
              <div className="mt-4">
                <ScoreBar label="AI Confidence" value={c.aiConfidence} variant="confidence" />
              </div>
            </div>
          </div>

          {/* Summary */}
          <div className="mt-6">
            <SectionLabel icon={Gavel}>AI Summary</SectionLabel>
            <p className="text-sm leading-relaxed text-foreground/90">{c.summary}</p>
          </div>

          {/* Parties */}
          <div className="mt-6">
            <SectionLabel icon={Users}>Parties</SectionLabel>
            <div className="flex flex-wrap gap-2">
              {c.parties.map((p) => (
                <span key={p} className="rounded-md border border-border bg-secondary px-2.5 py-1 text-sm text-secondary-foreground">
                  {p}
                </span>
              ))}
            </div>
          </div>

          {/* Conflicts */}
          {c.conflicts.length > 0 && (
            <div className="mt-6">
              <SectionLabel icon={ShieldAlert}>Conflict Hits</SectionLabel>
              <div className="space-y-2">
                {c.conflicts.map((h, i) => (
                  <div key={i} className="flex items-start justify-between gap-4 rounded-lg border border-border bg-card px-4 py-3">
                    <div>
                      <p className="text-sm font-medium text-foreground">{h.party}</p>
                      <p className="text-sm text-muted-foreground">{h.relation}</p>
                      <p className="mt-1 font-mono text-xs text-muted-foreground/70">Ref: {h.matter}</p>
                    </div>
                    <RiskTag risk={h.severity} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Extracted clauses */}
          {c.clauses.length > 0 && (
            <div className="mt-6">
              <SectionLabel icon={FileText}>Extracted Legal Clauses</SectionLabel>
              <div className="space-y-3">
                {c.clauses.map((cl) => (
                  <div key={cl.id} className="rounded-lg border border-border bg-card p-4">
                    <div className="mb-1.5 flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-foreground">{cl.label}</span>
                        <span className="rounded bg-muted px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground">
                          {cl.category}
                        </span>
                      </div>
                      <RiskTag risk={cl.risk} />
                    </div>
                    <p className="text-sm leading-relaxed text-foreground/80">{cl.text}</p>
                    <div className="mt-3 max-w-xs">
                      <ScoreBar label="Extraction confidence" value={cl.confidence} variant="confidence" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div className="flex flex-col gap-2 border-t border-border bg-muted/30 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs text-muted-foreground">
            {decided ? (
              <span className="inline-flex items-center gap-1.5">
                Decision recorded — <StatusBadge status={c.status} />
              </span>
            ) : (
              "Human-in-the-loop decision required."
            )}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={() => onAction(c.id, "rejected")}
              disabled={busy || c.status === "rejected"}
              className="gap-1.5 border-danger/30 text-danger hover:bg-danger-muted hover:text-danger"
            >
              <CircleX className="size-4" />
              Reject
            </Button>
            {c.conflictFlag && (
              <Button
                variant="outline"
                onClick={() => onAction(c.id, "override")}
                disabled={busy || c.status === "override"}
                className="gap-1.5 border-info/30 text-info hover:bg-info-muted hover:text-info"
              >
                <ShieldAlert className="size-4" />
                Override Conflict
              </Button>
            )}
            <Button
              onClick={() => onAction(c.id, "approved")}
              disabled={busy || c.status === "approved"}
              className="gap-1.5 bg-success text-success-foreground hover:bg-success/90"
            >
              <CircleCheckBig className="size-4" />
              {busy ? "Contacting AI agent..." : "Approve Assignment"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

function SectionLabel({ icon: Icon, children }: { icon: typeof FileText; children: React.ReactNode }) {
  return (
    <div className="mb-2.5 flex items-center gap-2">
      <Icon className="size-4 text-muted-foreground" />
      <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{children}</h3>
    </div>
  )
}

function Meta({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className={cn("mt-0.5 font-medium text-foreground", mono && "font-mono text-[13px]")}>{value}</dd>
    </div>
  )
}
