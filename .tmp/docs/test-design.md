# Test Design: Kill Solver on HTTP Disconnect

## 1. Introduction
This document outlines the test cases for verifying the functionality of terminating SCIP solver processes upon HTTP client disconnection, based on the requirements and technical design documents.

## 2. Test Strategy

### 2.1. Unit Tests
*   Focus: Individual components like `ScipSolverWrapper`'s ability to receive and act on termination signals.
*   Tools: `pytest`, `unittest.mock` for simulating `threading.Event` and `model.interruptSolve()`.

### 2.2. Integration Tests
*   Focus: Interaction between FastAPI, `MIPSolverService`, `ScipSolverWrapper`, and client disconnection detection.
*   Tools: `pytest`, `httpx` (for asynchronous client testing), `asyncio.sleep` for simulating delays.

## 3. Test Cases

### 3.1. Unit Test Cases

#### TC-UT-001: Solver Thread Termination Signal
*   **Objective:** Verify that `_run_solver_in_thread` correctly calls `model.interruptSolve()` when `disconnect_event` is set.
*   **Steps:**
    1.  Mock `pyscipopt.Model` and its `interruptSolve()` method.
    2.  Create a `threading.Event` instance (`disconnect_event`).
    3.  Call `_run_solver_in_thread` in a separate thread, passing the mocked model and `disconnect_event`.
    4.  After a short delay, set `disconnect_event`.
    5.  Assert that `model.interruptSolve()` was called.

#### TC-UT-002: Solver Thread Continues Without Signal
*   **Objective:** Verify that `_run_solver_in_thread` does not call `model.interruptSolve()` if `disconnect_event` is not set.
*   **Steps:**
    1.  Mock `pyscipopt.Model` and its `interruptSolve()` method.
    2.  Create a `threading.Event` instance (`disconnect_event`).
    3.  Call `_run_solver_in_thread` in a separate thread, passing the mocked model and `disconnect_event`.
    4.  Allow the thread to run for a period (simulating solver activity).
    5.  Assert that `model.interruptSolve()` was *not* called.

### 3.2. Integration Test Cases

#### TC-IT-001: Client Disconnects During Solve (Streaming)
*   **Objective:** Verify that the solver process is terminated when a streaming client disconnects prematurely.
*   **Steps:**
    1.  Start the FastAPI application.
    2.  Send a `POST /solve?stream=sse` request with a problem that takes a long time to solve.
    3.  Immediately close the client connection after receiving the initial headers/first event.
    4.  Monitor server logs to confirm that a log message indicating solver termination due to client disconnection is present.
    5.  (Optional) Attempt to make another request to the server to ensure it remains responsive.

#### TC-IT-002: Client Stays Connected Until Solve Completion (Streaming)
*   **Objective:** Verify that the solver process completes normally and is not terminated if the streaming client remains connected until the solve finishes.
*   **Steps:**
    1.  Start the FastAPI application.
    2.  Send a `POST /solve?stream=sse` request with a problem that solves within a reasonable time.
    3.  Keep the client connection open and consume all events until the `EndEvent`.
    4.  Monitor server logs to confirm that no log message indicating solver termination due to client disconnection is present.
    5.  Assert that the `ResultEvent` contains the expected solution.

#### TC-IT-003: Client Disconnects During Solve (Non-Streaming)
*   **Objective:** Verify that the solver process is terminated when a non-streaming client disconnects prematurely.
*   **Steps:**
    1.  Start the FastAPI application.
    2.  Send a `POST /solve` request with a problem that takes a long time to solve.
    3.  Immediately close the client connection.
    4.  Monitor server logs to confirm that a log message indicating solver termination due to client disconnection is present.

#### TC-IT-004: Server Responsiveness After Disconnection
*   **Objective:** Verify that the server remains responsive to new requests after a client disconnection and solver termination.
*   **Steps:**
    1.  Execute TC-IT-001 (client disconnects during solve).
    2.  After the solver is expected to be terminated, send a `GET /health` request.
    3.  Assert that the `/health` endpoint returns `200 OK`.

## 4. Future Test Considerations
*   Performance testing under high concurrency with disconnections.
*   Edge cases: very fast solves, immediate disconnections, network flakiness.
