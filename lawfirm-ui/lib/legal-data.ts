export type CaseStatus = "pending" | "approved" | "rejected" | "override"

export type RiskLevel = "low" | "medium" | "high"

export interface LegalClause {
  id: string
  label: string
  text: string
  category: string
  confidence: number // 0-100
  risk: RiskLevel
}

export interface ConflictHit {
  party: string
  relation: string
  matter: string
  severity: RiskLevel
}

export interface LegalCase {
  id: string
  backendCaseId: string
  title: string
  client: string
  matterType: string
  practiceArea: string
  jurisdiction: string
  receivedAt: string
  value: string
  status: CaseStatus
  suggestedLawyer: string
  suggestedLawyerRole: string
  conflictFlag: boolean
  riskScore: number // 0-100, higher = riskier
  aiConfidence: number // 0-100
  summary: string
  parties: string[]
  clauses: LegalClause[]
  conflicts: ConflictHit[]
}

export interface SystemLogEntry {
  id: string
  time: string
  actor: string
  action: string
  target: string
  level: "info" | "success" | "warning" | "danger"
}

export const initialCases: LegalCase[] = [
  {
    id: "MAT-2041",
    backendCaseId: "case-001",
    title: "Acquisition of Northwind Robotics",
    client: "Halcyon Capital Partners",
    matterType: "M&A / Due Diligence",
    practiceArea: "Corporate",
    jurisdiction: "Delaware, US",
    receivedAt: "2026-08-21 09:12",
    value: "$42.0M",
    status: "pending",
    suggestedLawyer: "Priya Ramanathan",
    suggestedLawyerRole: "Partner, Corporate M&A",
    conflictFlag: true,
    riskScore: 78,
    aiConfidence: 91,
    summary:
      "Buy-side acquisition of a robotics manufacturer. AI flagged a potential adverse-party relationship with an existing firm client on the sell side.",
    parties: ["Halcyon Capital Partners", "Northwind Robotics Inc.", "Meridian Trust (escrow)"],
    clauses: [
      {
        id: "c1",
        label: "Indemnification Cap",
        text: "Seller's aggregate liability shall not exceed 15% of the purchase price, excluding fraud.",
        category: "Risk Allocation",
        confidence: 94,
        risk: "medium",
      },
      {
        id: "c2",
        label: "Non-Compete",
        text: "Founders agree not to compete within the robotics sector for a period of 36 months.",
        category: "Restrictive Covenant",
        confidence: 88,
        risk: "low",
      },
      {
        id: "c3",
        label: "Material Adverse Change",
        text: "Buyer may terminate upon any event materially affecting the target's financial condition.",
        category: "Termination",
        confidence: 72,
        risk: "high",
      },
    ],
    conflicts: [
      {
        party: "Northwind Robotics Inc.",
        relation: "Represented by firm in 2024 IP dispute",
        matter: "MAT-1783",
        severity: "high",
      },
    ],
  },
  {
    id: "MAT-2038",
    backendCaseId: "case-002",
    title: "Series C Financing — Lumen Health",
    client: "Lumen Health, Inc.",
    matterType: "Venture Financing",
    practiceArea: "Corporate",
    jurisdiction: "California, US",
    receivedAt: "2026-08-21 08:40",
    value: "$18.5M",
    status: "pending",
    suggestedLawyer: "Daniel Osei",
    suggestedLawyerRole: "Senior Associate, Venture",
    conflictFlag: false,
    riskScore: 34,
    aiConfidence: 96,
    summary:
      "Lead counsel for a Series C preferred stock financing. No conflicts detected across current client roster.",
    parties: ["Lumen Health, Inc.", "Everbright Ventures", "Two Rivers Fund II"],
    clauses: [
      {
        id: "c1",
        label: "Liquidation Preference",
        text: "1x non-participating preference for Series C holders.",
        category: "Economics",
        confidence: 97,
        risk: "low",
      },
      {
        id: "c2",
        label: "Anti-Dilution",
        text: "Broad-based weighted average anti-dilution protection.",
        category: "Economics",
        confidence: 93,
        risk: "low",
      },
    ],
    conflicts: [],
  },
  {
    id: "MAT-2035",
    backendCaseId: "case-003",
    title: "Employment Dispute — Kessler v. Vantage",
    client: "Vantage Logistics LLC",
    matterType: "Litigation",
    practiceArea: "Employment",
    jurisdiction: "New York, US",
    receivedAt: "2026-08-20 16:55",
    value: "$1.2M exposure",
    status: "pending",
    suggestedLawyer: "Amara Njoku",
    suggestedLawyerRole: "Partner, Employment Litigation",
    conflictFlag: true,
    riskScore: 61,
    aiConfidence: 84,
    summary:
      "Defense of a wrongful termination and retaliation claim. Possible positional conflict with a concurrent plaintiff-side engagement.",
    parties: ["Vantage Logistics LLC", "Robert Kessler (plaintiff)"],
    clauses: [
      {
        id: "c1",
        label: "Arbitration Clause",
        text: "All employment disputes subject to binding arbitration under AAA rules.",
        category: "Dispute Resolution",
        confidence: 90,
        risk: "medium",
      },
    ],
    conflicts: [
      {
        party: "Positional — plaintiff-side employment matter",
        relation: "Firm currently represents plaintiffs in analogous claims",
        matter: "MAT-1990",
        severity: "medium",
      },
    ],
  },
  {
    id: "MAT-2029",
    backendCaseId: "case-004",
    title: "Commercial Lease — Harbor Tower",
    client: "Beacon Property Group",
    matterType: "Real Estate",
    practiceArea: "Real Estate",
    jurisdiction: "Massachusetts, US",
    receivedAt: "2026-08-20 11:02",
    value: "$6.8M",
    status: "approved",
    suggestedLawyer: "Marco Bellini",
    suggestedLawyerRole: "Counsel, Real Estate",
    conflictFlag: false,
    riskScore: 22,
    aiConfidence: 98,
    summary: "Negotiation of a 12-year anchor tenant lease. Cleared and assigned.",
    parties: ["Beacon Property Group", "Harbor Tower Holdings"],
    clauses: [
      {
        id: "c1",
        label: "Rent Escalation",
        text: "Annual escalation of 3% with CPI adjustment cap.",
        category: "Economics",
        confidence: 95,
        risk: "low",
      },
    ],
    conflicts: [],
  },
  {
    id: "MAT-2018",
    backendCaseId: "case-004",
    title: "Patent License — Aurora Semiconductors",
    client: "Aurora Semiconductors",
    matterType: "IP Licensing",
    practiceArea: "Intellectual Property",
    jurisdiction: "Texas, US",
    receivedAt: "2026-08-19 14:20",
    value: "$9.3M",
    status: "rejected",
    suggestedLawyer: "Priya Ramanathan",
    suggestedLawyerRole: "Partner, Corporate M&A",
    conflictFlag: true,
    riskScore: 88,
    aiConfidence: 79,
    summary:
      "Cross-licensing agreement declined at intake due to a direct adverse conflict with a strategic firm client.",
    parties: ["Aurora Semiconductors", "Cirrus Micro (adverse)"],
    clauses: [],
    conflicts: [
      {
        party: "Cirrus Micro",
        relation: "Active firm client — direct adverse party",
        matter: "MAT-1502",
        severity: "high",
      },
    ],
  },
]

export const initialLogs: SystemLogEntry[] = [
  {
    id: "log-9",
    time: "09:14:02",
    actor: "AI Intake Agent",
    action: "Extracted 3 clauses and computed risk score",
    target: "MAT-2041",
    level: "info",
  },
  {
    id: "log-8",
    time: "09:13:55",
    actor: "Conflict Engine",
    action: "Flagged potential adverse-party conflict",
    target: "MAT-2041",
    level: "warning",
  },
  {
    id: "log-7",
    time: "08:41:10",
    actor: "AI Assignment Agent",
    action: "Recommended Daniel Osei (confidence 96%)",
    target: "MAT-2038",
    level: "info",
  },
  {
    id: "log-6",
    time: "08:40:32",
    actor: "Conflict Engine",
    action: "Cleared — no conflicts detected",
    target: "MAT-2038",
    level: "success",
  },
  {
    id: "log-5",
    time: "16:56:44",
    actor: "Conflict Engine",
    action: "Flagged positional conflict for human review",
    target: "MAT-2035",
    level: "warning",
  },
  {
    id: "log-4",
    time: "11:20:18",
    actor: "Marco Bellini",
    action: "Approved assignment after review",
    target: "MAT-2029",
    level: "success",
  },
  {
    id: "log-3",
    time: "14:22:03",
    actor: "Priya Ramanathan",
    action: "Rejected intake — direct adverse conflict",
    target: "MAT-2018",
    level: "danger",
  },
]
