import json

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


def test_solve_optimal_streaming(lp_problem, requests_mock):
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

    requests_mock.post("http://localhost:8000/solve?stream=sse", text=sse_data)

    solver = ReMIPSolver(stream=True)
    status = solver.solve(lp_problem)
    assert status == constants.LpStatusOptimal
    assert lp_problem.objective.value == 1.0
    assert lp_problem.variables()[0].varValue == 1.0


def test_solve_optimal_non_streaming(lp_problem, requests_mock):
    solution = {
        "name": "Test_Problem",
        "status": "optimal",
        "objective_value": 1.0,
        "variables": {"x": 1.0},
    }
    requests_mock.post("http://localhost:8000/solve", json=solution)

    solver = ReMIPSolver(stream=False)
    status = solver.solve(lp_problem)
    assert status == constants.LpStatusOptimal
    assert lp_problem.objective.value == 1.0
    assert lp_problem.variables()[0].varValue == 1.0


def test_solve_infeasible_streaming(lp_problem, requests_mock):
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
    requests_mock.post("http://localhost:8000/solve?stream=sse", text=sse_data)

    solver = ReMIPSolver(stream=True)
    status = solver.solve(lp_problem)
    assert status == constants.LpStatusInfeasible


def test_solve_infeasible_non_streaming(lp_problem, requests_mock):
    solution = {
        "status": "infeasible",
        "name": "Test_Problem",
        "objective_value": None,
        "variables": {},
    }
    requests_mock.post("http://localhost:8000/solve", json=solution)

    solver = ReMIPSolver(stream=False)
    status = solver.solve(lp_problem)
    assert status == constants.LpStatusInfeasible


def test_solve_api_error(lp_problem, requests_mock):
    requests_mock.post(
        "http://localhost:8000/solve",
        exc=requests.exceptions.ConnectionError("API down"),
    )

    solver = ReMIPSolver()
    status = solver.solve(lp_problem)
    assert status == constants.LpStatusNotSolved


def test_solve_with_enhancements(lp_problem, requests_mock):
    solution = {
        "name": "Test_Problem",
        "status": "optimal",
        "objective_value": 1.0,
        "variables": {"x": 1.0},
        "mip_gap": 0.001,
        "slacks": {"c1": 0.0},
        "duals": {"c1": -1.0},
        "reduced_costs": {"x": 0.0},
    }
    requests_mock.post("http://localhost:8000/solve", json=solution)

    solver = ReMIPSolver(stream=False)
    status = solver.solve(lp_problem)
    assert status == constants.LpStatusOptimal
    assert lp_problem.objective.value == 1.0
    assert lp_problem.variables()[0].varValue == 1.0

    assert hasattr(lp_problem, "mip_gap")
    assert lp_problem.mip_gap == 0.001
    assert hasattr(lp_problem, "slacks")
    assert lp_problem.slacks == {"c1": 0.0}
    assert hasattr(lp_problem, "duals")
    assert lp_problem.duals == {"c1": -1.0}
    assert hasattr(lp_problem, "reduced_costs")
    assert lp_problem.reduced_costs == {"x": 0.0}
