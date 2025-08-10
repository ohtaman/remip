# MIP Solver API

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

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd mip-api
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    uv venv
    uv sync --all-extras
    ```

### Running the API

To run the API server locally, use the following command:

```bash
uvicorn mip_api.main:app --reload
```

The API will be available at `http://localhost:8000`.

## Usage

### API Endpoints

-   `POST /solve`: Submits a MIP problem for solving. The request body should be a JSON object representing the problem, compatible with PuLP's `toDict()` method.
-   `GET /solve-stream`: Submits a problem and streams the solver logs in real-time.
-   `GET /solver-info`: Returns information about the configured solver.

### Python Client

The `mip-client` library provides a PuLP-compatible solver interface.

**Example:**

```python
from pulp import LpProblem, LpVariable, lpSum, LpMinimize
from mip_client.solver import MipApiSolver

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
