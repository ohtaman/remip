# ReMIP: Remote Execution for Mixed-Integer Programming

**ReMIP** also stands for **R**emote **E**xecution **M**akes **I**deals **P**ossible.

This project provides a FastAPI-based web service for solving Mixed-Integer Programming (MIP) problems, with a dedicated Python client for seamless integration.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the API](#running-the-api)
- [Usage](#usage)
  - [API Endpoints](#api-endpoints)
  - [Python Client](#python-client)
- [Testing](#testing)
- [Docker](#docker)
- [Releasing](#releasing)
- [Contributing](#contributing)
- [License](#license)

---

## Features

-   **RESTful API**: Solve MIP problems via a clean and modern API.
-   **Real-time Logging**: Stream solver logs in real-time to monitor progress.
-   **Dedicated Python Client**: A `remip-client` library for easy integration with PuLP.
-   **Powered by PySCIPOpt**: Directly integrates with the SCIP optimization suite through its Python API for better performance and stability.
-   **Containerized**: Comes with a Docker setup for easy and consistent deployment.

---

## Project Structure

This repository is a monorepo containing two main packages:

-   `remip/`: The FastAPI server application.
-   `remip-client/`: The Python client library.

Both packages follow the standard `src` layout for clean and maintainable code.

---

## Getting Started

### Prerequisites

-   **SCIP Optimization Suite**: This project uses `pyscipopt`, which requires a working installation of the SCIP Optimization Suite. You can download it from the [official SCIP website](https://scipopt.org/index.php#download). Please follow their installation instructions.
-   Python 3.11+
-   [uv](https://github.com/astral-sh/uv): A fast Python package installer.
-   [Docker](https://www.docker.com/): For running the application in a container.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd remip
    ```
    *(Note: You might need to rename the root folder from `mip-api` to `remip`)*

2.  **Create a virtual environment:**
    ```bash
    uv venv
    ```

3.  **Install the Server and its dependencies:**
    ```bash
    # This command installs the server and test dependencies
    uv pip install -e .[test]
    ```

4.  **Install the Client:**
    ```bash
    # Navigate to the client directory and install it
    cd remip-client
    uv pip install -e .
    cd ..
    ```

### Running the API

To run the API server locally with hot-reloading:

```bash
uvicorn remip.main:app --reload
```

The API will be available at `http://localhost:8000`.

---

## Usage

### API Endpoints

-   `POST /solve`: Submits a MIP problem and returns the final solution.
-   `POST /solve-stream`: Submits a MIP problem and streams the solver logs.
-   `GET /solver-info`: Returns information about the configured solver.

### Python Client

The `remip-client` library provides a PuLP-compatible solver interface.

### Pyodide Support

The client can be used in a Pyodide environment to solve MIP problems in the browser. To use the client in a Pyodide environment, install it with the `pyodide` extra:

```bash
micropip.install("remip-client[pyodide]")
```

**Example:**

```python
from pulp import LpProblem, LpVariable, lpSum, LpMaximize
from remip_client.solver import MipApiSolver

# 1. Define a problem
prob = LpProblem("test_problem", LpMaximize)
x = LpVariable("x", 0, 1, cat='Binary')
y = LpVariable("y", 0, 1, cat='Binary')
prob += x + y, "objective"
prob += 2*x + y <= 2, "constraint1"

# 2. Initialize the remote solver
with MipApiSolver(base_url="http://localhost:8000") as solver:
    # 3. Solve the problem via the API
    prob.solve(solver)

from pulp import LpProblem, LpVariable, lpSum, LpMaximize, LpStatus

# 1. Define a problem
prob = LpProblem("test_problem", LpMaximize)
x = LpVariable("x", 0, 1, cat='Binary')
y = LpVariable("y", 0, 1, cat='Binary')
prob += x + y, "objective"
prob += 2*x + y <= 2, "constraint1"

# 2. Initialize the remote solver
with MipApiSolver(base_url="http://localhost:8000") as solver:
    # 3. Solve the problem via the API
    prob.solve(solver)

# 4. Print the results
print(f"Status: {LpStatus[prob.status]}")
for v in prob.variables():
    print(f"{v.name} = {v.varValue}")
```

---

## Testing

### Automated Test Suite

The project includes a full suite of automated tests for both the server and the CPython client.

To run the full test suite:

```bash
uv run pytest
```

### Manual Browser Test

The `remip-client` includes an integration test that runs in the browser using Pyodide. This test solves a small MIP problem by communicating with the live server from a web page.

To run the browser test:

1.  **Start the API Server:** Make sure the ReMIP server is running.
    ```bash
    uvicorn src.remip.main:app --host 0.0.0.0 --port 8000
    ```

2.  **Build the Client Wheel:** The test page needs the `remip-client` package built as a wheel file.
    ```bash
    # From the project root directory
    cd remip-client
    python -m build --wheel
    cd ..
    ```

3.  **Access the Test Page:** The main server also hosts the client files. Open your web browser and navigate to:
    [http://localhost:8000/test_pyodide.html](http://localhost:8000/test_pyodide.html)

4.  **Check the Console:** Open your browser's developer console. You should see the output of the test, including the final solution and a "Test assertions passed" message.

### Node.js (Pyodide) Test

This project also includes a test to verify that the `remip-client` works in a Node.js environment using Pyodide.

**Setup:**

1.  Navigate to the test directory:
    ```bash
    cd remip-client/tests/node
    ```
2.  Install the Node.js dependencies:
    ```bash
    npm install
    ```

**Running the Test:**

1.  **Start the API Server:** Make sure the ReMIP server is running in another terminal.
    ```bash
    # From the project root
    uvicorn src.remip.main:app --host 0.0.0.0 --port 8000
    ```

2.  **Build the Client Wheel:** The test needs the `remip-client` package built as a wheel file.
    ```bash
    # From the project root
    cd remip-client
    python -m build --wheel
    cd ..
    ```

3.  **Run the Node.js Test:** Execute the test script using the following command from the project root. The `--experimental-wasm-stack-switching` flag is required by Pyodide.
    ```bash
    # From the project root
    node --experimental-wasm-stack-switching remip-client/tests/node/index.js
    ```

4.  You should see "--- Node.js Test Succeeded! --- " if the test passes.

---

## Docker

To build and run the application using Docker:

```bash
docker-compose build
docker-compose up
```

---

## Releasing

This project uses [GitHub Actions](https://github.com/features/actions) to automate the release process.

A new release is created automatically whenever a new tag is pushed to the repository that starts with `v` (e.g., `v1.0.0`, `v1.1.0-alpha`).

The release workflow will:
1.  Build the server and client packages.
2.  Create a new GitHub Release with the tag name.
3.  Upload the built packages as assets to the release.

---

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

---

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
<!-- Test commit to trigger pre-commit hook -->
