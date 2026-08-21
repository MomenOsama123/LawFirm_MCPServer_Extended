from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SelfRefineResult:
    draft: str
    critique: str
    revised: str
    issues: list[str]


def _content_to_text(response: Any) -> str:
    content = getattr(response, "content", response)

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))

        return "\n".join(parts).strip()

    return str(content).strip()


def deterministic_checks(
    draft: str,
    rubric: list[str],
) -> list[str]:
    """
    Cheap deterministic checks before asking the LLM to critique.
    """

    issues = []

    if not draft.strip():
        issues.append("The draft is empty.")

    if len(draft.split()) < 20:
        issues.append("The draft is probably too short to satisfy the task.")

    if not rubric:
        issues.append("No evaluation rubric was provided.")

    return issues


def self_refine(
    goal: str,
    draft: str,
    llm: Any,
    rubric: list[str],
) -> SelfRefineResult:
    """
    Run one Self-Refine cycle:

        draft -> critique -> revision
    """

    grounded_issues = deterministic_checks(draft, rubric)

    rubric_text = "\n".join(
        f"{index}. {item}"
        for index, item in enumerate(rubric, start=1)
    )

    deterministic_report = (
        "\n".join(f"- {issue}" for issue in grounded_issues)
        if grounded_issues
        else "- No deterministic issues detected."
    )

    # Step 1: Critique
    critique_response = llm.invoke(
        [
            (
                "system",
                (
                    "You are a strict critic. "
                    "Evaluate the draft against the provided rubric. "
                    "Do not rewrite the draft."
                ),
            ),
            (
                "human",
                f"""
Goal:
{goal}

Rubric:
{rubric_text}

Deterministic checks:
{deterministic_report}

Draft:
{draft}

List only concrete problems that prevent the draft from satisfying "
"the goal and rubric.

If there are no problems, respond exactly:
PASS
""",
            ),
        ]
    )

    critique = _content_to_text(critique_response)

    if not critique:
        raise RuntimeError("The critic returned an empty response.")

    # Step 2: Revision
    if critique.upper() == "PASS":
        revised = draft
    else:
        revision_response = llm.invoke(
            [
                (
                    "system",
                    (
                        "You are a reviser. "
                        "Improve the draft using the critique and rubric. "
                        "Preserve correct information and do not invent facts."
                    ),
                ),
                (
                    "human",
                    f"""
Goal:
{goal}

Rubric:
{rubric_text}

Original draft:
{draft}

Deterministic issues:
{deterministic_report}

Critique:
{critique}

Return only the improved final deliverable.
""",
                ),
            ]
        )

        revised = _content_to_text(revision_response)

        if not revised:
            raise RuntimeError("The revision model returned an empty response.")

    return SelfRefineResult(
        draft=draft,
        critique=critique,
        revised=revised,
        issues=grounded_issues,
    )