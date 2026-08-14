from planning.environment import GroundedEnvironment
from planning.self_correction.reflexion import reflexion


class FakeResponse:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    def __init__(self):
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)

        # First attempt is invalid because case-002 is under_review.
        if len(self.calls) == 1:
            return FakeResponse(
                {
                    "action": "assign_case",
                    "case_id": "case-002",
                    "lawyer_id": "lawyer-001",
                }
            )

        # Reflection.
        if len(self.calls) == 2:
            return FakeResponse(
                "I should verify the case status before assigning it."
            )

        # Second attempt uses an accepted case.
        return FakeResponse(
            {
                "action": "assign_case",
                "case_id": "case-001",
                "lawyer_id": "lawyer-001",
            }
        )


def test_reflexion_uses_grounded_environment():
    environment = GroundedEnvironment()
    llm = FakeLLM()

    result = reflexion(
        goal="Assign an appropriate lawyer to the case.",
        llm=llm,
        evaluator=environment.evaluate,
        max_trials=3,
        reflection_buffer_size=3,
    )

    assert result.success is True
    assert result.final_output == {
        "action": "assign_case",
        "case_id": "case-001",
        "lawyer_id": "lawyer-001",
    }

    assert len(result.trials) == 2
    assert result.trials[0].success is False
    assert result.trials[0].reflection is not None
    assert result.trials[1].success is True

    assert len(result.reflections) == 1