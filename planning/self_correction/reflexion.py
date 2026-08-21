from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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


@dataclass
class ReflexionTrial:
    trial_number: int
    output: Any
    success: bool
    reflection: str | None


@dataclass
class ReflexionResult:
    final_output: Any
    success: bool
    trials: list[ReflexionTrial]
    reflections: list[str]


def reflexion(
    goal: str,
    llm: Any,
    evaluator: Any,
    max_trials: int = 3,
    reflection_buffer_size: int = 3,
) -> ReflexionResult:
    """
    Run a Reflexion loop with a capped episodic reflection buffer.

    The LLM generates each trial and reflection.
    The evaluator determines whether the trial actually succeeded.
    """

    if max_trials < 1:
        raise ValueError("max_trials must be positive")

    if reflection_buffer_size < 1:
        raise ValueError("reflection_buffer_size must be positive")

    reflections: list[str] = []
    trials: list[ReflexionTrial] = []

    best_output: Any = ""
    best_score = float("-inf")

    for trial_number in range(1, max_trials + 1):

        recalled = (
            "\n".join(
                f"- {reflection}"
                for reflection in reflections[-reflection_buffer_size:]
            )
            or "- No previous reflections."
        )

        # Generate the next attempt using previous reflections.
        response = llm.invoke(
            [
                (
                    "system",
                    (
                        "You are the acting agent in a Reflexion loop. "
                        "Attempt the task again using lessons from previous trials."
                    ),
                ),
                (
                    "human",
                    f"""
Task:
{goal}

Previous reflections:
{recalled}

Produce the complete deliverable.
Apply the previous lessons without discussing them.
""",
                ),
            ]
        )

        # Preserve structured outputs such as dictionaries/lists.
        # Text responses are normalized to strings.
        raw_content = getattr(response, "content", response)

        if isinstance(raw_content, (dict, list)):
            output = raw_content
        else:
            output = _content_to_text(response)

        if not output:
            raise RuntimeError("The chat model returned an empty response.")

        # The evaluator decides whether the attempt actually succeeded.
        feedback = evaluator(output)

        success = bool(feedback.success)
        score = float(
            getattr(
                feedback,
                "score",
                1.0 if success else 0.0,
            )
        )

        trial = ReflexionTrial(
            trial_number=trial_number,
            output=output,
            success=success,
            reflection=None,
        )

        if score > best_score:
            best_output = output
            best_score = score

        # Successful trial: stop immediately.
        if success:
            trials.append(trial)

            return ReflexionResult(
                final_output=output,
                success=True,
                trials=trials,
                reflections=reflections[-reflection_buffer_size:],
            )

        # Failed trial: generate a reflection.
        response = llm.invoke(
            [
                (
                    "system",
                    (
                        "Generate a concise first-person reflection. "
                        "Do not rewrite the answer."
                    ),
                ),
                (
                    "human",
                    f"""
Task:
{goal}

Failed attempt:
{output}

Evaluation feedback:
{feedback}

Explain what went wrong and what specific strategy
should be used in the next trial.

Start with "I".
""",
                ),
            ]
        )

        reflection = _content_to_text(response)

        if not reflection:
            raise RuntimeError(
                "The reflection model returned an empty response."
            )

        trial.reflection = reflection

        trials.append(trial)
        reflections.append(reflection)

    return ReflexionResult(
        final_output=best_output,
        success=False,
        trials=trials,
        reflections=reflections[-reflection_buffer_size:],
    )