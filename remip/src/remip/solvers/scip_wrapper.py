import asyncio
import re
import threading
import time
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, Optional, Tuple

from pyscipopt import Model

from ..models import (
    EndEvent,
    LogEvent,
    MetricEvent,
    MIPProblem,
    MIPSolution,
    ResultEvent,
    SolverEvent,
)


class ScipSolverWrapper:
    """
    A wrapper for the pyscipopt library that provides solving capabilities and
    streams structured SSE events.
    """

    def __init__(self):
        # Regex to capture SCIP's progress table lines
        self.metric_regex = re.compile(
            r"\s*(\d+\.\d+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*(\d+)\s*\|.*\|\s*([\d\.\-inf]+)\s*\|\s*([\d\.\-inf]+)\s*\|\s*([\d\.\-inf]+)"
        )
        self.seq = 0

    async def solve(self, problem: MIPProblem) -> MIPSolution:
        """
        Solves a MIP problem by consuming the event stream and returning the final solution.
        """
        solution: Optional[MIPSolution] = None

        async for event in self.solve_and_stream_events(problem):
            if isinstance(event, ResultEvent):
                solution = event.solution

        if not solution:
            raise Exception("Solver did not produce a result.")

        return solution

    async def solve_and_stream_events(self, problem: MIPProblem) -> AsyncGenerator[SolverEvent, None]:
        """
        Solves a MIP problem and streams structured SolverEvent objects.
        """
        self.seq = 0
        start_time = time.time()

        log_queue: asyncio.Queue[str] = asyncio.Queue()
        stop_event = threading.Event()
        model, vars = await self._build_model(problem)

        # The solver runs in a separate thread to avoid blocking asyncio event loop
        solver_thread = threading.Thread(target=self._run_solver_in_thread, args=(model, log_queue, stop_event))
        solver_thread.start()

        # Process logs from the queue until the solver is finished
        while not stop_event.is_set() or not log_queue.empty():
            try:
                log_line = await asyncio.wait_for(log_queue.get(), timeout=0.1)
                event = self._parse_log_line(log_line)
                if event:
                    self.seq += 1
                    event.sequence = self.seq
                    yield event
            except asyncio.TimeoutError:
                continue

        solver_thread.join()
        runtime_ms = int((time.time() - start_time) * 1000)

        # Yield the final result event
        solution = self._extract_solution(model, problem, vars)
        self.seq += 1
        yield ResultEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            solution=solution,
            runtime_milliseconds=runtime_ms,
            sequence=self.seq,
        )

        # Yield the end event
        yield EndEvent(success=True)

    def _run_solver_in_thread(self, model: Model, log_queue: asyncio.Queue, stop_event: threading.Event):
        """Target function for the solver thread."""

        # In the latest version of PySCIPOpt, setMessagehdlr is not available,
        # so we capture standard output to get logs instead
        import sys
        from io import StringIO

        # Capture standard output
        old_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            model.optimize()
        finally:
            # Restore standard output
            sys.stdout = old_stdout
            captured_output.seek(0)

            # Send captured output to log queue
            for line in captured_output:
                if line.strip():
                    asyncio.run_coroutine_threadsafe(log_queue.put(line.strip()), asyncio.get_running_loop())

        stop_event.set()

    def _parse_log_line(self, line: str) -> Optional[SolverEvent]:
        """Parses a raw log line from SCIP into a structured SolverEvent."""
        match = self.metric_regex.match(line)
        ts = datetime.now(timezone.utc).isoformat()

        if match:
            try:
                # It's a metric line
                return MetricEvent(
                    timestamp=ts,
                    iteration=int(match.group(2)),
                    objective_value=float(match.group(4)) if match.group(4) != "inf" else float("inf"),
                    gap=float(match.group(5)) if match.group(5) not in ["-", "inf"] else float("inf"),
                )
            except (ValueError, IndexError):
                # Fallback for parsing errors
                return LogEvent(timestamp=ts, level="info", stage="solving", message=line.strip())
        elif line.strip():
            # It's a standard log line
            return LogEvent(timestamp=ts, level="info", stage="presolve", message=line.strip())
        return None

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

        obj_coeffs = {c.name: c.value for c in problem.objective.coefficients}
        objective = sum(obj_coeffs[name] * var for name, var in vars.items() if name in obj_coeffs)
        model.setObjective(objective, "minimize" if problem.parameters.sense == 1 else "maximize")

        # Add SOS constraints
        if problem.sos1:
            for i, weights_dict in enumerate(problem.sos1):
                if not isinstance(weights_dict, dict):
                    continue
                name = f"sos1_{i}"
                sos_vars = [vars[var_name] for var_name in weights_dict.keys() if var_name in vars]
                weights = [weight for var_name, weight in weights_dict.items() if var_name in vars]
                if sos_vars:
                    model.addConsSOS1(sos_vars, weights, name=name)

        if problem.sos2:
            for i, weights_dict in enumerate(problem.sos2):
                if not isinstance(weights_dict, dict):
                    continue
                name = f"sos2_{i}"
                sos_vars = [vars[var_name] for var_name in weights_dict.keys() if var_name in vars]
                weights = [weight for var_name, weight in weights_dict.items() if var_name in vars]
                if sos_vars:
                    model.addConsSOS2(sos_vars, weights, name=name)

        # Apply solver options
        if problem.solver_options:
            for key, value in problem.solver_options.items():
                model.setParam(key, value)

        return model, vars

    def _extract_solution(self, model: Model, problem: MIPProblem, vars: Dict[str, Any]) -> MIPSolution:
        """Extracts the MIPSolution from the solved pyscipopt.Model."""
        status = model.getStatus()
        objective_value = None
        solution_vars = {}
        if model.getNSols() > 0:
            objective_value = model.getObjVal()
            solution = model.getBestSol()
            for var_name, var in vars.items():
                solution_vars[var_name] = solution[var]

        return MIPSolution(
            name=problem.parameters.name,
            status=status,
            objective_value=objective_value,
            variables=solution_vars,
        )
