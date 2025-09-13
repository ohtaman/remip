# Final Technical Design: Server-Side Solver Timeout

## 1. Overview

This document outlines the final technical design for implementing a server-side solver timeout. This design has been refined based on feedback to ensure a clean separation between the problem definition and solver control parameters. The timeout will be managed by the `remip` server and passed as a URL query parameter in API requests.

## 2. Proposed Changes

### 2.1. `remip-client` (`remip-client/src/remip_client/solver.py`)

- **`ReMIPSolver.__init__`**: The constructor will be updated to accept a `timeout` parameter, which will be stored on the instance.
  ```python
  def __init__(self, base_url="http://localhost:8000", stream=True, timeout=None, **kwargs):
      super().__init__(**kwargs)
      self.base_url = base_url
      self.stream = stream
      self.timeout = timeout
  ```

- **`ReMIPSolver.solve`**: The request URL will be dynamically constructed to include the `timeout` as a query parameter if it has been set. This will apply to both streaming and non-streaming requests.

  ```python
  # Example modification in solve method
  url = f"{self.base_url}/solve"
  params = {}
  if self.stream:
      params['stream'] = 'sse'
  if self.timeout is not None:
      params['timeout'] = self.timeout

  response = requests.post(
      url,
      params=params,
      json=problem_dict,
      # ...
  )
  ```

### 2.2. `remip` Server

#### 2.2.1. API Endpoint (`remip/src/remip/main.py`)

- The `/solve` endpoint will be updated to accept an optional `timeout` float value from a query parameter. FastAPI's `Query` will be used to add validation (e.g., must be greater than or equal to zero).

  ```python
  from fastapi import Depends, FastAPI, Query, Request

  # ...

  @app.post("/solve")
  async def solve(
      request: Request,
      problem: MIPProblem,
      service: MIPSolverService = Depends(get_solver_service),
      timeout: Optional[float] = Query(None, ge=0, description="Maximum solver time in seconds")
  ):
      # ... pass timeout to service layer
  ```

#### 2.2.2. Model (`remip/src/remip/models.py`)

- **No changes** will be made to the `MIPProblem` model, keeping it clean of solver-specific control parameters.

#### 2.2.3. Service Layer (`remip/src/remip/services.py`)

- The service methods will be updated to accept the `timeout` and pass it down to the solver wrapper.

  ```python
  # Example modification in MIPSolverService
  async def solve(self, problem_data: MIPProblem, timeout: Optional[float] = None) -> MIPSolution:
      return await self.solver.solve(problem_data, timeout=timeout)

  async def solve_stream(self, problem_data: MIPProblem, timeout: Optional[float] = None) -> AsyncGenerator[SolverEvent, None]:
      async for event in self.solver.solve_and_stream_events(problem_data, timeout=timeout):
          yield event
  ```

#### 2.2.4. Solver Wrapper (`remip/src/remip/solvers/scip_wrapper.py`)

- The core server-side timeout logic will be implemented here.
- The `solve_and_stream_events` method will accept the `timeout` value.
- If a timeout is provided, an `asyncio` watchdog task will be started. This task will sleep for the specified duration.
- If the watchdog's sleep completes before the solver finishes, it will call `model.interruptSolve()` in a thread-safe manner to gracefully stop the optimization process.
- The `_extract_solution` method will check the solver status. If the status is `"userinterrupt"` (the result of calling `interruptSolve()`), it will be mapped to our application's `"timelimit"` status in the final `MIPSolution`.

## 3. Data Flow Example

1.  A user calls `ReMIPSolver(timeout=60).solve(problem)`.
2.  The client sends a `POST` request to `http://localhost:8000/solve?timeout=60`.
3.  The server's `/solve` endpoint receives the request, extracting the `MIPProblem` from the body and the `timeout` from the query parameters.
4.  The `timeout` value is passed through the service layer to the `ScipSolverWrapper`.
5.  The wrapper starts the solver in a background thread and concurrently starts a 60-second watchdog timer.
6.  If 60 seconds pass, the watchdog interrupts the solver.
7.  The wrapper catches the interruption, checks the solver status (`"userinterrupt"`), and creates a `MIPSolution` with `"status": "timelimit"`.
8.  The server sends this solution back to the client.
