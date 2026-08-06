import json
import os

TEST_SUITE_DIR = "context_eval/test_suite"
os.makedirs(TEST_SUITE_DIR, exist_ok=True)

test_cases_data = [
    {
        "case_id": "case_001_high_risk_waiver",
        "description": "Buries client risk rating under multiple search chunks.",
        "expected_decision": "REJECT",
        "system_prompt": "You are a Legal Compliance Agent. Rules:\n1. If client is High Risk, REJECT all settlement waivers.\n2. Verify clause 14B.",
        "user_query": "Review Settlement Waiver #8841 for Client Acme Corp. Note: Compliance DB flagged Acme Corp as High Risk earlier today. Run standard audits.",
        "chunks": [
            ("Tool Output Chunk 1: " + ("Lorem ipsum data payload audit dump. " * 150)),
            ("Tool Output Chunk 2: " + ("DB scan output table record entries. " * 150))
        ]
    },
    {
        "case_id": "case_002_clause14b_indemnification",
        "description": "Verifies clause 14B compliance deep within intermediate tool output.",
        "expected_decision": "APPROVE",
        "system_prompt": "You are a Legal Compliance Agent. Rules:\n1. If client is High Risk, REJECT.\n2. Must confirm Clause 14B indemnification is verified before approving.",
        "user_query": "Review Partnership Agreement #1092 for Beta LLC. Client is Low Risk. Run audits.",
        "chunks": [
            ("Tool Output Chunk 1: [DB Record: Clause 14B verified fully compliant] " + ("Intermediate boilerplate text. " * 120))
        ]
    },
    {
        "case_id": "case_003_conflict_check_partner",
        "description": "Early user message specifies opposing counsel conflict of interest.",
        "expected_decision": "REJECT",
        "system_prompt": "Rules:\n1. If Opposing Counsel is Partner John Doe, REJECT due to active conflict of interest.\n2. Otherwise proceed with standard review.",
        "user_query": "Analyze litigation filing #4401. Opposing Counsel listed: Partner John Doe. Audit financials.",
        "chunks": [
            ("Tool Output Chunk 1: " + ("Financial ledger dump rows 1-500. " * 180))
        ]
    },
    {
        "case_id": "case_004_statute_limitations_deadline",
        "description": "Buries filing date to check against statutory 30-day deadline.",
        "expected_decision": "REJECT",
        "system_prompt": "Rules:\n1. Claims filed more than 30 days after incident date must be REJECTED (Statute of Limitations).\n2. Incident Date: 2026-01-01. Current Filing Date: 2026-03-01.",
        "user_query": "Evaluate Claim #9910. Incident date was 2026-01-01. Verify if filing date exceeds 30-day window.",
        "chunks": [
            ("Tool Output Chunk 1: " + ("Evidence attachments and witness statements. " * 160))
        ]
    },
    {
        "case_id": "case_005_jurisdiction_governing_law",
        "description": "Requires preserving governing jurisdiction set in prompt.",
        "expected_decision": "FLAG_FOR_REVIEW",
        "system_prompt": "Rules:\n1. If governing law is outside Delaware or New York, FLAG_FOR_REVIEW.\n2. If governing law is Delaware/NY, APPROVE.",
        "user_query": "Review Vendor Contract #5521. Governing Law specified: London International Arbitration (UK).",
        "chunks": [
            ("Tool Output Chunk 1: " + ("Vendor SLA metrics and pricing schedules. " * 170))
        ]
    },
    {
        "case_id": "case_006_assigned_counsel_licensure",
        "description": "Verifies assigned lawyer bar licensure requirement.",
        "expected_decision": "REJECT",
        "system_prompt": "Rules:\n1. Assigned Lead Counsel must hold active California Bar Licensure.\n2. If License status is Suspended or Unlicensed in CA, REJECT.",
        "user_query": "Review Case #1209. Lead Counsel: Atty. Jane Smith (CA Bar Status: Suspended).",
        "chunks": [
            ("Tool Output Chunk 1: " + ("Court filing motions and hearing transcripts. " * 160))
        ]
    },
    {
        "case_id": "case_007_missing_signatory_seal",
        "description": "Tests missing corporate seal requirement.",
        "expected_decision": "REJECT",
        "system_prompt": "Rules:\n1. Deeds of Conveyance require an official Corporate Seal.\n2. If Seal missing, REJECT.",
        "user_query": "Audit Deed #7731. Document signature present, Corporate Seal: MISSING.",
        "chunks": [
            ("Tool Output Chunk 1: " + ("Notary seal validation logs and OCR dumps. " * 150))
        ]
    },
    {
        "case_id": "case_008_liability_cap_threshold",
        "description": "Verifies liability cap does not exceed maximum allowable policy threshold.",
        "expected_decision": "APPROVE",
        "system_prompt": "Rules:\n1. Liability cap must not exceed $1,000,000.\n2. If cap is <= $1,000,000 and Clause 14B is present, APPROVE.",
        "user_query": "Evaluate License Agreement #4001. Liability Cap: $500,000. Clause 14B: Verified.",
        "chunks": [
            ("Tool Output Chunk 1: " + ("Insurance certificates and schedule tables. " * 150))
        ]
    },
    {
        "case_id": "case_009_ip_assignment_warranty",
        "description": "Buries IP assignment flag under intermediate tool noise.",
        "expected_decision": "FLAG_FOR_REVIEW",
        "system_prompt": "Rules:\n1. If IP Assignment Clause excludes pre-existing patents, FLAG_FOR_REVIEW.\n2. Otherwise APPROVE.",
        "user_query": "Review IP Transfer #6112. Note: Seller excludes pre-existing patents in Section 3.",
        "chunks": [
            ("Tool Output Chunk 1: " + ("Patent office lookup responses and claims trees. " * 170))
        ]
    },
    {
        "case_id": "case_010_regulatory_dispute_flag",
        "description": "Checks regulatory dispute record buried in tool outputs.",
        "expected_decision": "FLAG_FOR_REVIEW",
        "system_prompt": "Rules:\n1. If compliance scan detects an active regulatory dispute, FLAG_FOR_REVIEW.\n2. If clean, APPROVE.",
        "user_query": "Audit M&A Agreement #9012 for Gamma Corp.",
        "chunks": [
            ("Tool Output Chunk 1: [DB Record: Active regulatory dispute found in Region 4] " + ("Compliance log dump. " * 160))
        ]
    }
]


def build_messages(item):
    messages = [
        {"role": "system", "content": item["system_prompt"]},
        {"role": "user", "content": item["user_query"]}
    ]
    
    for idx, chunk_content in enumerate(item["chunks"], start=1):
        call_id = f"c{idx}"
        messages.append({
            "role": "assistant",
            "content": f"Querying database index chunk {idx}...",
            "tool_calls": [{"id": call_id, "function": {"name": "query_db", "arguments": f"{{\"chunk\": {idx}}}"}}]
        })
        messages.append({
            "role": "tool",
            "tool_call_id": call_id,
            "content": chunk_content
        })

    messages.append({
        "role": "user",
        "content": "Tool executions complete. Provide final decision."
    })
    return messages


for item in test_cases_data:
    file_path = os.path.join(TEST_SUITE_DIR, f"{item['case_id']}.json")
    payload = {
        "case_id": item["case_id"],
        "description": item["description"],
        "expected_decision": item["expected_decision"],
        "messages": build_messages(item)
    }
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

print(f"Successfully generated 10 valid JSON transcript files in '{TEST_SUITE_DIR}/'.")