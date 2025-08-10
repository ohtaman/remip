import pytest
from pydantic import ValidationError
from remip.models import MIPProblem

def test_mip_problem_valid():
    data = {
        "name": "test_problem",
        "sense": 1,
        "objective": {
            "name": "objective",
            "coefficients": [{"name": "x", "value": 1.0}]
        },
        "constraints": [],
        "variables": {
            "x": {"name": "x", "lowBound": 0, "upBound": 1, "cat": "Continuous"}
        }
    }
    problem = MIPProblem(**data)
    assert problem.name == "test_problem"
    assert problem.sense == 1

def test_mip_problem_invalid():
    with pytest.raises(ValidationError):
        # This is invalid because 'objective' and 'variables' are missing required keys
        MIPProblem(name="test", sense=1, objective={}, constraints=[], variables={})
