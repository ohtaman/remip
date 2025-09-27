# ReMIP Server

This directory contains the ReMIP FastAPI server, which provides a RESTful API for solving Mixed-Integer Programming (MIP) problems.

## Running the Server

To run the server, you need to have the dependencies installed (e.g., via `uv pip install -e .` from this directory). Then, you can start the server using the `remip` command:

```bash
uv run remip --host 0.0.0.0 --port 8000
```

The server will automatically find an open port if `8000` is in use, unless a specific port is provided.

## API Endpoints

### `GET /solver-info`

Returns information about the underlying MIP solver.

- **Method:** `GET`
- **Success Response:** `200 OK`
- **Response Body Example:**
  ```json
  {
    "solver": "SCIP",
    "version": "x.y.z"
  }
  ```

### `POST /solve`

Solves a MIP problem. It can return the solution directly or stream solver events using Server-Sent Events (SSE).

- **Method:** `POST`
- **Query Parameters:**
  - `timeout` (float, optional): Maximum time in seconds to allow the solver to run.
  - `stream` (string, optional): If set to `sse`, the server will stream solver events.
- **Request Body:** A JSON object representing the `MIPProblem`.
- **Success Response:** `200 OK`

---

#### Request Body (`MIPProblem`)

The request body must be a JSON object with the following structure:

```json
{
  "parameters": {
    "name": "MyProblem",
    "sense": 1,
    "status": 0,
    "sol_status": 0
  },
  "objective": {
    "name": "TotalProfit",
    "coefficients": [
      { "name": "x1", "value": 10 },
      { "name": "x2", "value": 15 }
    ]
  },
  "variables": [
    { "name": "x1", "cat": "Binary" },
    { "name": "x2", "cat": "Binary" }
  ],
  "constraints": [
    {
      "name": "ResourceA",
      "sense": -1,
      "coefficients": [
        { "name": "x1", "value": 2 },
        { "name": "x2", "value": 5 }
      ],
      "constant": 10
    }
  ],
  "solver_options": {
    "limits/time": 60
  }
}
```

---

#### Standard Response (`MIPSolution`)

If the `stream` parameter is not set, the response will be a JSON object with the solution:

```json
{
  "name": "MyProblem",
  "status": "optimal",
  "objective_value": 25.0,
  "variables": {
    "x1": 1.0,
    "x2": 1.0
  }
}
```

---

#### Streaming Response (SSE)

If `stream=sse` is specified, the response will be a `text/event-stream`. The client will receive a sequence of events, such as `log`, `metric`, `result`, and `end`.

**Example Event:**

```
event: metric
data: {"timestamp":"...","objective_value":25.0,"gap":0.0,"iteration":10,"sequence":5}

```
