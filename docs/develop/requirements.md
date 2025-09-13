# Requirements: Solver Timeout

## 1. Overview

The `remip` solver can sometimes take a long time to find a solution for complex optimization problems. To prevent indefinite runs and to allow users to control the maximum execution time, a timeout mechanism is required. This feature will allow users to specify a maximum duration for the solver to run.

## 2. Functional Requirements

### 2.1. Timeout Parameter

- The solver will accept a `timeout` parameter, specified in seconds.
- This parameter will be optional.
- If the `timeout` parameter is not provided, the solver will run without a time limit, preserving the current default behavior.

### 2.2. Solver Behavior

- When the `timeout` is specified, the solver process must terminate if the execution time exceeds the given value.
- If the solver terminates due to a timeout, it should return a specific status indicating that the timeout was reached.
- If a feasible (but not necessarily optimal) solution is found before the timeout occurs, the solver should return the best solution found so far.

## 3. Non-Functional Requirements

### 3.1. API Integration

- The `timeout` parameter must be integrated into the server's API endpoint for solving optimization problems.
- The `remip-client` library must be updated to support passing the `timeout` parameter to the server.

### 3.2. Error Handling

- If an invalid value is provided for the timeout (e.g., a negative number), the API should return a validation error.

### 3.3. User Experience

- The client should receive a clear message indicating that the solver stopped because the timeout was reached.

## 4. Out of Scope

- This feature will not include support for pausing and resuming the solver.
