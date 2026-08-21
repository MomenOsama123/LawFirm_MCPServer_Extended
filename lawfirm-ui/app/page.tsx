"use client"

import { useDeferredValue, useEffect, useMemo, useRef, useState } from "react"
import { Sidebar, type ViewKey } from "@/components/legal/sidebar"
import { DashboardView } from "@/components/legal/dashboard-view"
import { IntakeView, ConflictsView, AssignmentView, LogsView } from "@/components/legal/views"
import { CaseDetailModal } from "@/components/legal/case-detail-modal"
import {
  initialCases,
  initialLogs,
  type CaseStatus,
  type LegalCase,
  type SystemLogEntry,
} from "@/lib/legal-data"
import { Search, X } from "lucide-react"
import { callMcpTool } from "@/lib/mcp-client"
import { UserProfileModal } from "@/components/legal/user-profile-modal"

const viewTitles: Record<ViewKey, string> = {
  dashboard: "Operations Dashboard",
  intake: "Case Intake",
  conflicts: "Conflict Clearance",
  assignment: "Lawyer Assignment",
  logs: "System Logs",
}

const actionVerb: Record<Exclude<CaseStatus, "pending">, string> = {
  approved: "Approved assignment",
  rejected: "Rejected matter",
  override: "Overrode conflict flag",
}

const fallbackUsers = [
  { staff_id: "staff-001", full_name: "Mona Adel", role: "receptionist", email: "mona@lawfirm.eg", active: 1 },
  { staff_id: "staff-002", full_name: "Nourhan Samir", role: "senior_associate", email: "nourhan@lawfirm.eg", active: 1 },
  { staff_id: "staff-003", full_name: "Karim El-Sayed", role: "partner", email: "karim@lawfirm.eg", active: 1 },
  { staff_id: "staff-004", full_name: "Laila Mostafa", role: "admin", email: "laila@lawfirm.eg", active: 1 },
]

function roleLabel(role: string) {
  return role === "receptionist" ? "Normal user" : role.replaceAll("_", " ")
}

export default function Page() {
  const [view, setView] = useState<ViewKey>("dashboard")
  const [cases, setCases] = useState<LegalCase[]>(initialCases)
  const [logs, setLogs] = useState<SystemLogEntry[]>(initialLogs)
  const [openId, setOpenId] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)
  const [actionMessage, setActionMessage] = useState<string | null>(null)
  type StaffUser = { staff_id: string; full_name: string; role: string; email?: string; active?: number }
  const [users, setUsers] = useState<StaffUser[]>(fallbackUsers)
  const [user, setUser] = useState<StaffUser | null>(fallbackUsers[2])
  const [userOpen, setUserOpen] = useState(false)
  const [query, setQuery] = useState("")
  const searchRef = useRef<HTMLInputElement>(null)
  const deferredQuery = useDeferredValue(query)

  useEffect(() => {
    callMcpTool<StaffUser[]>("list_staff", {})
      .then((result) => {
        setUsers(result.data)
        const selectedId = window.localStorage.getItem("lexordia-staff-id") ?? "staff-003"
        setUser(result.data.find((staffUser) => staffUser.staff_id === selectedId) ?? result.data[0] ?? null)
      })
      .catch(() => undefined)
  }, [])

  function handleUserSelect(staffId: string) {
    const selectedUser = users.find((staffUser) => staffUser.staff_id === staffId)
    if (!selectedUser) return
    window.localStorage.setItem("lexordia-staff-id", staffId)
    setUser(selectedUser)
    setUserOpen(false)
  }

  async function handleCreateUser(newUser: Omit<StaffUser, "active">) {
    const result = await callMcpTool<{ success?: boolean; error?: string }>("create_staff", newUser)
    if (result.data.success === false) throw new Error(result.data.error ?? "Could not create user")
    const createdUser = { ...newUser, active: 1 }
    setUsers((previous) => [...previous, createdUser])
    setUser(createdUser)
    window.localStorage.setItem("lexordia-staff-id", createdUser.staff_id)
  }

  const pendingCount = useMemo(
    () => cases.filter((c) => c.conflictFlag && c.status === "pending").length,
    [cases],
  )

  const openCase = cases.find((c) => c.id === openId) ?? null
  const canDecide = user?.role !== "receptionist"

  const visibleCases = useMemo(() => {
    const normalizedQuery = deferredQuery.trim().toLowerCase()
    if (!normalizedQuery) return cases

    return cases.filter((c) =>
      [c.id, c.title, c.client, c.practiceArea, c.suggestedLawyer, c.matterType]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery),
    )
  }, [cases, deferredQuery])

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "/" && document.activeElement?.tagName !== "INPUT") {
        event.preventDefault()
        searchRef.current?.focus()
      }
    }
    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
  }, [])

  async function handleAction(id: string, status: CaseStatus) {
    if (status === "pending" || !canDecide) return
    const target = cases.find((c) => c.id === id)
    if (!target || busyId) return
    const tool = status === "rejected" ? "reject_case" : "accept_case"
    setBusyId(id)
    setActionMessage(null)
    try {
      const result = await callMcpTool<{ success?: boolean; error?: string }>(tool, {
        case_id: target.backendCaseId,
        decided_by: user.staff_id,
        decision_reason: status === "override" ? "Conflict overridden after human review." : "Decision recorded from Lexordia review queue.",
      })
      if (result.data?.success === false) throw new Error(result.data.error ?? "MCP decision failed")
      setActionMessage(`${actionVerb[status]} for ${target.title}`)
    } catch (error) {
      setActionMessage(error instanceof Error ? error.message : "MCP decision failed")
      setLogs((prev) => [
        {
          id: `log-${Date.now()}`,
          time: new Date().toTimeString().slice(0, 8),
          actor: "Lexordia UI",
          action: `MCP decision failed — ${error instanceof Error ? error.message : "Unknown error"}`,
          target: id,
          level: "danger",
        },
        ...prev,
      ])
      return
    } finally {
      setBusyId(null)
    }

    setCases((prev) => prev.map((c) => (c.id === id ? { ...c, status } : c)))
    {
      const now = new Date()
      const time = now.toTimeString().slice(0, 8)
      setLogs((prev) => [
        {
          id: `log-${Date.now()}`,
          time,
          actor: "A. Reyes",
          action: `${actionVerb[status]}${target ? ` — ${target.title}` : ""}`,
          target: id,
          level: status === "approved" ? "success" : status === "rejected" ? "danger" : "info",
        },
        ...prev,
      ])
    }
  }

  return (
    <div className="flex h-dvh overflow-hidden bg-background">
      <Sidebar active={view} onNavigate={setView} pendingCount={pendingCount} user={user} role={user?.role ?? "receptionist"} onOpenUser={() => setUserOpen(true)} />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-card px-4 py-4 sm:flex-nowrap sm:gap-4 sm:px-6">
          <div>
            <h1 className="text-base font-semibold text-foreground">{viewTitles[view]}</h1>
            <p className="text-xs text-muted-foreground">
              {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
            </p>
          </div>
          <div className="flex w-full items-center gap-3 sm:w-auto">
            <div className="flex min-w-0 flex-1 items-center gap-2 rounded-md border border-border bg-background px-3 py-1.5 text-sm text-muted-foreground transition-colors focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/20 sm:w-64 sm:flex-none">
              <Search className="size-4" />
              <input
                ref={searchRef}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search matters"
                aria-label="Search matters"
                className="min-w-0 flex-1 bg-transparent outline-none placeholder:text-muted-foreground"
              />
              {query ? (
                <button type="button" onClick={() => setQuery("")} aria-label="Clear search">
                  <X className="size-3.5" />
                </button>
              ) : (
                <kbd className="rounded border border-border bg-muted px-1.5 py-0.5 font-mono text-[11px]">/</kbd>
              )}
            </div>
            <span className="inline-flex items-center gap-2 rounded-full bg-success-muted px-3 py-1.5 text-xs font-medium text-success">
              <span className="size-1.5 rounded-full bg-success" aria-hidden />
              {user ? `${roleLabel(user.role)} · AI agents online` : "AI agents online"}
            </span>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto px-4 py-5 transition-colors sm:px-6 sm:py-6">
          <div className="mx-auto max-w-5xl">
            {query && (
              <p className="mb-4 text-xs text-muted-foreground" aria-live="polite">
                Showing {visibleCases.length} of {cases.length} matters for “{query}”
              </p>
            )}
            {actionMessage && (
              <p className="mb-4 rounded-md border border-info/30 bg-info-muted px-3 py-2 text-sm text-info" role="status">
                {actionMessage}
              </p>
            )}
            {view === "dashboard" && <DashboardView cases={visibleCases} onOpen={setOpenId} />}
            {view === "intake" && <IntakeView cases={visibleCases} onOpen={setOpenId} />}
            {view === "conflicts" && (
              <ConflictsView cases={visibleCases} onOpen={setOpenId} onAction={handleAction} />
            )}
            {view === "assignment" && (
              <AssignmentView cases={visibleCases} onOpen={setOpenId} onAction={handleAction} />
            )}
            {view === "logs" && <LogsView logs={logs} />}
          </div>
        </main>
      </div>

      <CaseDetailModal legalCase={openCase} busy={openCase?.id === busyId} canDecide={canDecide} onClose={() => setOpenId(null)} onAction={handleAction} />
      {userOpen && <UserProfileModal user={user} users={users} onSelect={handleUserSelect} onCreate={handleCreateUser} onClose={() => setUserOpen(false)} />}
    </div>
  )
}
