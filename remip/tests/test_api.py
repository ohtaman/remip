from typing import AsyncGenerator

from fastapi.testclient import TestClient

from remip.main import app, get_solver_service
from remip.models import MIPProblem, MIPSolution
from remip.services import MIPSolverService


class MockMIPSolverService(MIPSolverService):
    async def solve_problem(self, problem_data: MIPProblem) -> MIPSolution:
        return MIPSolution(
            name=problem_data.parameters.name,
            status="Optimal",
            objective_value=1.0,
            variables={"x": 1.0}
        )

    async def solve_problem_stream(self, problem_data: MIPProblem) -> AsyncGenerator[str, None]:
        yield "log line 1"
        yield "log line 2"

def override_get_solver_service():
    return MockMIPSolverService()

app.dependency_overrides[get_solver_service] = override_get_solver_service

client = TestClient(app)

def test_solver_info():
    response = client.get("/solver-info")
    assert response.status_code == 200
    assert response.json() == {"solver": "SCIP", "version": "x.y.z"}

def test_solve_valid():
    problem = {
        "parameters": {"name": "test_problem", "sense": 1, "status": 0, "sol_status": 0},
        "objective": {
            "name": "objective",
            "coefficients": [{"name": "x", "value": 1.0}]
        },
        "constraints": [],
        "variables": [
            {"name": "x", "lowBound": 0, "upBound": 1, "cat": "Continuous"}
        ]
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
    assert response.status_code == 422 # Unprocessable Entity

def test_solve_stream():
    problem = {
        "parameters": {"name": "test_problem", "sense": 1, "status": 0, "sol_status": 0},
        "objective": {
            "name": "objective",
            "coefficients": [{"name": "x", "value": 1.0}]
        },
        "constraints": [],
        "variables": [
            {"name": "x", "lowBound": 0, "upBound": 1, "cat": "Continuous"}
        ]
    }
    response = client.post("/solve-stream", json=problem)
    assert response.status_code == 200
    assert response.text == "log line 1log line 2"