# Test Design for Solution Enhancements

## 1. Overview

This document outlines the testing strategy for the new solution enhancement features: MIP gap, constraint slacks, dual values, and reduced costs. The tests will ensure that these features are implemented correctly and that they perform as expected.

The tests will be added to the existing test suites in `remip/tests` and `remip-client/tests`.

## 2. Unit Tests for `remip`

### 2.1. `test_models.py`

-   **Test Solution Model:**
    -   Verify that the `Solution` model can be instantiated with the new fields (`mip_gap`, `slacks`, `duals`, `reduced_costs`).
    -   Test serialization and deserialization of the `Solution` model to ensure the new fields are correctly handled.

### 2.2. `test_solver_wrapper.py`

This file will contain the bulk of the new tests. We will need to create specific test cases for LP and MIP problems to verify the correctness of the new solution attributes.

-   **MIP Problem Tests:**
    -   Create a simple MIP problem.
    -   Solve the problem and check that the `Solution` object is returned.
    -   **Test `mip_gap`:** Assert that `solution.mip_gap` is a float and has a reasonable value (e.g., close to 0 if the problem is solved to optimality).
    -   **Test `slacks`:** Assert that `solution.slacks` is a dictionary and contains correct slack values for the constraints.
    -   **Test `duals` and `reduced_costs` for MIP:** Assert that `solution.duals` and `solution.reduced_costs` are `None` for a MIP problem.

-   **LP Problem Tests:**
    -   Create a simple LP problem.
    -   Solve the problem and check that the `Solution` object is returned.
    -   **Test `mip_gap` for LP:** Assert that `solution.mip_gap` is `None` or 0.0 for an LP problem.
    -   **Test `slacks`:** Assert that `solution.slacks` is a dictionary and contains correct slack values for the constraints.
    -   **Test `duals`:** Assert that `solution.duals` is a dictionary and contains the correct dual values for the constraints. We will need to manually calculate the expected duals for the simple LP.
    -   **Test `reduced_costs`:** Assert that `solution.reduced_costs` is a dictionary and contains the correct reduced costs for the variables. We will need to manually calculate the expected reduced costs.

-   **Infeasible Problem Tests:**
    -   Create an infeasible problem.
    -   Verify that the solver returns a solution with a status of "infeasible" and that the new attributes are handled gracefully (e.g., they are `None`).

## 3. Unit Tests for `remip-client`

### 3.1. `test_solver.py`

-   **Test `Solution` data class:**
    -   Verify that the `remip_client.solver.Solution` data class includes the new fields.
-   **Test Deserialization:**
    -   Create a sample JSON response from the `remip` server that includes the new fields.
    -   Test that the `remip-client` can correctly deserialize this JSON into a `Solution` object.
    -   Assert that the values of the new fields are correct after deserialization.

## 4. Test Cases Details

### 4.1. Simple LP Problem

-   **Objective:** Maximize `x + 2y`
-   **Constraints:**
    -   `c1: -x + y <= 1`
    -   `c2: x + y <= 2`
-   **Bounds:** `x >= 0`, `y >= 0`
-   **Expected Solution:** `x=0.5`, `y=1.5`, objective = 3.5
-   **Expected Duals:** `dual(c1)=0.5`, `dual(c2)=1.5`
-   **Expected Reduced Costs:** `rc(x)=0`, `rc(y)=0`
-   **Expected Slacks:** `slack(c1)=0`, `slack(c2)=0`

### 4.2. Simple MIP Problem

-   **Objective:** Maximize `x + 2y`
-   **Constraints:**
    -   `c1: -x + y <= 1`
    -   `c2: x + y <= 2`
-   **Bounds:** `x >= 0`, `y >= 0`
-   **Variable Types:** `x` is integer.
-   **Expected Solution:** `x=0`, `y=1`, objective = 2 (or `x=1, y=1`, obj=3, or `x=2, y=0`, obj=2 - need to check what SCIP does)
    *Let's assume for the test `x=1, y=1`, obj=3.*
-   **Expected MIP Gap:** Should be close to 0.0 if solved to optimality.
-   **Expected Slacks:** `slack(c1)=0`, `slack(c2)=0`
-   **Expected Duals:** `None`
-   **Expected Reduced Costs:** `None`

## 5. Manual Testing

-   After the implementation and automated tests are complete, a manual test with a more complex model could be performed to ensure everything works as expected in a more realistic scenario. However, for this feature, strong unit tests are the priority.
