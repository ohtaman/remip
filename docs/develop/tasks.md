# Implementation Tasks for API Refactoring

Based on the updated `design.md`, the following tasks need to be completed to refactor the API.

## 1. Refactor API Endpoints (`main.py`)

- [x] Remove the `GET /solve-stream` endpoint.
- [x] Update the `POST /solve` endpoint to handle both standard JSON responses and streaming responses.
- [x] Implement logic to check for the `stream` query parameter or the `Accept: text/event-stream` header to determine the response type.

## 2. Refactor MIP Solver Service (`services.py`)

- [x] Consolidate the `solve_problem` and `solve_problem_stream` methods into a single method that can be used for both streaming and non-streaming responses.
- [x] The new method should return an async generator.

## 3. Update API Tests (`tests/test_api.py`)

- [x] Remove tests for the deprecated `/solve-stream` endpoint.
- [x] Add new tests for the `POST /solve` endpoint to verify both standard and streaming responses.
- [x] Ensure tests cover the `stream` query parameter and `Accept` header functionality.

## 4. Update Client Library (`remip-client`)

- [x] Update the client in `remip-client/src/remip_client/solver.py` to use the new unified `/solve` endpoint.
- [x] Add support for handling streaming responses in the client.
- [x] Update client tests in `remip-client/tests/test_solver.py`.

## 5. Documentation

- [x] Update the `README.md` and any other relevant documentation to reflect the API changes.
- [x] Ensure the examples show how to use the new unified endpoint for both response types.

## 6. Code Cleanup

- [x] Remove any dead code related to the old streaming implementation.
- [x] Ensure the codebase adheres to the style guide (run `ruff format .` and `ruff check . --fix`).
- [x] Verify all tests pass.
- [x] Create a pull request with the changes.
- [x] Delete the feature branch after merging.
- [x] Close the related issue.

## 7. Implement SSE Event Stream Response

- [ ] **Modify `MIP Solver Service` (`services.py`):**
    - [ ] Update the solver service's streaming method to yield structured data (dictionaries or Pydantic models) for logs, metrics, results, and end events, instead of just raw log lines.
    - [ ] Create Pydantic models in `models.py` for the different SSE event data structures (`LogEvent`, `MetricEvent`, `ResultEvent`, `EndEvent`).
- [ ] **Update API Endpoint (`main.py`):**
    - [ ] Modify the `POST /solve` endpoint's streaming logic.
    - [ ] It should take the structured data from the service and format it into the correct `event: <type>` and `data: <json>` SSE string format.
- [ ] **Update `SCIP Solver Wrapper` (`solvers/scip_wrapper.py`):**
    - [ ] Modify the wrapper to parse the raw SCIP solver output.
    - [ ] It needs to identify and extract different types of information (presolve logs, progress metrics, final solution) and yield them as distinct event types.
- [ ] **Update API Tests (`tests/test_api.py`):**
    - [ ] Update the streaming tests to validate the new SSE event structure.
    - [ ] Add tests to ensure each event type (`log`, `metric`, `result`, `end`) is received correctly with the expected JSON payload.
- [ ] **Update Client Library (`remip-client`):**
    - [ ] Update the client to parse the SSE events.
    - [ ] The client should be able to handle the different event types and extract their data.
    - [ ] Update client tests to reflect these changes.
