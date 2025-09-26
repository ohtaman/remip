# Task List: Pyodide (Node.js) Support

This document breaks down the work required to implement Pyodide support for `remip-client` in a Node.js environment.

## Phase 1: Core Implementation

-   [ ] **Task 1.1: Create New Modules**
    -   Create the following empty files:
        -   `remip-client/src/remip_client/environment.py`
        -   `remip-client/src/remip_client/http_client.py`

-   [ ] **Task 1.2: Implement Environment Detection**
    -   In `environment.py`, implement the `get_environment()` function to detect `cpython`, `pyodide-node`, and `pyodide-browser` environments.

-   [ ] **Task 1.3: Implement `HttpClient` Abstraction**
    -   In `http_client.py`, define the `HttpClient` abstract base class with an abstract `post` method and a `close` method.

-   [ ] **Task 1.4: Implement `RequestsHttpClient`**
    -   In `http_client.py`, create the `RequestsHttpClient` class that inherits from `HttpClient`.
    -   It should wrap a `requests.Session` to handle requests in a CPython environment.

-   [ ] **Task 1.5: Implement `PyodideHttpClient`**
    -   In `http_client.py`, create the `PyodideHttpClient` class.
    -   Implement the `post` method which uses `pyodide.ffi.run_sync` to call an internal `_post_async` method.
    -   The `_post_async` method will use `js.fetch` to make the actual HTTP request.

-   [ ] **Task 1.6: Create a `PyodideResponse` Wrapper**
    -   In `http_client.py`, create a response wrapper class for the `js.fetch` response.
    -   Implement a `json()` method that correctly awaits the JavaScript promise.
    -   Implement an `ok` property and a `raise_for_status()` method.

-   [ ] **Task 1.7: Implement Streaming `iter_lines` for Pyodide**
    -   In the `PyodideResponse` wrapper, implement a synchronous `iter_lines` method.
    -   This method must internally handle the asynchronous JavaScript `ReadableStream` from the `fetch` response and yield decoded lines synchronously. This is a complex task.

-   [ ] **Task 1.8: Integrate `HttpClient` into `ReMIPSolver`**
    -   In `remip_client/solver.py`, modify the `__init__` method to use `get_environment()` and instantiate the correct `HttpClient`.
    -   Replace all `requests.post` calls with `self._client.post`.
    -   Add a `__del__` method to the solver to call `self._client.close()`.

## Phase 2: Testing

-   [ ] **Task 2.1: Implement CPython Unit Tests**
    -   Create `remip-client/tests/test_environment.py` and test the `get_environment` function.
    -   Create `remip-client/tests/test_http_client.py` to test the instantiation logic of the clients.

-   [ ] **Task 2.2: Refactor Existing Solver Tests**
    -   Update `remip-client/tests/test_solver.py`.
    -   Modify the tests to mock `remip_client.http_client.RequestsHttpClient` instead of mocking the `requests` library directly.
    -   Ensure all existing tests pass after the refactoring.

-   [ ] **Task 2.3: Create Node.js Test Runner**
    -   Create a new file: `remip-client/tests/node/test_solver_pyodide.js`.
    -   In this file, write the JavaScript code to:
        1.  Load the Pyodide module.
        2.  Monkeypatch the global `fetch` API to return mock responses.
        3.  Load the `remip-client` wheel using `micropip`.
        4.  Execute a Python test script.

-   [ ] **Task 2.4: Create Python Test Script for Node.js**
    -   Create a new Python file (e.g., `remip-client/tests/node/py_tests.py`).
    -   In this file, write the Python test functions (`test_node_streaming_solve`, `test_node_non_streaming_solve`, etc.) that will be called by the Node.js runner.
    -   These tests will use `ReMIPSolver` to solve problems and assert the results are correct based on the mocked `fetch` responses.

## Phase 3: Finalization

-   [ ] **Task 3.1: Update Documentation**
    -   Update the main `README.md` to include instructions on how to use the library in a Pyodide/Node.js environment.

-   [ ] **Task 3.2: Manual Verification**
    -   Perform a full manual test run:
        1.  Run all CPython tests with `pytest`.
        2.  Build the wheel.
        3.  Run the Node.js tests.
    -   Ensure all tests pass and the client is fully functional.
