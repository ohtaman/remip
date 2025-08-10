from pyscipopt import Model, SCIP_RESULT, SCIP_PARAMSETTING
from ..models import MIPProblem, MIPSolution
from typing import AsyncGenerator
import asyncio
import threading

class ScipSolverWrapper:
    """
    A wrapper for the pyscipopt library.
    """

    async def solve(self, problem: MIPProblem) -> MIPSolution:
        """
        Solves a MIP problem using pyscipopt.
        """
        model, vars = self._build_model(problem)
        model.optimize()
        return self._extract_solution(model, problem, vars)

    async def solve_and_stream_logs(self, problem: MIPProblem) -> AsyncGenerator[str, None]:
        """
        Solves a MIP problem and streams the logs.
        """
        log_queue = asyncio.Queue()
        stop_event = threading.Event()

        def message_hdlr(msg):
            asyncio.run_coroutine_threadsafe(log_queue.put(msg), asyncio.get_running_loop())

        model, vars = self._build_model(problem)
        model.setMessagehdlr(message_hdlr, quiet=False)

        def optimize_in_thread():
            model.optimize()
            stop_event.set()

        solver_thread = threading.Thread(target=optimize_in_thread)
        solver_thread.start()

        while not stop_event.is_set() or not log_queue.empty():
            try:
                log_line = await asyncio.wait_for(log_queue.get(), timeout=0.1)
                yield log_line
            except asyncio.TimeoutError:
                pass
        
        solver_thread.join()

    def _build_model(self, problem: MIPProblem):
        model = Model(problem.parameters.name)
        vars = {}
        for var_data in problem.variables:
            vars[var_data.name] = model.addVar(
                name=var_data.name,
                lb=var_data.lowBound,
                ub=var_data.upBound,
                vtype="C" if var_data.cat == "Continuous" else "I"
            )
        for const_data in problem.constraints:
            coeffs = {vars[c.name]: c.value for c in const_data.coefficients}
            sense = const_data.sense
            rhs = 0.0
            if const_data.constant:
                rhs = -const_data.constant

            if sense == 0: # EQ
                model.addCons(sum(c * v for v, c in coeffs.items()) == rhs)
            elif sense == -1: # LEQ
                model.addCons(sum(c * v for v, c in coeffs.items()) <= rhs)
            else: # GEQ
                model.addCons(sum(c * v for v, c in coeffs.items()) >= rhs)

        obj_coeffs = {vars[c.name]: c.value for c in problem.objective.coefficients}
        model.setObjective(sum(c * v for v, c in obj_coeffs.items()), "minimize" if problem.parameters.sense == 1 else "maximize")
        return model, vars

    def _extract_solution(self, model, problem, vars):
        status = model.getStatus()
        objective_value = model.getObjVal()
        solution_vars = {}
        if model.getNSols() > 0:
            solution = model.getBestSol()
            for var_name, var in vars.items():
                solution_vars[var_name] = solution[var]
        return MIPSolution(
            name=problem.parameters.name,
            status=status,
            objective_value=objective_value,
            variables=solution_vars
        )
