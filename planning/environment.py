from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from mcp_server.database import get_connection


@dataclass
class EvaluationCase:
    name: str
    goal: str
    expected_success: bool = True


@dataclass
class EvaluationResult:
    case_name: str
    success: bool
    output: Any
    score: float | None = None
    trials: int | None = None
    error: str | None = None


class EvaluationHarness:
    def __init__(
        self,
        cases: list[EvaluationCase],
    ) -> None:
        self.cases = cases

    def run(
        self,
        approach: Callable[[str], Any],
    ) -> list[EvaluationResult]:
        results: list[EvaluationResult] = []

        for case in self.cases:
            try:
                output = approach(case.goal)

                success = bool(
                    getattr(output, "success", case.expected_success)
                )

                score = getattr(output, "score", None)
                trials = getattr(output, "trials", None)

                if isinstance(trials, list):
                    trials = len(trials)

                results.append(
                    EvaluationResult(
                        case_name=case.name,
                        success=success,
                        output=output,
                        score=score,
                        trials=trials,
                    )
                )

            except Exception as exc:
                results.append(
                    EvaluationResult(
                        case_name=case.name,
                        success=False,
                        output=None,
                        error=str(exc),
                    )
                )

        return results

    def evaluate_results(
        self,
        results: list[EvaluationResult],
    ) -> dict[str, Any]:
        passed = 0

        for result, case in zip(results, self.cases):
            if result.success == case.expected_success:
                passed += 1

        total = len(results)

        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "accuracy": passed / total if total else 0.0,
        }


@dataclass
class EnvironmentFeedback:
    success: bool
    score: float
    evidence: str
    details: dict[str, Any]


class GroundedEnvironment:
    """
    Deterministically validates a proposed case assignment
    against the current LawFirm database state.

    The evaluator is read-only and does not modify the database.
    """

    def evaluate(self, output: Any) -> EnvironmentFeedback:
        if not isinstance(output, dict):
            return EnvironmentFeedback(
                success=False,
                score=0.0,
                evidence="Planning output must be a dictionary.",
                details={
                    "received_type": type(output).__name__,
                },
            )

        action = output.get("action")
        case_id = output.get("case_id")
        lawyer_id = output.get("lawyer_id")

        if action != "assign_case":
            return EnvironmentFeedback(
                success=False,
                score=0.0,
                evidence="Unsupported or missing action.",
                details={
                    "action": action,
                },
            )

        if not case_id or not lawyer_id:
            return EnvironmentFeedback(
                success=False,
                score=0.0,
                evidence="case_id and lawyer_id are required.",
                details={
                    "case_id": case_id,
                    "lawyer_id": lawyer_id,
                },
            )

        with get_connection() as conn:
            cursor = conn.cursor()

            # Check case state.
            cursor.execute(
                'SELECT status FROM "case" WHERE case_id = ?',
                (case_id,),
            )
            case = cursor.fetchone()

            if case is None:
                return EnvironmentFeedback(
                    success=False,
                    score=0.0,
                    evidence="The requested case does not exist.",
                    details={
                        "case_id": case_id,
                    },
                )

            case_status = case["status"]

            if case_status != "accepted":
                return EnvironmentFeedback(
                    success=False,
                    score=0.0,
                    evidence="The case is not in an assignable state.",
                    details={
                        "case_id": case_id,
                        "status": case_status,
                        "required_status": "accepted",
                    },
                )

            # Check lawyer state and capacity.
            cursor.execute(
                """
                SELECT
                    current_caseload,
                    max_caseload,
                    status
                FROM lawyer
                WHERE lawyer_id = ?
                """,
                (lawyer_id,),
            )
            lawyer = cursor.fetchone()

            if lawyer is None:
                return EnvironmentFeedback(
                    success=False,
                    score=0.0,
                    evidence="The requested lawyer does not exist.",
                    details={
                        "lawyer_id": lawyer_id,
                    },
                )

            if lawyer["status"] != "active":
                return EnvironmentFeedback(
                    success=False,
                    score=0.0,
                    evidence="The lawyer is not active.",
                    details={
                        "lawyer_id": lawyer_id,
                        "status": lawyer["status"],
                        "required_status": "active",
                    },
                )

            if lawyer["current_caseload"] >= lawyer["max_caseload"]:
                return EnvironmentFeedback(
                    success=False,
                    score=0.0,
                    evidence="The lawyer has reached maximum caseload.",
                    details={
                        "lawyer_id": lawyer_id,
                        "current_caseload": lawyer["current_caseload"],
                        "max_caseload": lawyer["max_caseload"],
                    },
                )

        return EnvironmentFeedback(
            success=True,
            score=1.0,
            evidence=(
                "The proposed assignment satisfies the current "
                "database constraints."
            ),
            details={
                "case_id": case_id,
                "lawyer_id": lawyer_id,
                "case_status": "accepted",
            },
        )