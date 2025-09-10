# ReMIP Client

**ReMIP Client** is a Python client library for integrating with the ReMIP server. It provides a PuLP-compatible solver interface for solving Mixed-Integer Programming (MIP) problems remotely.

## Overview

The ReMIP Client allows you to leverage the capabilities of the ReMIP server without disrupting existing PuLP workflows. It eliminates the need for local solver installation and configuration, making it easy to use cloud-based optimization solutions.

## Features

- **PuLP Compatibility**: Use with existing PuLP code without modifications
- **Remote Execution**: Solve MIP problems without using local resources
- **Streaming Support**: Monitor solver progress in real-time
- **Simple Integration**: Integrate with existing projects with minimal code changes

## Installation

```bash
# Navigate to the remip-client directory
cd remip-client

# Install the client
uv pip install -e .
```

## Usage

### Basic Example

```python
from pulp import LpProblem, LpVariable, LpMaximize, LpStatus
from remip_client.solver import ReMIPSolver

# 1. Define a problem
prob = LpProblem("test_problem", LpMaximize)
x = LpVariable("x", 0, 1, cat='Binary')
y = LpVariable("y", 0, 1, cat='Binary')
prob += x + y, "objective"
prob += 2*x + y <= 2, "constraint1"

# 2. Initialize the remote solver for a non-streaming request
solver = ReMIPSolver(stream=False)

# 3. Solve the problem
prob.solve(solver)

# 4. Print the results
print(f"Status: {LpStatus[prob.status]}")
for v in prob.variables():
    print(f"{v.name} = {v.varValue}")
```

### Using Streaming Functionality

```python
# To get a stream of solver events, set stream=True
streaming_solver = ReMIPSolver(stream=True)

# The client will print log and metric events to the console
prob.solve(streaming_solver)
```

### Customizing Server Configuration

```python
# Initialize solver with custom server URL
solver = ReMIPSolver(
    server_url="http://your-remip-server:8000",
    stream=False
)
```

## Accessing Solution Information

After solving a problem, the `LpProblem` object is populated with the solution details.
In addition to the standard PuLP attributes, the following fields are also available on the `LpProblem` object:

-   `mip_gap`: The final MIP gap (for MIP problems).
-   `slacks`: A dictionary of constraint names and their slack values.
-   `duals`: A dictionary of constraint names and their dual values (for LP problems).
-   `reduced_costs`: A dictionary of variable names and their reduced costs (for LP problems).

### Example

```python
# ... after solving the problem ...

print(f"MIP Gap: {prob.mip_gap}")
print(f"Slacks: {prob.slacks}")
```

## API Reference

### ReMIPSolver

A PuLP-compatible solver class for communicating with the ReMIP server.

#### Parameters

- `server_url` (str, optional): URL of the ReMIP server. Defaults to `"http://localhost:8000"`
- `stream` (bool, optional): Whether to enable streaming mode. Defaults to `True`

#### Methods

- `solve(problem)`: Solves a PuLP problem and returns the results

## Testing

To run the test suite:

```bash
uv run pytest
```

## Project Structure

This package follows the standard `src` layout:

```
remip-client/
├── src/
│   └── remip_client/
│       ├── __init__.py
│       └── solver.py
├── tests/
│   ├── browser/
│   ├── node/
│   └── test_solver.py
└── pyproject.toml
```

## Dependencies

- Python 3.11+
- PuLP
- requests
- sseclient-py (for streaming functionality)

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](../LICENSE) file for details.
