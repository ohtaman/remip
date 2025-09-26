import json
from typing import AsyncGenerator, Optional

from fastapi.testclient import TestClient

from remip.main import app, get_solver_service
from remip.models import (
    EndEvent,
    LogEvent,
    MetricEvent,
    MIPProblem,
    MIPSolution,
    ResultEvent,
    SolverEvent,
)
from remip.services import MIPSolverService


class MockMIPSolverService(MIPSolverService):
    async def solve(self, problem_data: MIPProblem, timeout: Optional[float] = None) -> MIPSolution:
        return MIPSolution(
            name=problem_data.parameters.name,
            status="Optimal",
            objective_value=1.0,
            variables={"x": 1.0},
        )

    async def solve_stream(
        self, problem_data: MIPProblem, timeout: Optional[float] = None
    ) -> AsyncGenerator[SolverEvent, None]:
        yield LogEvent(
            type="log",
            timestamp="2025-01-01T00:00:00Z",
            level="info",
            stage="presolve",
            message="log line 1",
            sequence=1,
        )
        yield MetricEvent(
            type="metric",
            timestamp="2025-01-01T00:00:01Z",
            objective_value=1.5,
            gap=0.5,
            iteration=10,
            sequence=2,
        )
        yield ResultEvent(
            type="result",
            timestamp="2025-01-01T00:00:02Z",
            solution=MIPSolution(
                name=problem_data.parameters.name,
                status="Optimal",
                objective_value=1.0,
                variables={"x": 1.0},
            ),
            runtime_milliseconds=100,
            sequence=3,
        )
        yield EndEvent(type="end", success=True)


def override_get_solver_service():
    return MockMIPSolverService()


app.dependency_overrides[get_solver_service] = override_get_solver_service

client = TestClient(app)


def test_solver_info():
    response = client.get("/solver-info")
    assert response.status_code == 200
    assert response.json() == {"solver": "SCIP", "version": "x.y.z"}


def test_solve_non_streaming():
    problem = {
        "parameters": {"name": "test_problem", "sense": 1, "status": 0, "sol_status": 0},
        "objective": {"name": "objective", "coefficients": [{"name": "x", "value": 1.0}]},
        "constraints": [],
        "variables": [{"name": "x", "lowBound": 0, "upBound": 1, "cat": "Continuous"}],
    }
    response = client.post("/solve", json=problem)
    assert response.status_code == 200
    solution = response.json()
    assert solution["name"] == "test_problem"
    assert solution["status"] == "Optimal"
    assert solution["objective_value"] == 1.0
    assert solution["variables"] == {"x": 1.0}


def test_solve_invalid():
    problem = {}
    response = client.post("/solve", json=problem)
    assert response.status_code == 422  # Unprocessable Entity


def test_solve_stream_sse():
    problem = {
        "parameters": {"name": "test_problem", "sense": 1, "status": 0, "sol_status": 0},
        "objective": {"name": "objective", "coefficients": [{"name": "x", "value": 1.0}]},
        "constraints": [],
        "variables": [{"name": "x", "lowBound": 0, "upBound": 1, "cat": "Continuous"}],
    }

    response = client.post("/solve?stream=sse", json=problem)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    raw_events = response.text.strip().split("\n\n")
    events = []
    for raw_event in raw_events:
        lines = raw_event.split("\n")
        event_type = lines[0].replace("event: ", "")
        data = json.loads(lines[1].replace("data: ", ""))
        events.append({"type": event_type, "data": data})

    assert len(events) == 4

    assert events[0]["type"] == "log"
    assert events[0]["data"]["message"] == "log line 1"

    assert events[1]["type"] == "metric"
    assert events[1]["data"]["gap"] == 0.5

    assert events[2]["type"] == "result"
    assert events[2]["data"]["solution"]["status"] == "Optimal"

    assert events[3]["type"] == "end"
    assert events[3]["data"]["success"] is True


def test_solve_non_stream_with_accept_header():
    problem = {
        "parameters": {"name": "test_problem", "sense": 1, "status": 0, "sol_status": 0},
        "objective": {"name": "objective", "coefficients": [{"name": "x", "value": 1.0}]},
        "constraints": [],
        "variables": [{"name": "x", "lowBound": 0, "upBound": 1, "cat": "Continuous"}],
    }
    headers = {"Accept": "text/event-stream"}
    response = client.post("/solve", json=problem, headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
