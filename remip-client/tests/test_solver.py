import json
from unittest.mock import MagicMock, patch

import pytest
import requests
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


@patch("remip_client.http_client.RequestsHttpClient")
def test_solve_optimal_streaming(mock_client_class, lp_problem):
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

    mock_response = MagicMock()
    mock_response.iter_lines.return_value = [
        line.encode("utf-8") for line in sse_data.strip().split("\n")
    ]

    mock_client_instance = mock_client_class.return_value
    mock_client_instance.solve.return_value = mock_response

    solver = ReMIPSolver(stream=True, env="cpython")
    status = solver.actualSolve(lp_problem)
    assert status == constants.LpStatusOptimal
    assert lp_problem.objective.value == 1.0
    assert lp_problem.variables()[0].varValue == 1.0


@patch("remip_client.http_client.RequestsHttpClient")
def test_solve_optimal_non_streaming(mock_client_class, lp_problem):
    solution = {
        "name": "Test_Problem",
        "status": "optimal",
        "objective_value": 1.0,
        "variables": {"x": 1.0},
    }
    mock_response = MagicMock()
    mock_response.json.return_value = solution
    mock_client_instance = mock_client_class.return_value
    mock_client_instance.solve.return_value = mock_response

    solver = ReMIPSolver(stream=False, env="cpython")
    status = solver.actualSolve(lp_problem)
    assert status == constants.LpStatusOptimal
    assert lp_problem.objective.value == 1.0
    assert lp_problem.variables()[0].varValue == 1.0


@patch("remip_client.http_client.RequestsHttpClient")
def test_solve_infeasible_streaming(mock_client_class, lp_problem):
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

    sse_data = (
        f"event: result\ndata: {json.dumps(result_event)}\n\n"
        f"event: end\ndata: {json.dumps(end_event)}\n\n"
    )
    mock_response = MagicMock()
    mock_response.iter_lines.return_value = [
        line.encode("utf-8") for line in sse_data.strip().split("\n")
    ]
    mock_client_instance = mock_client_class.return_value
    mock_client_instance.solve.return_value = mock_response

    solver = ReMIPSolver(stream=True, env="cpython")
    status = solver.actualSolve(lp_problem)
    assert status == constants.LpStatusInfeasible


@patch("remip_client.http_client.RequestsHttpClient")
def test_solve_infeasible_non_streaming(mock_client_class, lp_problem):
    solution = {
        "status": "infeasible",
        "name": "Test_Problem",
        "objective_value": None,
        "variables": {},
    }
    mock_response = MagicMock()
    mock_response.json.return_value = solution
    mock_client_instance = mock_client_class.return_value
    mock_client_instance.solve.return_value = mock_response

    solver = ReMIPSolver(stream=False, env="cpython")
    status = solver.actualSolve(lp_problem)
    assert status == constants.LpStatusInfeasible


@patch("remip_client.http_client.RequestsHttpClient")
def test_solve_api_error(mock_client_class, lp_problem):
    mock_client_instance = mock_client_class.return_value
    mock_client_instance.solve.side_effect = requests.exceptions.RequestException(
        "API down"
    )

    solver = ReMIPSolver(env="cpython")
    status = solver.actualSolve(lp_problem)
    assert status == constants.LpStatusNotSolved


@patch("remip_client.http_client.RequestsHttpClient")
def test_solve_with_timeout_sends_query_param(mock_client_class, lp_problem):
    """Tests that the timeout is sent as a query parameter."""
    mock_client_instance = mock_client_class.return_value

    solver = ReMIPSolver(stream=True, timeout=60, env="cpython")
    solver.actualSolve(lp_problem)

    mock_client_instance.solve.assert_called_once()
    # The http_client's solve method is called with the lp_problem dict
    call_args, call_kwargs = mock_client_instance.solve.call_args
    assert "timeout" in call_kwargs
    assert call_kwargs["timeout"] == 60


@patch("remip_client.http_client.RequestsHttpClient")
def test_solve_with_enhancements(mock_client_class, lp_problem):
    solution = {
        "name": "Test_Problem",
        "status": "optimal",
        "objective_value": 1.0,
        "variables": {"x": 1.0},
        "mip_gap": 0.001,
        "slacks": {"_C1": 0.0},
        "duals": {"_C1": -1.0},
        "reduced_costs": {"x": 0.0},
    }
    mock_response = MagicMock()
    mock_response.json.return_value = solution
    mock_client_instance = mock_client_class.return_value
    mock_client_instance.solve.return_value = mock_response

    solver = ReMIPSolver(stream=False, env="cpython")
    status = solver.actualSolve(lp_problem)
    assert status == constants.LpStatusOptimal
    assert lp_problem.objective.value == 1.0
    assert lp_problem.variables()[0].varValue == 1.0

    assert hasattr(solver.solution, "mip_gap")
    assert solver.solution.mip_gap == 0.001
    assert hasattr(lp_problem.constraints["_C1"], "slack")
    assert lp_problem.constraints["_C1"].slack == 0.0
    assert hasattr(lp_problem.constraints["_C1"], "pi")
    assert lp_problem.constraints["_C1"].pi == -1.0
    assert hasattr(lp_problem.variables()[0], "dj")
    assert lp_problem.variables()[0].dj == 0.0
