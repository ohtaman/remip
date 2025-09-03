from unittest.mock import MagicMock, patch

import pytest

from remip.models import MIPProblem, Objective, ObjectiveCoefficient, Parameters, Variable
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
