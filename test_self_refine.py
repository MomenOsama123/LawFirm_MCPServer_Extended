from planning.self_correction.self_refine import self_refine


class PassingFakeLLM:
    def __init__(self):
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        return FakeResponse("PASS")


def test_self_refine_keeps_good_draft():
    llm = PassingFakeLLM()

    draft = (
        "Client: Ahmed\n"
        "Case: Contract dispute\n"
        "Lawyer: John"
    )

    result = self_refine(
        goal="Create a structured legal case summary.",
        draft=draft,
        llm=llm,
        rubric=[
            "Include the client name.",
            "Include the case type.",
            "Include the assigned lawyer.",
            "Do not invent information.",
        ],
    )

    assert result.revised == draft
    assert result.critique == "PASS"
    assert llm.calls == 1
    
    
class FakeResponse:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    def __init__(self):
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1

        if self.calls == 1:
            return FakeResponse(
                "Missing the lawyer assignment."
            )

        return FakeResponse(
            "Client: Ahmed\n"
            "Case: Contract dispute\n"
            "Lawyer: John"
        )


def test_self_refine_revises_flawed_draft():
    llm = FakeLLM()

    result = self_refine(
        goal="Create a structured legal case summary.",
        draft=(
            "Client: Ahmed\n"
            "Case: Contract dispute"
        ),
        llm=llm,
        rubric=[
            "Include the client name.",
            "Include the case type.",
            "Include the assigned lawyer.",
            "Do not invent information.",
        ],
    )

    assert result.draft != result.revised
    assert "lawyer" in result.critique.lower()
    assert "Lawyer: John" in result.revised
    assert llm.calls == 2