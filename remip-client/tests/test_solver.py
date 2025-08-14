import json

import httpx
import pytest
from pulp import LpMinimize, LpProblem, LpVariable, constants
from remip_client.solver import ReMIPSolver


@pytest.fixture
def lp_problem():
    # Create a simple LP problem
    prob = LpProblem("Test_Problem", LpMinimize)
    x = LpVariable("x", lowBound=0)
    prob += x  # Objective: minimize x
    prob += x >= 1
    return prob


@pytest.mark.asyncio
async def test_solve_optimal(lp_problem):
    def mock_transport(request: httpx.Request) -> httpx.Response:
        solution = {
            "status": "optimal",
            "objective_value": 1.0,
            "variables": {"x": 1.0}
        }
        return httpx.Response(
            200,
            text=f'LOG: some log\nRESULT: {json.dumps(solution)}'
        )

    async with ReMIPSolver(transport=httpx.MockTransport(mock_transport)) as solver:
        status = await solver.solve(lp_problem)
        assert status == constants.LpStatusOptimal
        assert lp_problem.objective.value == 1.0
        assert lp_problem.variables()[0].varValue == 1.0


@pytest.mark.asyncio
async def test_solve_infeasible(lp_problem):
    def mock_transport(request: httpx.Request) -> httpx.Response:
        solution = {"status": "infeasible"}
        return httpx.Response(
            200,
            text=f'LOG: some log\nRESULT: {json.dumps(solution)}'
        )

    async with ReMIPSolver(transport=httpx.MockTransport(mock_transport)) as solver:
        status = await solver.solve(lp_problem)
        assert status == constants.LpStatusInfeasible


@pytest.mark.asyncio
async def test_solve_api_error(lp_problem):
    def mock_transport(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("API down")

    async with ReMIPSolver(transport=httpx.MockTransport(mock_transport)) as solver:
        status = await solver.solve(lp_problem)
        assert status == constants.LpStatusNotSolved
