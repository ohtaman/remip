# Task List: Server-Side Solver Timeout

This document breaks down the implementation of the server-side timeout feature into a series of actionable tasks for the developer.

## 1. Environment Setup

- [x] Ensure you are on the `feature/support-timeout` branch.

## 2. Server-Side Implementation (`remip`)

-   **Task 2.1: Update API Endpoint**
    -   **File**: `remip/src/remip/main.py`
    -   **Action**: Modify the signature of the `solve` function to accept an optional `timeout` query parameter with validation.
    -   **Details**: Use `timeout: Optional[float] = Query(None, ge=0, description="...")`.
    -   **Action**: Pass the received `timeout` value to the `MIPSolverService` methods.

-   **Task 2.2: Update Service Layer**
    -   **File**: `remip/src/remip/services.py`
    -   **Action**: Update the signatures of `solve` and `solve_stream` to accept the `timeout: Optional[float]` parameter.
    -   **Action**: Pass the `timeout` value down to the `self.solver` methods.

-   **Task 2.3: Implement Core Timeout Logic**
    -   **File**: `remip/src/remip/solvers/scip_wrapper.py`
    -   **Action**: Update the signatures of `solve` and `solve_and_stream_events` to accept the `timeout: Optional[float]` parameter.
    -   **Action**: In `solve_and_stream_events`, if `timeout` is provided, create and manage an `asyncio` watchdog task that calls `model.interruptSolve()` after the specified duration.
    -   **Action**: In `_extract_solution`, check for the `"userinterrupt"` status from the solver and map it to `"timelimit"` in the returned `MIPSolution`.

## 3. Client-Side Implementation (`remip-client`)

-   **Task 3.1: Update Solver Initialization**
    -   **File**: `remip-client/src/remip_client/solver.py`
    -   **Action**: Update the `ReMIPSolver.__init__` method to accept and store a `timeout=None` parameter.

-   **Task 3.2: Pass Timeout in Request**
    -   **File**: `remip-client/src/remip_client/solver.py`
    -   **Action**: In the `solve` method, dynamically build the request URL and parameters. If `self.timeout` is set, add it as a query parameter to the request.

## 4. Testing

-   **Task 4.1: Implement Client Unit Test**
    -   **File**: `remip-client/tests/test_solver.py`
    -   **Action**: Add the `test_solve_with_timeout_sends_query_param` test case. Use `requests_mock` to assert that the request URL contains the correct `timeout` query parameter.

-   **Task 4.2: Implement Server Integration Tests**
    -   **File**: `remip/tests/test_timeout.py` (create this new file).
    -   **Action**: Add a helper function to generate a time-consuming knapsack problem.
    -   **Action**: Implement the `test_solve_with_timeout_triggers` test case.
    -   **Action**: Implement the `test_solve_without_timeout_completes_optimally` test case.
    -   **Action**: Implement the `test_solve_with_invalid_timeout_returns_error` test case.

-   **Task 4.3: Run All Tests**
    -   **Action**: Execute the full test suites for both `remip` and `remip-client` projects and ensure all tests pass.

## 5. Finalization

-   **Task 5.1: Code Review**
    -   **Action**: Create a pull request and ask for a review of the changes.

-   **Task 5.2: Merge**
    -   **Action**: Merge the `feature/support-timeout` branch into the main branch after approval.
