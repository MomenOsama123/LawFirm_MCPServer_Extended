from planning.environment import GroundedEnvironment


def ungrounded_check(output: dict) -> bool:
    """
    Simulates a superficial self-critique that only checks
    whether the required fields are present.
    """
    return all(
        output.get(field)
        for field in ("action", "case_id", "lawyer_id")
    )


def test_grounded_validation_catches_failure_missed_by_ungrounded_check():
    output = {
        "action": "assign_case",
        "case_id": "case-002",
        "lawyer_id": "lawyer-001",
    }

    # The superficial check considers the output valid
    # because the expected fields are present.
    assert ungrounded_check(output) is True

    # The grounded environment checks the actual database state.
    environment = GroundedEnvironment()
    grounded_result = environment.evaluate(output)

    assert grounded_result.success is False
    assert grounded_result.score == 0.0

    assert grounded_result.details["case_id"] == "case-002"
    assert grounded_result.details["status"] == "under_review"

    assert "not in an assignable state" in grounded_result.evidence
    