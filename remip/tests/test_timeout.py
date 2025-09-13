#!/usr/bin/env python

import pytest
from fastapi.testclient import TestClient

from remip.main import app


@pytest.fixture(scope="module")
def real_solver_client():
    """A TestClient that is guaranteed to use the real solver service."""
    # Temporarily clear any dependency overrides to ensure we use the real service
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides.clear()

    client = TestClient(app)
    yield client

    # Restore the original overrides after the tests in this module are done
    app.dependency_overrides = original_overrides


@pytest.fixture(scope="module")
def simple_problem():
    """A very simple problem payload."""
    return {
        "parameters": {"name": "test_simple", "sense": 1, "status": 0, "sol_status": 0},
        "objective": {"name": "objective", "coefficients": [{"name": "x", "value": 1.0}]},
        "constraints": [],
        "variables": [{"name": "x", "lowBound": 0, "upBound": 1, "cat": "Continuous"}],
    }


@pytest.fixture(scope="module")
def tsptw_problem():
    """Generates a TSP with Time Windows (TSPTW) problem for 50 cities."""
    import random

    random.seed(42)
    num_cities = 50

    # Generate random city data
    cities = {i: (random.randint(0, 100), random.randint(0, 100)) for i in range(num_cities)}
    service_times = {i: random.randint(5, 15) for i in range(num_cities)}
    time_windows = {i: (random.randint(0, 400), random.randint(500, 1000)) for i in range(num_cities)}
    time_windows[0] = (0, 1000)  # Depot

    def dist(p1, p2):
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

    travel_times = {(i, j): dist(cities[i], cities[j]) for i in cities for j in cities if i != j}

    # Variables
    variables = []
    # x_i_j = 1 if traveling from i to j
    for i in range(num_cities):
        for j in range(num_cities):
            if i != j:
                variables.append({"name": f"x_{i}_{j}", "cat": "Integer", "lowBound": 0, "upBound": 1})
    # t_i = arrival time at city i
    for i in range(num_cities):
        variables.append({"name": f"t_{i}", "cat": "Continuous", "lowBound": time_windows[i][0], "upBound": time_windows[i][1]})

    # Objective: Minimize total travel time
    objective = {
        "name": "total_travel_time",
        "coefficients": [{"name": f"x_{i}_{j}", "value": travel_times[i, j]} for i, j in travel_times],
    }

    # Constraints
    constraints = []
    # Visit each city exactly once
    for j in range(num_cities):
        constraints.append(
            {
                "name": f"enter_{j}",
                "sense": 0,
                "coefficients": [{"name": f"x_{i}_{j}", "value": 1} for i in range(num_cities) if i != j],
                "constant": -1,
            }
        )
    for i in range(num_cities):
        constraints.append(
            {
                "name": f"leave_{i}",
                "sense": 0,
                "coefficients": [{"name": f"x_{i}_{j}", "value": 1} for j in range(num_cities) if i != j],
                "constant": -1,
            }
        )

    # Time window and subtour elimination constraints
    big_m = 2 * max(tw[1] for tw in time_windows.values())
    for i in range(num_cities):
        for j in range(1, num_cities):  # No constraint for returning to depot 0
            if i != j:
                constraints.append(
                    {
                        "name": f"timewindow_{i}_{j}",
                        "sense": -1,
                        "coefficients": [
                            {"name": f"t_{i}", "value": 1},
                            {"name": f"t_{j}", "value": -1},
                            {"name": f"x_{i}_{j}", "value": big_m},
                        ],
                        "constant": -(big_m - service_times[i] - travel_times[i, j]),
                    }
                )

    return {
        "parameters": {"name": "tsptw_50", "sense": 1, "status": 0, "sol_status": 0},
        "objective": objective,
        "variables": variables,
        "constraints": constraints,
    }


def test_solve_with_invalid_timeout_returns_error(real_solver_client, simple_problem):
    """
    Tests that providing a negative timeout results in a 422 Unprocessable Entity error.
    """
    response = real_solver_client.post("/solve?timeout=-1", json=simple_problem)
    assert response.status_code == 422


def test_solve_with_timeout_triggers(real_solver_client, tsptw_problem):
    """
    Tests that the solver stops early when a timeout is provided.
    """
    # This TSPTW problem is NP-hard and will not solve to optimality in 1 second
    response = real_solver_client.post("/solve?timeout=1", json=tsptw_problem)
    assert response.status_code == 200
    solution = response.json()
    # The status should be 'timelimit' because the solver was interrupted
    assert solution["status"] == "timelimit"
