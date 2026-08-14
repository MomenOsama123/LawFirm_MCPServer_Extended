from planning.self_correction.reflexion import reflexion


class FakeResponse:
    def __init__(self, content):
        self.content = content


class FakeFeedback:
    def __init__(self, success, score):
        self.success = success
        self.score = score

    def __str__(self):
        return f"success={self.success}, score={self.score}"


class FakeLLM:
    def __init__(self):
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)

        # Odd calls = trial attempts
        # Even calls = reflections
        if len(self.calls) == 1:
            return FakeResponse("First failed attempt")

        if len(self.calls) == 2:
            return FakeResponse(
                "I forgot to satisfy an important requirement."
            )

        if len(self.calls) == 3:
            return FakeResponse("Second improved attempt")

        return FakeResponse("I applied the previous reflection.")


def test_reflexion_carries_reflection_to_next_trial():
    llm = FakeLLM()

    evaluations = [
        FakeFeedback(False, 0.2),
        FakeFeedback(True, 1.0),
    ]

    evaluation_index = 0

    def evaluator(output):
        nonlocal evaluation_index

        feedback = evaluations[evaluation_index]
        evaluation_index += 1

        return feedback

    result = reflexion(
        goal="Produce a correct legal case summary.",
        llm=llm,
        evaluator=evaluator,
        max_trials=3,
        reflection_buffer_size=3,
    )

    assert result.success is True
    assert result.final_output == "Second improved attempt"

    assert len(result.trials) == 2
    assert len(result.reflections) == 1

    assert result.trials[0].reflection is not None

    # The second trial should receive the first trial's reflection.
    second_trial_messages = llm.calls[2]

    second_trial_prompt = second_trial_messages[1][1]

    assert "I forgot to satisfy an important requirement." in second_trial_prompt
    
    
def test_reflexion_stops_after_success():
    llm = FakeLLM()

    def evaluator(output):
        return FakeFeedback(True, 1.0)

    result = reflexion(
        goal="Produce a correct legal case summary.",
        llm=llm,
        evaluator=evaluator,
        max_trials=3,
        reflection_buffer_size=3,
    )

    assert result.success is True
    assert len(result.trials) == 1
    assert len(result.reflections) == 0
    
    
def test_reflexion_respects_max_trials():
    llm = FakeLLM()

    def evaluator(output):
        return FakeFeedback(False, 0.1)

    result = reflexion(
        goal="Produce a correct legal case summary.",
        llm=llm,
        evaluator=evaluator,
        max_trials=3,
        reflection_buffer_size=3,
    )

    assert result.success is False
    assert len(result.trials) == 3
    assert len(result.reflections) == 3