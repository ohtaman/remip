from pyscipopt import Model
from ..models import MIPProblem, MIPSolution
from typing import AsyncGenerator

class ScipSolverWrapper:
    """
    A wrapper for the pyscipopt library.
    """

    async def solve(self, problem: MIPProblem) -> MIPSolution:
        """
        Solves a MIP problem using pyscipopt.
        """
        model = Model(problem.name)

        # Add variables
        vars = {}
        for var_data in problem.variables.values():
            vars[var_data.name] = model.addVar(
                name=var_data.name,
                lb=var_data.lowBound,
                ub=var_data.upBound,
                vtype="C" if var_data.cat == "Continuous" else "I"
            )

        # Add constraints
        for const_data in problem.constraints:
            coeffs = {vars[c['name']]: c['value'] for c in const_data['coefficients']}
            sense = const_data['sense']
            rhs = const_data['rhs']
            
            if sense == 0: # EQ
                model.addCons(sum(coeff * var for var, coeff in coeffs.items()) == rhs)
            elif sense == -1: # LEQ
                model.addCons(sum(coeff * var for var, coeff in coeffs.items()) <= rhs)
            else: # GEQ
                model.addCons(sum(coeff * var for var, coeff in coeffs.items()) >= rhs)

        # Set objective
        obj_coeffs = {vars[c.name]: c.value for c in problem.objective.coefficients}
        model.setObjective(sum(coeff * var for var, coeff in obj_coeffs.items()), "minimize" if problem.sense == 1 else "maximize")

        model.optimize()

        # Get solution
        status = model.getStatus()
        objective_value = model.getObjVal()
        solution_vars = {}
        if model.getNSols() > 0:
            solution = model.getBestSol()
            for var_name, var in vars.items():
                solution_vars[var_name] = solution[var]

        return MIPSolution(
            name=problem.name,
            status=status,
            objective_value=objective_value,
            variables=solution_vars
        )

    async def solve_and_stream_logs(self, problem: MIPProblem) -> AsyncGenerator[str, None]:
        """
        Solves a MIP problem and streams the logs.
        pyscipopt does not have a simple way to stream logs to a generator.
        This will be a placeholder for now.
        """
        # In a real implementation, we would need to redirect stdout
        # of the underlying C library, which is complex.
        # For now, we will just solve and return a summary.
        
        solution = await self.solve(problem)
        yield f"Solver status: {solution.status}\n"
        yield f"Objective value: {solution.objective_value}\n"
