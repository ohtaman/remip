import pytest
from remip.models import MIPProblem, Objective, ObjectiveCoefficient, Variable
from remip.solvers.scip_wrapper import ScipSolverWrapper

@pytest.fixture
def solver_wrapper():
    return ScipSolverWrapper()

def test_convert_to_lp_format_minimize(solver_wrapper):
    problem = MIPProblem(
        name="test_min",
        sense=1, # Minimize
        objective=Objective(name="obj", coefficients=[ObjectiveCoefficient(name="x", value=1.0), ObjectiveCoefficient(name="y", value=-2.0)]),
        constraints=[
            {"name": "c1", "coefficients": [{"name": "x", "value": 1.0}, {"name": "y", "value": 1.0}], "sense": -1, "rhs": 10.0}, # LEQ
            {"name": "c2", "coefficients": [{"name": "x", "value": 2.0}, {"name": "y", "value": -1.0}], "sense": 1, "rhs": 0.0}, # GEQ
        ],
        variables={
            "x": Variable(name="x", lowBound=0, upBound=5, cat="Continuous"),
            "y": Variable(name="y", lowBound=0, cat="Integer"),
        }
    )

    expected_lp = (
        "Minimize\n"
        "  obj: 1.0 x + -2.0 y\n"
        "Subject To\n"
        "  c0: 1.0 x + 1.0 y <= 10.0\n"
        "  c1: 2.0 x + -1.0 y >= 0.0\n"
        "Bounds\n"
        "  0.0 <= x\n"
        "  x <= 5.0\n"
        "  0.0 <= y\n"
        "Generals\n"
        "  y\n"
        "End\n"
    )

    assert solver_wrapper._convert_to_lp_format(problem) == expected_lp

def test_parse_solution(solver_wrapper, tmp_path):
    sol_content = (
        "solution status: optimal\n"
        "objective value: -20.0\n"
        "x = 0.0\n"
        "y = 10.0\n"
    )
    sol_file = tmp_path / "solution.sol"
    sol_file.write_text(sol_content)

    problem = MIPProblem(
        name="test_parse",
        sense=1,
        objective=Objective(name="obj", coefficients=[]),
        constraints=[],
        variables={"x": Variable(name="x", cat="Continuous"), "y": Variable(name="y", cat="Integer")}
    )

    solution = solver_wrapper._parse_solution(str(sol_file), problem)

    assert solution.name == "test_parse"
    assert solution.status == "optimal"
    assert solution.objective_value == -20.0
    assert solution.variables == {"x": 0.0, "y": 10.0}