"""_______________________________________"""
MAX_STEPS = 6

MODEL_NAME = "gemini-2.5-flash"


REQUIRED_CASE_TOOLS = [
"get_case",
"get_client",
"get_conflict_checks",
"get_lawyer",
]

REQUIRED_RESOURCES = [
"company://intake-policy",
"company://required-documents",
"company://policies/conflict",
"company://lawyers",
]