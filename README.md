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
-   **Powered by SCIP**: Utilizes the powerful SCIP optimization suite.
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

**Example:**

```python
from pulp import LpProblem, LpVariable, lpSum, LpMinimize
from remip_client.solver import MipApiSolver

# 1. Define a problem
prob = LpProblem("test_problem", LpMinimize)
x = LpVariable("x", 0, 1)
y = LpVariable("y", 0, 1)
prob += x + y, "objective"
prob += 2*x + y <= 1, "constraint1"

# 2. Initialize the remote solver
solver = MipApiSolver(base_url="http://localhost:8000")

# 3. Solve the problem via the API
prob.solve(solver)

# 4. Print the results
print(f"Status: {prob.status}")
for v in prob.variables():
    print(f"{v.name} = {v.varValue}")
```

---

## Testing

To run the full test suite for the server:

```bash
uv run pytest
```

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