from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


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