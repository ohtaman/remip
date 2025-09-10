import pytest
from pydantic import ValidationError

from remip.models import MIPProblem, MIPSolution


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


def test_mip_solution_with_enhancements():
    solution_data = {
        "name": "test_solution",
        "status": "optimal",
        "objective_value": 10.0,
        "variables": {"x": 1.0, "y": 2.0},
        "mip_gap": 0.001,
        "slacks": {"c1": 0.0, "c2": 1.0},
        "duals": {"c1": -1.0, "c2": 0.0},
        "reduced_costs": {"x": 0.0, "y": 0.5},
    }
    solution = MIPSolution(**solution_data)
    assert solution.name == "test_solution"
    assert solution.status == "optimal"
    assert solution.objective_value == 10.0
    assert solution.variables == {"x": 1.0, "y": 2.0}
    assert solution.mip_gap == 0.001
    assert solution.slacks == {"c1": 0.0, "c2": 1.0}
    assert solution.duals == {"c1": -1.0, "c2": 0.0}
    assert solution.reduced_costs == {"x": 0.0, "y": 0.5}

    # Test serialization
    serialized_solution = solution.model_dump()
    assert serialized_solution["mip_gap"] == 0.001

    # Test deserialization
    deserialized_solution = MIPSolution(**serialized_solution)
    assert deserialized_solution.mip_gap == 0.001
