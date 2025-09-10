# Task List for Solution Enhancements

This document breaks down the implementation of the solution enhancement features into smaller, actionable tasks.

## 1. Core `remip` Implementation

-   **Task 1.1: Update `remip.models.Solution`**
    -   **File:** `remip/src/remip/models.py`
    -   **Details:** Add the new optional fields to the `Solution` Pydantic model:
        -   `mip_gap: Optional[float] = None`
        -   `slacks: Optional[Dict[str, float]] = None`
        -   `duals: Optional[Dict[str, float]] = None`
        -   `reduced_costs: Optional[Dict[str, float]] = None`

-   **Task 1.2: Implement Data Population in `scip_wrapper.py`**
    -   **File:** `remip/src/remip/solvers/scip_wrapper.py`
    -   **Details:**
        -   In the `solve` method, after the problem is solved, retrieve the additional solution information from the PySCIPOpt model.
        -   Populate `mip_gap` using `model.getGap()`.
        -   Implement logic to calculate and populate `slacks`. Iterate through constraints, get activity, and calculate slack against LHS/RHS.
        -   For LP problems (check with `model.isMIP()`), implement logic to populate `duals` using `model.getDualsol()`.
        -   For LP problems, implement logic to populate `reduced_costs` using `model.getReducedcost()` for each variable.
        -   Pass the new data when creating the `Solution` object.

## 2. `remip` Testing

-   **Task 2.1: Write Unit Tests for `Solution` Model**
    -   **File:** `remip/tests/test_models.py`
    -   **Details:**
        -   Add a test to create a `Solution` instance with the new fields.
        -   Add a test for `Solution` serialization and deserialization to ensure the new fields are handled correctly.

-   **Task 2.2: Write Unit Tests for `scip_wrapper.py`**
    -   **File:** `remip/tests/test_solver_wrapper.py`
    -   **Details:**
        -   Add a test with a simple MIP problem to verify:
            -   `mip_gap` is correctly populated.
            -   `slacks` are correctly calculated.
            -   `duals` and `reduced_costs` are `None`.
        -   Add a test with a simple LP problem to verify:
            -   `mip_gap` is `None` or `0.0`.
            -   `slacks` are correctly calculated.
            -   `duals` are correctly populated with expected values.
            -   `reduced_costs` are correctly populated with expected values.
        -   Add a test for an infeasible problem to ensure graceful failure (new fields are `None`).

## 3. `remip-client` Updates

-   **Task 3.1: Update `remip_client.solver.Solution`**
    -   **File:** `remip-client/src/remip_client/solver.py`
    -   **Details:** Add the new optional fields to the `Solution` dataclass to match the `remip` server's `Solution` model.

-   **Task 3.2: Write Unit Tests for `remip-client`**
    -   **File:** `remip-client/tests/test_solver.py`
    -   **Details:**
        -   Add a test to verify the `Solution` dataclass in the client has the new fields.
        -   Add a test to simulate a response from the server with the new fields and verify the client can deserialize it correctly.

## 4. Documentation

-   **Task 4.1: Update READMEs or other documentation**
    -   **Files:** `remip/README.md`, `remip-client/README.md` (and any other relevant docs)
    -   **Details:** Briefly document the new fields available in the `Solution` object and how to use them. Explain which fields are only available for LP problems.

## 5. Final Review and Merge

-   **Task 5.1: Create Pull Request**
    -   **Details:** Create a pull request from the `feature/solution-enhancements` branch to the main development branch. The PR description should summarize the changes.
-   **Task 5.2: Code Review**
    -   **Details:** Request a code review from team members.
-   **Task 5.3: Merge**
    -   **Details:** After approval, merge the pull request.
