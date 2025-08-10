# remip

This project provides a FastAPI-based web service for solving Mixed-Integer Programming (MIP) problems. It also includes a Python client library that integrates with the PuLP modeling language.

## Features

- Solve MIP problems via a REST API.
- Real-time streaming of solver logs.
- Python client library for easy integration with PuLP.
- Powered by the SCIP solver.
- Containerized with Docker for easy deployment.

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (for package management)
- Docker (for running the containerized application)

### Installation

1.  **Clone the repository (and rename the root directory):**
    ```bash
    git clone <repository-url>
    mv mip-api remip
    cd remip
    ```

2.  **Set up the environment:**
    ```bash
    uv venv
    ```

3.  **Install the Server:**
    To install the server with its dependencies, run the following command from the root of the project:
    ```bash
    uv pip install -e .[test]
    ```

4.  **Install the Client:**
    To install the client library, navigate to the `remip-client` directory and install it:
    ```bash
    cd remip-client
    uv pip install -e .
    cd ..
    ```

### Running the API

To run the API server locally, use the following command:

```bash
uvicorn remip.main:app --reload
```

The API will be available at `http://localhost:8000`.

## Usage

### API Endpoints

-   `POST /solve`: Submits a MIP problem for solving. The request body should be a JSON object representing the problem, compatible with PuLP's `toDict()` method.
-   `GET /solve-stream`: Submits a problem and streams the solver logs in real-time.
-   `GET /solver-info`: Returns information about the configured solver.

### Python Client

The `remip-client` library provides a PuLP-compatible solver interface.

**Example:**

```python
from pulp import LpProblem, LpVariable, lpSum, LpMinimize
from remip_client.solver import MipApiSolver

# 1. Create a problem
prob = LpProblem("test_problem", LpMinimize)
x = LpVariable("x", 0, 1)
y = LpVariable("y", 0, 1)
prob += x + y, "objective"
prob += 2*x + y <= 1, "constraint1"

# 2. Create the solver
solver = MipApiSolver(base_url="http://localhost:8000")

# 3. Solve the problem
prob.solve(solver)

# 4. Print the results
print(f"Status: {prob.status}")
for v in prob.variables():
    print(f"{v.name} = {v.varValue}")
```

## Testing

To run the test suite, use the following command:

```bash
uv run pytest
```

## Docker

To build and run the application with Docker, use the following commands:

```bash
docker-compose build
docker-compose up
```
