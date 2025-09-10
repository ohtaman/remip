# Requirements for Solution Enhancements

## 1. Overview

This document outlines the requirements for enhancing the solution object to include additional information from the solver. The goal is to provide users with more insights into the solution quality and the model's characteristics.

The following attributes should be added to the solution:

-   MIP Gap
-   Constraint Slacks
-   Dual Values
-   Reduced Costs

## 2. Functional Requirements

### 2.1. MIP Gap

-   The solution object should contain the final MIP gap of the optimization process.
-   The MIP gap should be a floating-point number.
-   If the problem is not a MIP, the MIP gap should be 0.0 or not applicable.

### 2.2. Constraint Slacks

-   The solution object should provide a way to access the slack value for each constraint.
-   This could be a dictionary or a similar data structure mapping constraint names (or IDs) to their slack values.
-   Slack values should be floating-point numbers.

### 2.3. Dual Values (Shadow Prices)

-   The solution object should provide access to the dual values (shadow prices) for each constraint.
-   This should be a dictionary or a similar data structure mapping constraint names (or IDs) to their dual values.
-   Dual values are typically available for Linear Programs (LPs) only. The implementation should handle cases where dual values are not available (e.g., for MIPs). In such cases, it could return an empty dictionary or raise an informative error.
-   Dual values should be floating-point numbers.

### 2.4. Reduced Costs

-   The solution object should provide access to the reduced costs for each variable.
-   This should be a dictionary or a similar data structure mapping variable names (or IDs) to their reduced costs.
-   Reduced costs are typically available for Linear Programs (LPs) only. The implementation should handle cases where reduced costs are not available (e.g., for MIPs).
-   Reduced costs should be floating-point numbers.

## 3. Non-Functional Requirements

-   **Performance:** The additional data should be retrieved from the solver efficiently without significantly impacting the overall solution time.
-   **API Clarity:** The new attributes on the solution object should be well-documented and easy to use.
-   **Error Handling:** The system should gracefully handle cases where the requested information is not available from the solver for a particular problem type (e.g., requesting dual values for a MIP).

## 4. Out of Scope

-   Any changes to the modeling part of the API.
-   Support for solver-specific parameters not directly related to these solution attributes.
