"use client"

import { cn } from "@/lib/utils"
import { Scale, LayoutDashboard, FileInput, ShieldAlert, UserCheck, ScrollText } from "lucide-react"

export type ViewKey = "dashboard" | "intake" | "conflicts" | "assignment" | "logs"

const nav: { key: ViewKey; label: string; icon: typeof LayoutDashboard }[] = [
  { key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { key: "intake", label: "Case Intake", icon: FileInput },
  { key: "conflicts", label: "Conflict Clearance", icon: ShieldAlert },
  { key: "assignment", label: "Lawyer Assignment", icon: UserCheck },
  { key: "logs", label: "System Logs", icon: ScrollText },
]

export function Sidebar({
  active,
  onNavigate,
  pendingCount,
}: {
  active: ViewKey
  onNavigate: (v: ViewKey) => void
  pendingCount: number
}) {
  return (
    <aside className="flex w-16 shrink-0 flex-col bg-sidebar text-sidebar-foreground transition-[width] md:w-64">
      <div className="flex items-center justify-center gap-2.5 px-3 py-5 md:justify-start md:px-5">
        <div className="flex size-9 items-center justify-center rounded-md bg-sidebar-primary text-sidebar-primary-foreground">
          <Scale className="size-5" />
        </div>
        <div className="hidden leading-tight md:block">
          <p className="text-sm font-semibold text-sidebar-accent-foreground">Lexordia</p>
          <p className="text-xs text-sidebar-foreground/70">Law Firm AI Platform</p>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-3 py-2" aria-label="Primary">
        <p className="hidden px-2 pb-1 pt-3 text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/50 md:block">
          Workflow
        </p>
        {nav.map(({ key, label, icon: Icon }) => {
          const isActive = active === key
          return (
            <button
              key={key}
              onClick={() => onNavigate(key)}
              title={label}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "group flex items-center justify-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors md:justify-start",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
              )}
            >
              <Icon className={cn("size-4 shrink-0", isActive ? "text-sidebar-primary" : "opacity-80")} />
              <span className="hidden flex-1 text-left md:block">{label}</span>
              {key === "conflicts" && pendingCount > 0 && (
                <span className="rounded-full bg-warning px-1.5 py-0.5 text-[11px] font-bold tabular-nums text-warning-foreground">
                  {pendingCount}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      <div className="mt-auto border-t border-sidebar-border px-2 py-4 md:px-4">
        <div className="flex items-center gap-3">
          <div className="flex size-9 items-center justify-center rounded-full bg-sidebar-accent text-sm font-semibold text-sidebar-accent-foreground">
            AR
          </div>
          <div className="hidden min-w-0 leading-tight md:block">
            <p className="truncate text-sm font-medium text-sidebar-accent-foreground">A. Reyes</p>
            <p className="truncate text-xs text-sidebar-foreground/60">Intake Supervisor</p>
          </div>
        </div>
      </div>
    </aside>
  )
}
