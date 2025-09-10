# Design for Solution Enhancements

## 1. Overview

This document provides the technical design for incorporating MIP gap, constraint slacks, dual values, and reduced costs into the solution object. This design is based on the approved requirements.

The primary changes will be in the `remip.models.Solution` class and the solver wrapper (`remip.solvers.scip_wrapper.ScipWrapper`) that creates the `Solution` object.

## 2. Data Model Changes

The `remip.models.Solution` class will be extended to include the new attributes.

```python
# In remip/models.py

from typing import Dict, Optional
from pydantic import BaseModel

# ... existing Solution class ...

class Solution(BaseModel):
    # ... existing fields ...
    mip_gap: Optional[float] = None
    slacks: Optional[Dict[str, float]] = None
    duals: Optional[Dict[str, float]] = None
    reduced_costs: Optional[Dict[str, float]] = None

```

### 2.1. `mip_gap`

-   A `float` to store the MIP gap.
-   It will be `None` if not applicable (e.g., for LPs).

### 2.2. `slacks`

-   A dictionary mapping constraint names (`str`) to their slack values (`float`).
-   `None` if not computed or not applicable.

### 2.3. `duals`

-   A dictionary mapping constraint names (`str`) to their dual values (`float`).
-   `None` if not available (e.g., for MIPs).

### 2.4. `reduced_costs`

-   A dictionary mapping variable names (`str`) to their reduced costs (`float`).
-   `None` if not available (e.g., for MIPs).

## 3. Solver Wrapper Modifications

The `remip.solvers.scip_wrapper.ScipWrapper` will be responsible for populating these new fields in the `Solution` object.

### 3.1. Populating `mip_gap`

-   After solving a MIP, the `getGap()` method of the PySCIPOpt model object will be used to retrieve the MIP gap.
-   This value will be passed to the `Solution` object.

### 3.2. Populating `slacks`

-   After a solution is found, iterate through the constraints of the PySCIPOpt model.
-   For each constraint, the `getActivity()` method can be used to get the value of the constraint's expression.
-   The slack can be calculated based on the activity and the left-hand side (LHS) and right-hand side (RHS) of the constraint.
    -   For `LHS <= expr <= RHS`, slack for LHS is `activity - LHS`, and for RHS is `RHS - activity`.
    -   We will need to decide on a consistent way to report slack for ranged constraints. A good approach is to provide the "violation" of the tightest bound.
-   The constraint name and its slack value will be stored in the `slacks` dictionary.

### 3.3. Populating `duals`

-   This is applicable mainly for LP problems. After solving, we need to check if the problem is an LP.
-   If it is an LP, we can use `getDualsol()` on the PySCIPOpt model object to get the dual values for the constraints.
-   The `getDualsol` method requires a constraint object. We will iterate through the constraints and get their dual values.
-   The constraint name and its dual value will be stored in the `duals` dictionary.
-   If the problem is a MIP, this field will remain `None`. We might need to add a check `model.isMIP()`.

### 3.4. Populating `reduced_costs`

-   Similar to dual values, reduced costs are typically for LP problems.
-   After solving an LP, we can use the `getReducedcost()` method on a variable object.
-   We will iterate through the variables in the model and get their reduced costs.
-   The variable name and its reduced cost will be stored in the `reduced_costs` dictionary.
-   If the problem is a MIP, this field will remain `None`.

## 4. API on `remip-client`

The `remip-client` will also need to be updated to reflect these changes.

-   The `remip_client.solver.Solution` data class will be updated to match the changes in `remip.models.Solution`.
-   The client will then be able to deserialize the full solution object received from the `remip` server.

## 5. Error Handling

-   If a user tries to access duals or reduced costs for a MIP problem where they are not available, the API will return `None` for these fields. No exception will be raised. The client-side code should handle the `None` case.

## 6. Implementation Plan

1.  Modify `remip.models.Solution` to include the new fields.
2.  Update `remip.solvers.scip_wrapper.ScipWrapper` to populate the new fields from the PySCIPOpt model.
3.  Modify `remip_client.solver.Solution` to mirror the server-side `Solution` model.
4.  Add unit tests to verify that the new fields are populated correctly for both LP and MIP problems.
