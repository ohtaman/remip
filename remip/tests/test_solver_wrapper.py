from unittest.mock import MagicMock, patch

import pytest

from remip.models import (
    Constraint,
    MIPProblem,
    Objective,
    ObjectiveCoefficient,
    Parameters,
    Variable,
)
from remip.solvers.scip_wrapper import ScipSolverWrapper


@pytest.fixture
def solver_wrapper():
    return ScipSolverWrapper()


@pytest.fixture
def sample_problem():
    return MIPProblem(
        parameters=Parameters(name="test_problem", sense=1, status=0, sol_status=0),
        objective=Objective(name="obj", coefficients=[ObjectiveCoefficient(name="x", value=1.0)]),
        constraints=[],
        variables=[Variable(name="x", lower_bound=0, upper_bound=1, category="Continuous")],
    )


@pytest.fixture
def lp_problem():
    """A simple LP problem."""
    return MIPProblem(
        parameters=Parameters(name="lp_problem", sense=-1, status=0, sol_status=0),  # maximize
        objective=Objective(
            name="obj",
            coefficients=[
                ObjectiveCoefficient(name="x", value=1.0),
                ObjectiveCoefficient(name="y", value=2.0),
            ],
        ),
        constraints=[
            Constraint(
                name="c1",
                sense=-1,
                coefficients=[
                    ObjectiveCoefficient(name="x", value=-1.0),
                    ObjectiveCoefficient(name="y", value=1.0),
                ],
                constant=-1.0,  # Represents RHS, so -x + y <= 1
            ),
            Constraint(
                name="c2",
                sense=-1,
                coefficients=[
                    ObjectiveCoefficient(name="x", value=1.0),
                    ObjectiveCoefficient(name="y", value=1.0),
                ],
                constant=-2.0,  # Represents RHS, so x + y <= 2
            ),
        ],
        variables=[
            Variable(name="x", lower_bound=0, upper_bound=None, category="Continuous"),
            Variable(name="y", lower_bound=0, upper_bound=None, category="Continuous"),
        ],
        solver_options={"presolving/maxrounds": 0},
    )


@pytest.fixture
def mip_problem():
    """A simple MIP problem."""
    return MIPProblem(
        parameters=Parameters(name="mip_problem", sense=-1, status=0, sol_status=0),  # maximize
        objective=Objective(
            name="obj",
            coefficients=[
                ObjectiveCoefficient(name="x", value=1.0),
                ObjectiveCoefficient(name="y", value=2.0),
            ],
        ),
        constraints=[
            Constraint(
                name="c1",
                sense=-1,
                coefficients=[
                    ObjectiveCoefficient(name="x", value=-1.0),
                    ObjectiveCoefficient(name="y", value=1.0),
                ],
                constant=-1.0,
            ),
            Constraint(
                name="c2",
                sense=-1,
                coefficients=[
                    ObjectiveCoefficient(name="x", value=1.0),
                    ObjectiveCoefficient(name="y", value=1.0),
                ],
                constant=-2.0,
            ),
        ],
        variables=[
            Variable(name="x", lower_bound=0, upper_bound=None, category="Integer"),
            Variable(name="y", lower_bound=0, upper_bound=None, category="Continuous"),
        ],
        solver_options={"presolving/maxrounds": 0},
    )


@patch("remip.solvers.scip_wrapper.Model")
@pytest.mark.asyncio
async def test_solve(MockModel, solver_wrapper, sample_problem):
    # Arrange
    mock_model_instance = MagicMock()
    MockModel.return_value = mock_model_instance

    # Create a mock variable that can be used as a key in the solution dict
    mock_var = MagicMock()
    mock_var.name = "x"
    mock_model_instance.addVar.return_value = mock_var

    mock_solution = {mock_var: 1.0}
    mock_model_instance.getBestSol.return_value = mock_solution
    mock_model_instance.getStatus.return_value = "optimal"
    mock_model_instance.getObjVal.return_value = 1.0
    mock_model_instance.getNSols.return_value = 1
    mock_model_instance.getNBinVars.return_value = 0
    mock_model_instance.getNIntVars.return_value = 0
    mock_model_instance.getConss.return_value = []

    # Act
    solution = await solver_wrapper.solve(sample_problem)

    # Assert
    assert solution.status == "optimal"
    assert solution.objective_value == 1.0
    assert solution.variables["x"] == 1.0
    mock_model_instance.optimize.assert_called_once()


@patch("remip.solvers.scip_wrapper.Model")
@pytest.mark.asyncio
async def test_solve_and_stream_events_optimizes_model(MockModel, solver_wrapper, sample_problem):
    # Arrange
    mock_model_instance = MagicMock()
    MockModel.return_value = mock_model_instance
    mock_model_instance.getNSols.return_value = 0  # Avoid TypeError
    mock_model_instance.getStatus.return_value = "not solved"  # Avoid ValidationError
    mock_model_instance.getNBinVars.return_value = 0
    mock_model_instance.getNIntVars.return_value = 0
    mock_model_instance.getConss.return_value = []

    # Act
    # We need to consume the generator to execute the code
    async for _ in solver_wrapper.solve_and_stream_events(sample_problem):
        pass

    # Assert
    # In the new implementation, optimize is called instead of setMessagehdlr
    mock_model_instance.optimize.assert_called_once()


@patch("remip.solvers.scip_wrapper.Model")
@pytest.mark.asyncio
async def test_build_model_with_sos1(MockModel, solver_wrapper):
    # Arrange
    mock_model_instance = MagicMock()
    MockModel.return_value = mock_model_instance

    # Mock variables
    mock_x_A = MagicMock()
    mock_x_A.name = "x_A"
    mock_x_B = MagicMock()
    mock_x_B.name = "x_B"
    mock_x_C = MagicMock()
    mock_x_C.name = "x_C"

    def addVar_side_effect(name, **kwargs):
        if name == "x_A":
            return mock_x_A
        if name == "x_B":
            return mock_x_B
        if name == "x_C":
            return mock_x_C
        return MagicMock()

    mock_model_instance.addVar.side_effect = addVar_side_effect

    problem = MIPProblem(
        parameters=Parameters(name="sos_problem", sense=-1, status=0, sol_status=0),  # maximize
        objective=Objective(
            name="obj",
            coefficients=[
                ObjectiveCoefficient(name="x_A", value=100.0),
                ObjectiveCoefficient(name="x_B", value=120.0),
                ObjectiveCoefficient(name="x_C", value=80.0),
            ],
        ),
        constraints=[],
        variables=[
            Variable(name="x_A", lower_bound=0, upper_bound=1, category="Binary"),
            Variable(name="x_B", lower_bound=0, upper_bound=1, category="Binary"),
            Variable(name="x_C", lower_bound=0, upper_bound=1, category="Binary"),
        ],
        sos1=[{"x_A": 1, "x_B": 2, "x_C": 3}],
    )

    # Act
    model, vars = await solver_wrapper._build_model(problem)

    # Assert
    mock_model_instance.addVar.assert_any_call(name="x_A", lb=0, ub=1, vtype="I")
    mock_model_instance.addVar.assert_any_call(name="x_B", lb=0, ub=1, vtype="I")
    mock_model_instance.addVar.assert_any_call(name="x_C", lb=0, ub=1, vtype="I")
    mock_model_instance.setObjective.assert_called_once()

    # Check that addConsSOS1 was called correctly
    mock_model_instance.addConsSOS1.assert_called_once()
    args, kwargs = mock_model_instance.addConsSOS1.call_args

    passed_vars = args[0]
    passed_weights = args[1]

    # The order of variables is not guaranteed because it comes from a dictionary.
    # We should sort them to have a deterministic test.
    passed_vars_and_weights = sorted(zip(passed_vars, passed_weights), key=lambda x: x[1])

    assert passed_vars_and_weights[0][0].name == "x_A"
    assert passed_vars_and_weights[0][1] == 1
    assert passed_vars_and_weights[1][0].name == "x_B"
    assert passed_vars_and_weights[1][1] == 2
    assert passed_vars_and_weights[2][0].name == "x_C"
    assert passed_vars_and_weights[2][1] == 3


@pytest.mark.asyncio
async def test_solve_lp_problem(solver_wrapper, lp_problem):
    solution = await solver_wrapper.solve(lp_problem)

    assert solution.status == "optimal"
    assert solution.objective_value == pytest.approx(3.5)
    assert solution.variables["x"] == pytest.approx(0.5)
    assert solution.variables["y"] == pytest.approx(1.5)

    assert solution.mip_gap is None or solution.mip_gap == 0.0

    assert solution.slacks is not None
    assert solution.slacks["c1"] == pytest.approx(0.0)
    assert solution.slacks["c2"] == pytest.approx(0.0)

    assert solution.duals is not None
    assert solution.duals["c1"] == pytest.approx(0.5)
    assert solution.duals["c2"] == pytest.approx(1.5)

    assert solution.reduced_costs is not None
    assert solution.reduced_costs["x"] == pytest.approx(0.0)
    assert solution.reduced_costs["y"] == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_solve_mip_problem(solver_wrapper, mip_problem):
    solution = await solver_wrapper.solve(mip_problem)

    assert solution.status == "optimal"
    # With x as integer, the optimal solution is x=1, y=1, obj=3
    assert solution.objective_value == pytest.approx(3.0)
    assert solution.variables["x"] == pytest.approx(1.0)
    assert solution.variables["y"] == pytest.approx(1.0)

    assert solution.mip_gap is not None
    assert solution.mip_gap == pytest.approx(0.0)

    assert solution.slacks is not None
    assert solution.slacks["c1"] == pytest.approx(1.0)  # -1 + 1 = 0 <= 1, slack is 1
    assert solution.slacks["c2"] == pytest.approx(0.0)  # 1 + 1 = 2 <= 2, slack is 0

    assert solution.duals is None
    assert solution.reduced_costs is None
