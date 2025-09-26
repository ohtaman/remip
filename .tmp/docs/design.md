# Technical Design: Kill Solver on HTTP Disconnect

## 1. Introduction
This document details the technical design for implementing the termination of SCIP solver processes upon HTTP client disconnection. It addresses the functional and non-functional requirements outlined in the `requirements.md` document.

## 2. High-Level Design
The core idea is to leverage FastAPI's request lifecycle and Python's `asyncio` capabilities to monitor the client connection. When a disconnection is detected, a signal will be sent to the separate thread running the SCIP solver to initiate its termination.

## 3. Detailed Design

### 3.1. Detecting Client Disconnection (FR1)
FastAPI provides a mechanism to detect client disconnections through the `Request.is_disconnected()` method or by awaiting `Request.is_disconnected()` in an `async` context. We will use `Request.is_disconnected()` within a background task.

### 3.2. Terminating Solver Process (FR2)

#### 3.2.1. Solver Thread Management
The `ScipSolverWrapper` already runs the `model.optimize()` call in a separate `threading.Thread`. This thread needs a way to receive a termination signal.

#### 3.2.2. PySCIPOpt Termination
PySCIPOpt models can be interrupted using `model.interruptSolve()`. This method can be called from a different thread than the one running `optimize()`.

#### 3.2.3. Implementation Flow
1.  In `MIPSolverService.solve_stream` (or `solve`), when a solver process is initiated, a `threading.Event` (e.g., `disconnect_event`) will be created and passed to the `ScipSolverWrapper`.
2.  The `ScipSolverWrapper` will pass this `disconnect_event` to its internal solver thread (`_run_solver_in_thread`).
3.  A new `asyncio` background task will be created in `MIPSolverService` (or `main.py` if more appropriate) that `await`s `request.is_disconnected()`.
4.  Once `request.is_disconnected()` returns `True`, this background task will set the `disconnect_event`.
5.  The `_run_solver_in_thread` function will periodically check `disconnect_event.is_set()`. If set, it will call `model.interruptSolve()`.

### 3.3. Resource Cleanup (FR3)
*   `model.interruptSolve()` is designed to gracefully stop the solver, which should handle most internal resource cleanup.
*   Python's garbage collection will handle the release of Python objects. No explicit manual cleanup beyond `model.interruptSolve()` is anticipated.

### 3.4. Graceful Handling of Solver Completion (FR4)
*   The `_run_solver_in_thread` will continue to run until `model.optimize()` completes or is interrupted. If `model.optimize()` completes normally, `stop_event` will be set, and the `disconnect_event` check will become irrelevant.
*   The `solve_and_stream_events` generator will correctly yield `ResultEvent` or `EndEvent` based on the solver's actual completion status.

### 3.5. Error Logging (FR5)
*   When `disconnect_event` is set and `model.interruptSolve()` is called, a `LogEvent` will be yielded (or logged internally) indicating that the solver was terminated due to client disconnection.

## 4. Non-Functional Considerations

### 4.1. Performance (NFR1)
*   `Request.is_disconnected()` is non-blocking. Checking `disconnect_event.is_set()` in the solver thread is a low-overhead operation.
*   The background task for disconnection detection will run concurrently with the main request handling, minimizing impact.

### 4.2. Reliability (NFR2)
*   Using `threading.Event` and `model.interruptSolve()` provides a reliable mechanism for cross-thread communication and solver termination.

### 4.3. Scalability (NFR3)
*   The design uses per-request background tasks and thread-safe events, which scales well with concurrent requests.

### 4.4. Security (NFR4)
*   The termination signal is internal to the application and tied to the specific request, preventing unauthorized process termination.

## 5. Open Questions / Future Work
*   Consider if `model.interruptSolve()` is sufficient for all scenarios or if a more forceful `os.kill` might be needed for unresponsive solvers (though `interruptSolve` is preferred for graceful shutdown).
*   Refine logging messages for clarity and debuggability.
