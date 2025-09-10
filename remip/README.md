# ReMIP Server

**ReMIP** (Remote Execution for Mixed-Integer Programming) server is a FastAPI-based web service for solving Mixed-Integer Programming (MIP) problems.

## Overview

The ReMIP server directly integrates with the SCIP Optimization Suite and solves MIP problems through a RESTful API. It provides real-time logging functionality and streaming capabilities through Server-Sent Events (SSE).

## Features

- **RESTful API**: Solve MIP problems through a clean and modern API
- **Real-time Logging**: Stream solver logs in real-time to monitor progress
- **PySCIPOpt Integration**: Directly integrates with the SCIP Optimization Suite through its Python API for better performance and stability
- **Containerized**: Comes with a Docker setup for easy and consistent deployment

## Prerequisites

- **SCIP Optimization Suite**: This project uses `pyscipopt`, which requires a working installation of the SCIP Optimization Suite. You can download it from the [official SCIP website](https://scipopt.org/index.php#download).
- Python 3.11+
- [uv](https://github.com/astral-sh/uv): A fast Python package installer
- [Docker](https://www.docker.com/): For running the application in a container

## Installation

1. **Create a virtual environment:**
   ```bash
   uv venv
   ```

2. **Install the server and its dependencies:**
   ```bash
   # This command installs the server and test dependencies
   uv pip install -e .[test]
   ```

## Running

To run the API server locally:

```bash
uv run remip
```

The API will be available at `http://localhost:8000`.

## API Endpoints

- `POST /solve`: Submits a MIP problem. Returns the final solution as JSON. If the `stream=sse` query parameter is provided or the `Accept` header is `text/event-stream`, it streams solver events using Server-Sent Events (SSE).
- `GET /solver-info`: Returns information about the configured solver.

## Solution Object

The solution object returned by the `/solve` endpoint contains the following fields:

-   `name`: The name of the problem.
-   `status`: The solution status (e.g., `optimal`, `infeasible`).
-   `objective_value`: The objective value of the solution.
-   `variables`: A dictionary of variable names and their values.
-   `mip_gap`: The final MIP gap (for MIP problems).
-   `slacks`: A dictionary of constraint names and their slack values.
-   `duals`: A dictionary of constraint names and their dual values (for LP problems).
-   `reduced_costs`: A dictionary of variable names and their reduced costs (for LP problems).

## Testing

To run the test suite:

```bash
uv run pytest
```

## Docker

To build and run the application using Docker:

```bash
docker-compose build
docker-compose up
```

## Project Structure

This package follows the standard `src` layout for clean and maintainable code:

```
remip/
├── src/
│   └── remip/
│       ├── __init__.py
│       ├── main.py
│       ├── models.py
│       ├── services.py
│       └── solvers/
│           └── scip_wrapper.py
├── tests/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](../LICENSE) file for details.
