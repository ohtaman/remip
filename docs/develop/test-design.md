# Test Design: Server-Side Solver Timeout

## 1. Overview

This document outlines the testing strategy for the server-side solver timeout feature, based on the final approved design. The tests will validate that the `timeout` is correctly passed as a URL query parameter and that the server enforces the timeout correctly.

## 2. `remip-client` Unit Tests

**Location**: `remip-client/tests/test_solver.py`

### Test Case: `test_solve_with_timeout_sends_query_param`

- **Objective**: Verify that the `timeout` value set on the `ReMIPSolver` instance is correctly sent as a query parameter in the API request.
- **Setup**:
    1.  Instantiate `ReMIPSolver` with a timeout value, e.g., `solver = ReMIPSolver(timeout=60)`.
    2.  Use `requests_mock` to intercept the `POST` request.
- **Action**:
    1.  Call `solver.solve()` on a sample PuLP problem.
- **Assertions**:
    1.  Verify that the URL the request was sent to includes the `timeout` query parameter (e.g., `http://localhost:8000/solve?stream=sse&timeout=60`).

## 3. `remip` Integration Tests

**Location**: `remip/tests/test_timeout.py` (a new file)

These end-to-end tests will use a real `TestClient` without a mocked service to ensure the entire workflow, including the server-side watchdog, functions correctly.

### Test Setup

- A helper function will be created to generate a knapsack-style integer programming problem, which can be scaled to be time-consuming.
- The `TestClient` will be instantiated without overriding the `get_solver_service` dependency.

### Test Case: `test_solve_with_timeout_triggers`

- **Objective**: Verify that the solver terminates early and returns a `timeout` status when the timeout is reached.
- **Setup**:
    1.  Construct a knapsack problem that takes several seconds to solve.
- **Action**:
    1.  Send a `POST` request to the `/solve?timeout=1` endpoint with the problem in the request body.
- **Assertions**:
    1.  The HTTP status code must be `200`.
    2.  The `status` field in the JSON response must be `"timelimit"`.

### Test Case: `test_solve_without_timeout_completes_optimally`

- **Objective**: Ensure the solver runs to completion when no timeout is specified.
- **Setup**:
    1.  Use the same knapsack problem.
- **Action**:
    1.  Send a `POST` request to the `/solve` endpoint (with no query parameter).
- **Assertions**:
    1.  The HTTP status code must be `200`.
    2.  The `status` field in the JSON response must be `"optimal"`.

### Test Case: `test_solve_with_invalid_timeout_returns_error`

- **Objective**: Verify that the API validation for the `timeout` parameter works correctly.
- **Setup**:
    1.  Use any valid problem payload.
- **Action**:
    1.  Send a `POST` request to the `/solve?timeout=-5` endpoint.
- **Assertions**:
    1.  The HTTP status code must be `422 Unprocessable Entity`, as the `timeout` must be greater than or equal to 0.

This test plan ensures that the client correctly formats the request, the API validates the input, and the server-side timeout logic is robust and effective.
