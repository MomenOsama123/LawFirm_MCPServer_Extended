from planning.environment import GroundedEnvironment


def test_valid_case_assignment_is_accepted():
    environment = GroundedEnvironment()

    result = environment.evaluate(
        {
            "action": "assign_case",
            "case_id": "case-001",
            "lawyer_id": "lawyer-001",
        }
    )

    assert result.success is True
    assert result.score == 1.0
    assert "satisfies" in result.evidence
    assert result.details["case_id"] == "case-001"
    assert result.details["lawyer_id"] == "lawyer-001"


def test_unaccepted_case_is_rejected():
    environment = GroundedEnvironment()

    result = environment.evaluate(
        {
            "action": "assign_case",
            "case_id": "case-002",
            "lawyer_id": "lawyer-001",
        }
    )

    assert result.success is False
    assert result.score == 0.0
    assert "not in an assignable state" in result.evidence
    assert result.details["status"] == "under_review"


def test_full_caseload_lawyer_is_rejected():
    environment = GroundedEnvironment()

    result = environment.evaluate(
        {
            "action": "assign_case",
            "case_id": "case-001",
            "lawyer_id": "lawyer-003",
        }
    )

    assert result.success is False
    assert result.score == 0.0
    assert "maximum caseload" in result.evidence
    assert result.details["current_caseload"] == 6
    assert result.details["max_caseload"] == 6


def test_missing_case_is_rejected():
    environment = GroundedEnvironment()

    result = environment.evaluate(
        {
            "action": "assign_case",
            "case_id": "case-999",
            "lawyer_id": "lawyer-001",
        }
    )

    assert result.success is False
    assert result.score == 0.0
    assert "does not exist" in result.evidence


def test_invalid_action_is_rejected():
    environment = GroundedEnvironment()

    result = environment.evaluate(
        {
            "action": "something_else",
            "case_id": "case-001",
            "lawyer_id": "lawyer-001",
        }
    )

    assert result.success is False
    assert result.score == 0.0