# Task List: Kill Solver on HTTP Disconnect

## 1. Introduction
This document outlines the implementable tasks for integrating the solver termination mechanism upon HTTP client disconnection, based on the approved requirements, technical design, and test design.

## 2. Implementation Tasks

### 2.1. Core Logic Implementation

#### Task 2.1.1: Modify `MIPSolverService.solve_stream` to pass `disconnect_event`
*   **Description:** Introduce a `threading.Event` (`disconnect_event`) in `MIPSolverService.solve_stream` and pass it to `ScipSolverWrapper.solve_and_stream_events`.
*   **Files:** `remip/src/remip/services.py`

#### Task 2.1.2: Modify `ScipSolverWrapper.solve_and_stream_events` to accept `disconnect_event`
*   **Description:** Update the signature of `solve_and_stream_events` to accept `disconnect_event`.
*   **Files:** `remip/src/remip/solvers/scip_wrapper.py`

#### Task 2.1.3: Pass `disconnect_event` to `_run_solver_in_thread`
*   **Description:** Pass the `disconnect_event` from `solve_and_stream_events` to the `_run_solver_in_thread` function.
*   **Files:** `remip/src/remip/solvers/scip_wrapper.py`

#### Task 2.1.4: Implement periodic check and `interruptSolve` in `_run_solver_in_thread`
*   **Description:** Modify `_run_solver_in_thread` to periodically check `disconnect_event.is_set()` and call `model.interruptSolve()` if the event is set.
*   **Files:** `remip/src/remip/solvers/scip_wrapper.py`

#### Task 2.1.5: Implement client disconnection detection in `MIPSolverService`
*   **Description:** Create an `asyncio` background task in `MIPSolverService.solve_stream` that `await`s `request.is_disconnected()` and sets `disconnect_event` when `True`.
*   **Files:** `remip/src/remip/services.py`

#### Task 2.1.6: Add logging for solver termination due to disconnection
*   **Description:** Log an informative message when the solver is terminated due to client disconnection.
*   **Files:** `remip/src/remip/solvers/scip_wrapper.py`

### 2.2. Test Implementation

#### Task 2.2.1: Implement Unit Test TC-UT-001
*   **Description:** Create a unit test to verify `_run_solver_in_thread` calls `model.interruptSolve()` when signaled.
*   **Files:** `remip/tests/test_solver_wrapper.py` (or a new test file)

#### Task 2.2.2: Implement Unit Test TC-UT-002
*   **Description:** Create a unit test to verify `_run_solver_in_thread` does not call `model.interruptSolve()` without a signal.
*   **Files:** `remip/tests/test_solver_wrapper.py` (or a new test file)

#### Task 2.2.3: Implement Integration Test TC-IT-001
*   **Description:** Create an integration test for client disconnection during streaming solve.
*   **Files:** `remip/tests/test_api.py` (or a new test file)

#### Task 2.2.4: Implement Integration Test TC-IT-002
*   **Description:** Create an integration test for client staying connected during streaming solve.
*   **Files:** `remip/tests/test_api.py` (or a new test file)

#### Task 2.2.5: Implement Integration Test TC-IT-003
*   **Description:** Create an integration test for client disconnection during non-streaming solve.
*   **Files:** `remip/tests/test_api.py` (or a new test file)

#### Task 2.2.6: Implement Integration Test TC-IT-004
*   **Description:** Create an integration test for server responsiveness after disconnection.
*   **Files:** `remip/tests/test_api.py` (or a new test file)

## 3. Documentation Updates

#### Task 3.1.1: Update `README.md` (if necessary)
*   **Description:** Add a note about the solver termination feature.
*   **Files:** `remip/README.md`

## 4. Review and Refinement

#### Task 4.1.1: Code Review
*   **Description:** Review implemented code for adherence to design, style, and best practices.

#### Task 4.1.2: Test Review
*   **Description:** Review implemented tests for coverage and correctness.
