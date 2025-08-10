import httpx
import pytest
from pulp import LpMaximize, LpProblem, LpVariable
from remip_client.solver import MipApiSolver


@pytest.mark.asyncio
async def test_client_solve_with_mock():
    """
    Tests the client's solve method with a mocked server.
    """
    # 1. Define a problem
    prob = LpProblem("test_problem_mock", LpMaximize)
    x = LpVariable("x", 0, 1, cat='Binary')
    y = LpVariable("y", 0, 1, cat='Binary')
    prob += x + y, "objective"
    prob += 2*x + y <= 2, "constraint1"

    # 2. Create a mock transport
    def mock_transport(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "name": "test_problem_mock",
                "status": "optimal",
                "objective_value": 1.0,
                "variables": {"x": 1.0, "y": 0.0}
            }
        )

    # 3. Initialize the solver with the mock transport
    async with MipApiSolver(transport=httpx.MockTransport(mock_transport)) as solver:
        # 4. Solve the problem
        status = await solver.solve(prob)

    # 5. Check the results
    assert status == 1 # LpStatusOptimal
    assert prob.status == 1 # LpStatusOptimal
    assert x.varValue == 1.0
    assert y.varValue == 0.0
