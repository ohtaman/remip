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
async def test_solve_optimal_streaming(lp_problem):
    def mock_transport(request: httpx.Request) -> httpx.Response:
        assert "stream=sse" in str(request.url)

        log_event = {
            "type": "log",
            "timestamp": "2025-01-01T00:00:00Z",
            "level": "info",
            "stage": "presolve",
            "message": "log line 1",
            "sequence": 1,
        }
        metric_event = {
            "type": "metric",
            "timestamp": "2025-01-01T00:00:01Z",
            "objective_value": 1.5,
            "gap": 0.5,
            "iteration": 10,
            "sequence": 2,
        }
        result_event = {
            "type": "result",
            "timestamp": "2025-01-01T00:00:02Z",
            "solution": {
                "name": "Test_Problem",
                "status": "optimal",
                "objective_value": 1.0,
                "variables": {"x": 1.0},
            },
            "runtime_milliseconds": 100,
            "sequence": 3,
        }
        end_event = {"type": "end", "success": True}

        sse_data = (
            f"event: log\ndata: {json.dumps(log_event)}\n\n"
            f"event: metric\ndata: {json.dumps(metric_event)}\n\n"
            f"event: result\ndata: {json.dumps(result_event)}\n\n"
            f"event: end\ndata: {json.dumps(end_event)}\n\n"
        )

        return httpx.Response(200, text=sse_data)

    async with ReMIPSolver(
        transport=httpx.MockTransport(mock_transport), stream=True
    ) as solver:
        status = await solver.solve(lp_problem)
        assert status == constants.LpStatusOptimal
        assert lp_problem.objective.value == 1.0
        assert lp_problem.variables()[0].varValue == 1.0


@pytest.mark.asyncio
async def test_solve_optimal_non_streaming(lp_problem):
    def mock_transport(request: httpx.Request) -> httpx.Response:
        assert "stream=sse" not in str(request.url)
        solution = {
            "name": "Test_Problem",
            "status": "optimal",
            "objective_value": 1.0,
            "variables": {"x": 1.0},
        }
        return httpx.Response(200, json=solution)

    async with ReMIPSolver(
        transport=httpx.MockTransport(mock_transport), stream=False
    ) as solver:
        status = await solver.solve(lp_problem)
        assert status == constants.LpStatusOptimal
        assert lp_problem.objective.value == 1.0
        assert lp_problem.variables()[0].varValue == 1.0


@pytest.mark.asyncio
async def test_solve_infeasible(lp_problem):
    def mock_transport(request: httpx.Request) -> httpx.Response:
        result_event = {
            "type": "result",
            "timestamp": "2025-01-01T00:00:02Z",
            "solution": {
                "name": "Test_Problem",
                "status": "infeasible",
                "objective_value": None,
                "variables": {},
            },
            "runtime_milliseconds": 100,
            "sequence": 1,
        }
        end_event = {"type": "end", "success": True}

        if "stream=sse" in str(request.url):
            sse_data = (
                f"event: result\ndata: {json.dumps(result_event)}\n\n"
                f"event: end\ndata: {json.dumps(end_event)}\n\n"
            )
            return httpx.Response(200, text=sse_data)
        else:
            return httpx.Response(
                200,
                json={
                    "status": "infeasible",
                    "name": "Test_Problem",
                    "objective_value": None,
                    "variables": {},
                },
            )

    # Test both streaming and non-streaming
    async with ReMIPSolver(
        transport=httpx.MockTransport(mock_transport), stream=True
    ) as solver:
        status = await solver.solve(lp_problem)
        assert status == constants.LpStatusInfeasible

    async with ReMIPSolver(
        transport=httpx.MockTransport(mock_transport), stream=False
    ) as solver:
        status = await solver.solve(lp_problem)
        assert status == constants.LpStatusInfeasible


@pytest.mark.asyncio
async def test_solve_api_error(lp_problem):
    def mock_transport(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("API down")

    async with ReMIPSolver(transport=httpx.MockTransport(mock_transport)) as solver:
        status = await solver.solve(lp_problem)
        assert status == constants.LpStatusNotSolved
