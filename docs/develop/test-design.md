# Test Design: Pyodide Support for remip-client

## 1. Introduction

This document outlines the testing strategy for verifying the Pyodide compatibility of the `remip-client` library. The goal is to ensure that the client functions correctly and reliably in both the standard CPython environment and the Pyodide (browser) environment.

## 2. Testing Scope

### In Scope

-   **Unit Testing** of the new `HttpClient` abstraction and environment detection.
-   **Integration Testing** of the `ReMIPSolver` in a CPython environment, ensuring no regressions.
-   **Integration Testing** of the `ReMIPSolver` in a live Pyodide environment to validate the `PyodideHttpClient` implementation.
-   Verification of both **streaming (SSE)** and **non-streaming** communication in both environments.
-   Error handling for network failures and server-side errors.

### Out of Scope

-   Performance testing.
-   Testing of the `remip` backend server itself.
-   Automated browser testing in the CI/CD pipeline (this will be a manual step for now).

## 3. Testing Environments

-   **CPython**: The standard Python environment where tests will be run using `pytest`.
-   **Pyodide**: A browser-based environment using a local HTML file to load Pyodide, install the client, and execute tests.

## 4. CPython Unit & Integration Tests

Existing tests will be adapted, and new unit tests will be added to cover the new modules.

### 4.1. `test_environment.py` (New)

-   **Test Case**: `test_is_pyodide_false`
    -   **Description**: Verify that `is_pyodide()` returns `False` when run in the CPython test environment.
-   **Test Case**: `test_is_pyodide_true`
    -   **Description**: Verify that `is_pyodide()` returns `True` by mocking `sys.modules` to include `pyodide`.

### 4.2. `test_http_client.py` (New)

-   **Test Case**: `test_solver_instantiates_requests_client`
    -   **Description**: Verify that `ReMIPSolver` instantiates `RequestsHttpClient` when not in Pyodide.
-   **Test Case**: `test_solver_instantiates_pyodide_client`
    -   **Description**: Verify that `ReMIPSolver` instantiates `PyodideHttpClient` when `is_pyodide()` returns `True`.

### 4.3. `tests/test_solver.py` (Update)

-   **Description**: The existing tests that use `requests-mock` will be refactored. Instead of mocking `requests`, they will mock the `RequestsHttpClient` instance to return mock response objects. This ensures the core solver logic is tested independently of the HTTP client implementation.
-   **Test Cases to be preserved**:
    -   Successful non-streaming solve.
    -   Successful streaming solve.
    -   Server error handling.
    -   Infeasible/unbounded problem status handling.

## 5. Pyodide Integration Tests (Node.js)

These tests will be conducted using a Node.js script and the existing test infrastructure in `remip-client/tests/node/`.

### 5.1. Test Setup & Workflow

1.  **Build Wheel**: Build the `remip-client` package as a wheel (`.whl`) file.
    ```bash
    (cd remip-client && uv run hatch build)
    ```
2.  **Run Tests**: Execute a Node.js test script that will orchestrate the test run.
    ```bash
    (cd remip-client/tests/node && node test_solver_pyodide.js)
    ```

### 5.2. `test_solver_pyodide.js` (New File)

This Node.js script will perform the following actions:

1.  **Monkeypatch `fetch`**: Before loading Pyodide, the global `fetch` function will be replaced with a mock version that can simulate different server responses (e.g., success, error, streaming data) based on the request URL or body.
2.  **Load Pyodide**: Initialize a Pyodide instance.
3.  **Install Client**: Use `pyodide.loadPackage()` and `micropip.install()` to install the locally built `.whl` file.
4.  **Execute Python Test Code**: Run a Python script within Pyodide that defines and executes the test cases using the `ReMIPSolver`.

#### 5.2.1. Pyodide Python Test Cases

The Python code run by the Node.js script will contain the following tests:

-   **Test Case**: `test_node_non_streaming_solve`
    -   **Description**: Solves a simple problem in non-streaming mode. The mocked `fetch` will return a complete JSON solution.
    -   **Assert**: The problem status is `Optimal` and variable values are correct.

-   **Test Case**: `test_node_streaming_solve`
    -   **Description**: Solves a simple problem in streaming mode. The mocked `fetch` will return a `Response` with a `ReadableStream` body that yields SSE events.
    -   **Assert**: The problem status is `Optimal` and the final solution is parsed correctly.

-   **Test Case**: `test_node_network_error`
    -   **Description**: Simulates a network error by having the mocked `fetch` reject the promise.
    -   **Assert**: The solver status is `LpStatusNotSolved`.

-   **Test Case**: `test_node_server_error`
    -   **Description**: Simulates a 500 server error by having `fetch` return a response with `status = 500`.
    -   **Assert**: The solver status is `LpStatusNotSolved`.

## 6. Summary

This test plan provides comprehensive coverage for the new Pyodide feature. It validates the functionality in the target browser environment while ensuring no regressions occur in the standard CPython environment through a combination of unit and integration tests.
