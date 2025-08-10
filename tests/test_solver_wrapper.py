import pytest
from unittest.mock import MagicMock, patch
from remip.models import MIPProblem, Objective, ObjectiveCoefficient, Variable
from remip.solvers.scip_wrapper import ScipSolverWrapper

@pytest.fixture
def solver_wrapper():
    return ScipSolverWrapper()

@pytest.fixture
def sample_problem():
    return MIPProblem(
        name="test_problem",
        sense=1,
        objective=Objective(name="obj", coefficients=[ObjectiveCoefficient(name="x", value=1.0)]),
        constraints=[],
        variables={"x": Variable(name="x", lowBound=0, upBound=1, cat="Continuous")}
    )

@patch('remip.solvers.scip_wrapper.Model')
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

@patch('remip.solvers.scip_wrapper.Model')
@pytest.mark.asyncio
async def test_solve_and_stream_logs_sets_message_handler(MockModel, solver_wrapper, sample_problem):
    # Arrange
    mock_model_instance = MagicMock()
    MockModel.return_value = mock_model_instance

    # Act
    # We need to consume the generator to execute the code
    async for _ in solver_wrapper.solve_and_stream_logs(sample_problem):
        pass

    # Assert
    mock_model_instance.setMessagehdlr.assert_called_once()