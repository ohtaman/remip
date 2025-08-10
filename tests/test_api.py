import pytest
from fastapi.testclient import TestClient
from mip_api.main import app

client = TestClient(app)

def test_solver_info():
    response = client.get("/solver-info")
    assert response.status_code == 200
    assert response.json() == {"solver": "SCIP", "version": "x.y.z"}

def test_solve_valid():
    problem = {
        "name": "test_problem",
        "sense": 1,
        "objective": {
            "name": "objective",
            "coefficients": [{"name": "x", "value": 1.0}]
        },
        "constraints": [],
        "variables": {
            "x": {"name": "x", "lowBound": 0, "upBound": 1, "cat": "Continuous"}
        }
    }
    response = client.post("/solve", json=problem)
    assert response.status_code == 200
    solution = response.json()
    assert solution["name"] == "test_problem"
    assert solution["status"] == "Optimal"

def test_solve_invalid():
    problem = {
        "name": "invalid_problem",
        "sense": 1,
        "objective": {}, # Invalid
        "constraints": [],
        "variables": {}
    }
    response = client.post("/solve", json=problem)
    assert response.status_code == 422 # Unprocessable Entity
