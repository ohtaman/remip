"""
A wrapper for the SCIP solver.
"""

from typing import Any, AsyncGenerator, Dict, Tuple

from pyscipopt import Model

from ..models import (
    Diagnostics,
    EndEvent,
    LogEvent,
    MetricEvent,
    MIPProblem,
    MIPSolution,
    ResultEvent,
    SolverEvent,
    ViolatedConstraint,
)


class ScipSolverWrapper:
    """
    A wrapper for the SCIP solver that provides a consistent interface for solving MIP problems.
    """

    async def solve(self, problem: MIPProblem) -> MIPSolution:
        """
        Solves a MIP problem using SCIP and returns the solution.
        """
        solution = None
        async for event in self.solve_and_stream_events(problem):
            if event.type == "result":
                solution = event.solution
        if solution is None:
            raise ValueError("No solution found")
        return solution

    async def solve_and_stream_events(self, problem: MIPProblem) -> AsyncGenerator[SolverEvent, None]:
        """
        Solves a MIP problem using SCIP and streams events back to the caller.
        """
        # Build the model
        model, vars = await self._build_model(problem)

        # Set solver options
        if problem.solver_options:
            for key, value in problem.solver_options.items():
                model.setParam(key, value)

        # Optimize the model
        model.optimize()

        # Extract the solution
        solution = self._extract_solution(model, problem, vars)

        # Yield the result event
        yield ResultEvent(
            timestamp="2024-01-01T00:00:00Z",
            solution=solution,
            runtime_milliseconds=int(model.getSolvingTime()),
            sequence=0,
        )

        # Yield the end event
        yield EndEvent(success=True)

    async def _build_model(self, problem: MIPProblem) -> Tuple[Model, Dict[str, Any]]:
        """Builds a pyscipopt.Model instance from a MIPProblem definition."""
        model = Model(problem.parameters.name)
        vars = {}
        for var_data in problem.variables:
            vars[var_data.name] = model.addVar(
                name=var_data.name,
                lb=var_data.lower_bound,
                ub=var_data.upper_bound,
                vtype="C" if var_data.category == "Continuous" else "I",
            )

        for i, const_data in enumerate(problem.constraints):
            coeffs = {c.name: c.value for c in const_data.coefficients}
            sense = const_data.sense
            rhs = -const_data.constant if const_data.constant is not None else 0.0
            constraint_name = const_data.name or f"unnamed_constraint_{i}"

            expr = sum(coeffs[name] * var for name, var in vars.items() if name in coeffs)
            if sense == 0:  # EQ
                constraint = expr == rhs
            elif sense == -1:  # LEQ
                constraint = expr <= rhs
            else:  # GEQ
                constraint = expr >= rhs
            model.addCons(constraint, name=constraint_name)

        objective = sum(c.value * vars[c.name] for c in problem.objective.coefficients)
        model.setObjective(objective, "minimize" if problem.parameters.sense == 1 else "maximize")

        # Add SOS1 constraints
        for sos_data in problem.sos1:
            sos_vars = [vars[name] for name in sos_data.keys()]
            sos_weights = [weight for weight in sos_data.values()]
            model.addConsSOS1(sos_vars, sos_weights)

        # Add SOS2 constraints
        for sos_data in problem.sos2:
            sos_vars = [vars[name] for name in sos_data.keys()]
            sos_weights = [weight for weight in sos_data.values()]
            model.addConsSOS2(sos_vars, sos_weights)

        return model, vars

    def _extract_solution(self, model: Model, problem: MIPProblem, vars: Dict[str, Any]) -> MIPSolution:
        """Extracts the solution from a pyscipopt.Model instance."""
        status = model.getStatus()
        objective_value = None
        solution_vars = {}
        diagnostics = None

        if status == "infeasible":
            # --- Infeasible Diagnostics ---
            model.setPresolve(Model.Presolve.OFF)
            model.setHeuristics(Model.Heuristics.OFF)

            violated_constraints = []
            dual_values = {}

            # Get variable values from the last LP relaxation
            for var_name, var in vars.items():
                try:
                    solution_vars[var_name] = model.getVal(var)
                except Exception:
                    solution_vars[var_name] = 0.0  # Fallback

            # Analyze constraints
            for c in model.getConss():
                if not model.isLinearCons(c):
                    continue

                activity = model.getActivity(c)
                rhs = c.getRhs()
                lhs = c.getLhs()
                sense = c.getSensedString()
                violation = 0.0

                if sense == "L":  # <=
                    if activity > rhs:
                        violation = activity - rhs
                elif sense == "G":  # >=
                    if activity < lhs:
                        violation = lhs - activity
                elif sense == "E":  # ==
                    violation = abs(activity - rhs)

                if violation > 1e-6:
                    violated_constraints.append(
                        ViolatedConstraint(
                            name=c.name,
                            violation_amount=violation,
                            left_hand_side=activity,
                            right_hand_side=rhs if sense != "G" else lhs,
                            sense=sense,
                        )
                    )

                # Get Farkas duals
                try:
                    dual_values[c.name] = model.getDualfarkasLinear(c)
                except Exception:
                    dual_values[c.name] = 0.0

            diagnostics = Diagnostics(
                violated_constraints=violated_constraints,
                irreducible_infeasible_set=[],  # IIS not supported by PySCIPOpt
                dual_values=dual_values,
            )

        elif model.getNSols() > 0:
            # --- Feasible Solution ---
            objective_value = model.getObjVal()
            solution = model.getBestSol()
            for var_name, var in vars.items():
                solution_vars[var_name] = solution[var]

        return MIPSolution(
            name=problem.parameters.name,
            status=status,
            objective_value=objective_value,
            variables=solution_vars,
            diagnostics=diagnostics,
        )
