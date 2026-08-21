"use client"

import { useState } from "react"
import { Mail, ShieldCheck, X } from "lucide-react"

type StaffUser = { staff_id: string; full_name: string; role: string; email?: string; active?: number }

function roleLabel(role: string) {
  return role === "receptionist" ? "Normal user" : role.replaceAll("_", " ")
}

export function UserProfileModal({ user, users, onSelect, onCreate, onClose }: { user: StaffUser | null; users: StaffUser[]; onSelect: (staffId: string) => void; onCreate: (user: Omit<StaffUser, "active">) => Promise<void>; onClose: () => void }) {
  const [form, setForm] = useState({ staff_id: "", full_name: "", role: "admin", email: "" })
  const [creating, setCreating] = useState(false)
  if (!user) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button className="absolute inset-0 bg-foreground/40 backdrop-blur-sm" onClick={onClose} aria-label="Close user profile" />
      <section role="dialog" aria-modal="true" aria-labelledby="user-profile-title" className="relative w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-2xl">
        <button onClick={onClose} aria-label="Close" className="absolute right-4 top-4 rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"><X className="size-5" /></button>
        <div className="flex items-center gap-4">
          <div className="flex size-14 items-center justify-center rounded-full bg-info-muted text-lg font-semibold text-info">{user.full_name.split(" ").map((name) => name[0]).join("").slice(0, 2)}</div>
          <div><h2 id="user-profile-title" className="text-lg font-semibold text-foreground">{user.full_name}</h2><p className="text-sm capitalize text-muted-foreground">{roleLabel(user.role)}</p></div>
        </div>
        <dl className="mt-6 space-y-4 text-sm">
          <div className="flex items-center gap-3"><ShieldCheck className="size-4 text-success" /><div><dt className="text-xs text-muted-foreground">Staff ID</dt><dd className="font-mono text-foreground">{user.staff_id}</dd></div></div>
          {user.email && <div className="flex items-center gap-3"><Mail className="size-4 text-muted-foreground" /><div><dt className="text-xs text-muted-foreground">Email</dt><dd className="text-foreground">{user.email}</dd></div></div>}
          <div><dt className="text-xs text-muted-foreground">Account status</dt><dd className="font-medium text-success">{user.active ? "Active" : "Inactive"}</dd></div>
        </dl>
        <label className="mt-6 block text-xs font-medium text-muted-foreground" htmlFor="active-user">Switch active user</label>
        <select id="active-user" value={user.staff_id} onChange={(event) => onSelect(event.target.value)} className="mt-1.5 w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-ring focus:ring-2 focus:ring-ring/20">
          {users.map((staffUser) => <option key={staffUser.staff_id} value={staffUser.staff_id}>{staffUser.full_name} · {roleLabel(staffUser.role)}</option>)}
        </select>
        <div className="mt-6 border-t border-border pt-5">
          <p className="text-sm font-medium text-foreground">Add staff user</p>
          <div className="mt-3 grid gap-2">
            {(["staff_id", "full_name", "email"] as const).map((field) => <input key={field} value={form[field]} onChange={(event) => setForm({ ...form, [field]: event.target.value })} placeholder={field.replace("_", " ")} className="rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-ring" />)}
            <select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })} className="rounded-md border border-border bg-background px-3 py-2 text-sm">
              <option value="admin">Admin</option><option value="partner">Partner</option><option value="senior_associate">Senior associate</option><option value="receptionist">Normal user</option>
            </select>
            <button type="button" disabled={creating} onClick={async () => { setCreating(true); try { await onCreate(form); setForm({ staff_id: "", full_name: "", role: "admin", email: "" }) } finally { setCreating(false) } }} className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50">{creating ? "Adding..." : "Add user"}</button>
          </div>
        </div>
      </section>
    </div>
  )
}