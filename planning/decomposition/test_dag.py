import pytest

from planning.decomposition.dag import validate_and_sort


def test_cycle_is_rejected():
    tasks = [
        {"id": "A", "depends_on": ["B"]},
        {"id": "B", "depends_on": ["A"]},
    ]

    with pytest.raises(ValueError, match="Cycle detected"):
        validate_and_sort(tasks)


def test_valid_graph_is_sorted():
    tasks = [
        {"id": "C", "depends_on": ["B"]},
        {"id": "B", "depends_on": ["A"]},
        {"id": "A", "depends_on": []},
    ]

    result = validate_and_sort(tasks)

    assert result == ["A", "B", "C"]