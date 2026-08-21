import { cn } from "@/lib/utils"
import type { CaseStatus, RiskLevel } from "@/lib/legal-data"

const statusConfig: Record<CaseStatus, { label: string; className: string }> = {
  pending: {
    label: "Pending Review",
    className: "bg-warning-muted text-warning-foreground ring-1 ring-warning/30",
  },
  approved: {
    label: "Approved",
    className: "bg-success-muted text-success ring-1 ring-success/30",
  },
  rejected: {
    label: "Rejected",
    className: "bg-danger-muted text-danger ring-1 ring-danger/30",
  },
  override: {
    label: "Conflict Overridden",
    className: "bg-info-muted text-info ring-1 ring-info/30",
  },
}

export function StatusBadge({ status, className }: { status: CaseStatus; className?: string }) {
  const cfg = statusConfig[status]
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
        cfg.className,
        className,
      )}
    >
      <span className="size-1.5 rounded-full bg-current opacity-70" aria-hidden />
      {cfg.label}
    </span>
  )
}

const riskConfig: Record<RiskLevel, { label: string; className: string }> = {
  low: { label: "Low", className: "bg-success-muted text-success" },
  medium: { label: "Medium", className: "bg-warning-muted text-warning-foreground" },
  high: { label: "High", className: "bg-danger-muted text-danger" },
}

export function RiskTag({ risk, className }: { risk: RiskLevel; className?: string }) {
  const cfg = riskConfig[risk]
  return (
    <span
      className={cn(
        "inline-flex items-center rounded px-1.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide",
        cfg.className,
        className,
      )}
    >
      {cfg.label} risk
    </span>
  )
}

function riskColor(score: number) {
  if (score >= 70) return "text-danger"
  if (score >= 40) return "text-warning-foreground"
  return "text-success"
}

function riskBar(score: number) {
  if (score >= 70) return "bg-danger"
  if (score >= 40) return "bg-warning"
  return "bg-success"
}

export function ScoreBar({
  label,
  value,
  variant = "confidence",
}: {
  label: string
  value: number
  variant?: "confidence" | "risk"
}) {
  const barColor = variant === "risk" ? riskBar(value) : "bg-primary"
  const valueColor = variant === "risk" ? riskColor(value) : "text-foreground"
  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between">
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
        <span className={cn("font-mono text-sm font-semibold tabular-nums", valueColor)}>{value}%</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div className={cn("h-full rounded-full transition-all", barColor)} style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}

function riskStroke(score: number) {
  if (score >= 70) return "stroke-danger"
  if (score >= 40) return "stroke-warning"
  return "stroke-success"
}

export function ScoreRing({ value, variant = "risk" }: { value: number; variant?: "risk" | "confidence" }) {
  const strokeClass = variant === "risk" ? riskStroke(value) : "stroke-primary"
  const circumference = 2 * Math.PI * 20
  const offset = circumference - (value / 100) * circumference
  return (
    <div className="relative inline-flex size-14 items-center justify-center">
      <svg className="size-14 -rotate-90" viewBox="0 0 48 48">
        <circle cx="24" cy="24" r="20" fill="none" strokeWidth="4" className="stroke-muted" />
        <circle
          cx="24"
          cy="24"
          r="20"
          fill="none"
          strokeWidth="4"
          strokeLinecap="round"
          className={cn("transition-all", strokeClass)}
          style={{ strokeDasharray: circumference, strokeDashoffset: offset }}
        />
      </svg>
      <span className={cn("absolute font-mono text-sm font-bold tabular-nums", riskColor(value))}>{value}</span>
    </div>
  )
}
