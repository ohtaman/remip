import pytest
from pydantic import ValidationError

from remip.models import MIPProblem


def test_mip_problem_valid():
    data = {
        "parameters": {"name": "test_problem", "sense": 1, "status": 0, "sol_status": 0},
        "objective": {"name": "objective", "coefficients": [{"name": "x", "value": 1.0}]},
        "constraints": [],
        "variables": [{"name": "x", "lowBound": 0, "upBound": 1, "cat": "Continuous"}],
    }
    problem = MIPProblem(**data)
    assert problem.parameters.name == "test_problem"
    assert problem.parameters.sense == 1


def test_mip_problem_invalid():
    with pytest.raises(ValidationError):
        # This is invalid because it's an empty dictionary
        MIPProblem(**{})
