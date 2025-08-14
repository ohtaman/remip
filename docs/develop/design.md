# Detailed Design - MIP Solver API

## 1. Architecture Overview

This document outlines the detailed design for the MIP Solver API, a FastAPI-based service for solving Mixed-Integer Programming problems.

### 1.1 System Architecture Diagram

```mermaid
graph TD
    subgraph Client
        A[Python Client Library]
        B[HTTP Client]
    end

    subgraph Server (FastAPI)
        C[API Endpoints]
        D[MIP Solver Service]
        E[Data Models]
    end

    subgraph Solver
        F[SCIP Solver]
    end

    A -- PuLP Interface --> C
    B -- HTTP Requests --> C
    C -- Calls --> D
    D -- Uses --> E
    D -- Executes --> F
    F -- Returns Solution --> D
    D -- Returns Solution --> C
    C -- HTTP Response --> B
    C -- Streams Logs --> B
    C -- Updates --> A
```

### 1.2 Technology Stack

- **Language**: Python 3.11+
- **Frameworks**: FastAPI
- **Web Server**: Uvicorn
- **Libraries**:
  - `pulp`: For modeling and interacting with problems in the client library.
  - `scipy`: The core MIP solver.
  - `fastapi`: The web framework.
  - `pydantic`: For data validation and settings management.
- **Tools**:
  - `pytest`: For testing.
  - `ruff`: For linting and formatting.
  - `git`: For version control.

## 2. Component Design

### 2.1 Component List

| Component Name | Responsibility | Dependencies |
| :--- | :--- | :--- |
| **API Endpoints** | Handles incoming HTTP requests, validates data, and returns responses. | MIP Solver Service, Data Models |
| **MIP Solver Service** | Contains the core logic for receiving a problem, invoking the solver, and handling the results and logs. | SCIP Solver, Data Models |
| **Data Models** | Defines the Pydantic models for API request/response bodies and problem structure. | Pydantic |
| **Python Client** | Provides a PuLP-compatible solver interface that communicates with the API. | PuLP, HTTPX |

### 2.2 Component Details

#### API Endpoints

- **Purpose**: To provide a clean, stable HTTP interface for submitting problems and retrieving results.
- **Public Interface**:
  - `POST /solve`: Accepts a JSON representation of a PuLP problem, solves it, and returns the JSON solution.
  - `GET /solve-stream`: Accepts a JSON representation of a PuLP problem, solves it, and streams the solver logs back to the client via Server-Sent Events (SSE).
  - `GET /solver-info`: Returns information about the configured solver.

#### MIP Solver Service

- **Purpose**: To orchestrate the solving process, manage solver instances, and capture logs.
- **Internal Interface**:
  ```python
  class MIPSolverService:
      def solve_problem(self, problem_data: dict) -> dict:
          # Solves the problem and returns the final result
          pass

      async def solve_problem_stream(self, problem_data: dict) -> AsyncGenerator[str, None]:
          # Solves the problem and yields log lines
          pass
  ```
- **Internal Implementation Strategy**: This service will take the dictionary representation of the problem, reconstruct it into a format the solver can understand, and apply any solver-specific options from the `solver_options` field. It will run the solver in a separate process to avoid blocking and capture its stdout/stderr for logging.

#### Data Models

- **Purpose**: To ensure all data exchanged with the API is well-formed and validated.
- **Public Interface**:
  ```python
  from pydantic import BaseModel, Field
  from typing import List, Dict, Any, Optional

  class MIPProblem(BaseModel):
      # Based on PuLP's to_dict() structure
      name: str
      sense: int
      objective: Dict
      constraints: List[Dict]
      variables: Dict
      solver_options: Optional[Dict[str, Any]] = None # For solver-specific kwargs

  class MIPSolution(BaseModel):
      name: str
      status: str
      objective_value: float
      variables: Dict[str, float]
  ```

## 3. Data Flow

### 3.1 Data Flow Diagram

```
[Client] --(JSON: LpProblem)--> [POST /solve]
           |
           `--(JSON: LpProblem)--> [GET /solve-stream]

[API Endpoint] --(dict)--> [MIP Solver Service]
[MIP Solver Service] --(Solver-specific format)--> [SCIP Solver]
[SCIP Solver] --(Solution text)--> [MIP Solver Service]
[MIP Solver Service] --(dict)--> [API Endpoint]

[API Endpoint] --(JSON: MIPSolution)--> [Client]
               |
               `--(SSE stream: str)--> [Client]
```

### 3.2 Data Transformation

- **Input Data Format**: JSON object conforming to the structure created by PuLP's `to_dict()` method.
- **Processing Steps**:
  1. The API receives the JSON and validates it against the `MIPProblem` Pydantic model.
  2. The `MIPSolverService` converts the validated data into a temporary file or data structure that the SCIP command-line interface can read.
  3. The solver process is executed.
  4. The service parses the solver's output (solution details and status) from its stdout.
  5. The parsed data is structured into the `MIPSolution` Pydantic model.
- **Output Data Format**: JSON object conforming to the `MIPSolution` schema. For streaming, the output is a text stream of log lines.

## 4. API Interface

### 4.1 Internal API

- The interface between the `API Endpoints` and the `MIP Solver Service` will be direct Python function calls, using the Pydantic models for data transfer.

### 4.2 External API

- **`POST /solve`**
  - **Request Body**: `application/json` - `MIPProblem`
  - **Success Response**: `200 OK` - `MIPSolution`
  - **Error Response**: `400 Bad Request`, `422 Unprocessable Entity`, `500 Internal Server Error`

- **`GET /solve-stream`**
  - **Request Body**: `application/json` - `MIPProblem` (sent as a JSON string in a query parameter or custom header)
  - **Success Response**: `200 OK` - `text/event-stream`
  - **Error Response**: `400 Bad Request`, `500 Internal Server Error`

- **`GET /solver-info`**
  - **Request Body**: None
  - **Success Response**: `200 OK` - `{"solver": "SCIP", "version": "x.y.z"}`

## 5. Error Handling

### 5.1 Error Classification

- **User Input Error (4xx)**: Invalid JSON, validation failure against `MIPProblem` schema, or unsupported problem features. Handled by FastAPI's default exception handling.
- **Solver Error (5xx)**: The solver fails to start, crashes, or cannot find a solution due to internal issues. The API will return a `500 Internal Server Error` with a descriptive message.
- **Infeasible/Unbounded Problem (200)**: These are valid solver outcomes, not errors. The status will be returned in the `MIPSolution` object.

### 5.2 Error Notification

- Errors will be logged to `stderr` using Python's standard `logging` module.
- HTTP responses will contain a `detail` key in the JSON body with a human-readable error message.

## 6. Security Design

### 6.1 Authentication & Authorization

- No authentication or authorization is required for the initial version. The API is considered to be running in a trusted environment.

### 6.2 Data Protection

- **Input Validation**: Pydantic models provide robust validation of the incoming JSON structure and data types.
- **Resource Limiting**: The web server (Uvicorn) will be configured with limits on request body size to prevent DoS attacks. The solver process will be run with a timeout to prevent runaway resource consumption.

## 7. Test Design

**For detailed test design, please run the `/test-design` command to create a test design document.**

That document will define:
- Test cases for normal, edge, and boundary conditions
- Test data design
- Performance and security testing
- Automation strategy

## 8. Performance Optimization

### 8.1 Expected Load

- The API should handle dozens of concurrent requests, with the primary bottleneck being the solver's CPU time, not the API itself.

### 8.2 Optimization Strategy

- **Asynchronous Execution**: All API endpoints will be `async` to handle I/O-bound operations (like reading requests and sending responses) efficiently.
- **Process Isolation**: The MIP solver will be run in a separate subprocess using `asyncio.create_subprocess_exec` to prevent it from blocking the main FastAPI event loop. This ensures the server remains responsive to other requests while a problem is being solved.
- **Efficient Streaming**: Server-Sent Events (SSE) will be used for log streaming, as it is a lightweight and efficient protocol for unidirectional server-to-client communication.

## 9. Deployment

### 9.1 Deployment Configuration

- The application will be packaged into a Docker container.
- Deployment will be managed via a simple `docker-compose.yml` file for local development and testing.
- For production, a more robust container orchestration system like Kubernetes could be used.

### 9.2 Configuration Management

- Application settings (e.g., solver path, timeouts, logging level) will be managed using Pydantic's `BaseSettings`, which can read from environment variables. This avoids hardcoding configuration into the source code.

## 10. Implementation Notes

- **Solver Interface**: A wrapper class will be created to abstract the command-line interface of the SCIP solver, making it easier to swap out solvers in the future if needed.
- **Streaming Implementation**: We will use `fastapi.responses.StreamingResponse` with an `async` generator function to implement the SSE endpoint. The generator will read the solver's log output line by line and `yield` it to the client.
- **Multiple Solvers**: The design will support multiple solvers. The specific solver can be chosen via an API parameter. The default will be SCIP.
- **Solver-Specific Arguments**: The `solver_options` dictionary in the request will be used to pass command-line arguments to the solver executable. The application will need a mapping between the JSON keys and the solver's specific command-line flags.
