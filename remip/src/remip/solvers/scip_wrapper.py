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
    streams logs and results as structured SSE events.
    """

    def __init__(self):
        # Regex to capture SCIP's progress table lines
        self.metric_regex = re.compile(
            r"\s*(\d+\.\d+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*(\d+)\s*\|.*\|\s*([\d\.\-inf]+)\s*\|\s*([\d\.\-inf]+)\s*\|\s*([\d\.\-inf]+)"
        )
        self.log_sequence = 0

    async def solve(self, problem: MIPProblem, timeout: Optional[float] = None) -> MIPSolution:
        """
        Solves a MIP problem by consuming the event stream and returning the final solution.
        Only the final best solution (at completion or time limit) is returned.
        """
        solution: Optional[MIPSolution] = None

        async for event in self.solve_and_stream_events(problem, timeout=timeout):
            if isinstance(event, ResultEvent):
                solution = event.solution

        if not solution:
            raise Exception("Solver did not produce a result.")

        return solution

    async def solve_and_stream_events(
        self, problem: MIPProblem, timeout: Optional[float] = None
    ) -> AsyncGenerator[SolverEvent, None]:
        """
        Solves a MIP problem and streams structured SolverEvent objects.
        """
        self.log_sequence = 0
        start_time = time.time()

        # Yield an initial event to ensure headers are sent quickly
        self.log_sequence += 1
        yield LogEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level="info",
            stage="start",
            message="Solver process started.",
            sequence=self.log_sequence,
        )

        log_queue: asyncio.Queue[str] = asyncio.Queue()
        stop_event = threading.Event()
        model, vars = await self._build_model(problem, timeout=timeout)

        # Run SCIP in a separate thread (non-blocking for the asyncio loop)
        loop = asyncio.get_running_loop()
        solver_thread = threading.Thread(
            target=self._run_solver_in_thread,
            args=(model, log_queue, stop_event, loop, timeout),
            daemon=True,
        )
        solver_thread.start()

        # Process logs from the queue until the solver is finished
        while not stop_event.is_set() or not log_queue.empty():
            try:
                log_line = await asyncio.wait_for(log_queue.get(), timeout=0.1)
                event = self._parse_log_line(log_line, self.log_sequence)
                if event:
                    yield event
                    self.log_sequence += 1
            except asyncio.TimeoutError:
                continue

        solver_thread.join()
        runtime_ms = int((time.time() - start_time) * 1000)

        # Yield the final result event (best solution only)
        solution = self._extract_solution(model, problem, vars)
        self.log_sequence += 1
        yield ResultEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            solution=solution,
            runtime_milliseconds=runtime_ms,
            sequence=self.log_sequence,
        )

        # Yield the end event
        yield EndEvent(success=True)

    def _run_solver_in_thread(
        self,
        model: Model,
        log_queue: asyncio.Queue,
        stop_event: threading.Event,
        loop: asyncio.AbstractEventLoop,
        timeout: Optional[float],
    ):
        """
        Worker thread target:
          - Redirect SCIP output into Python.
          - Replace stdout/stderr with a line-buffering writer that forwards lines
            to the main asyncio loop (queue.put_nowait).
          - Optionally set a time limit via SCIP param (simple approach).
        """
        import threading
        from contextlib import redirect_stderr, redirect_stdout

        # Ensure SCIP logs go to Python instead of terminal
        try:
            model.redirectOutput()
        except Exception:
            # If unavailable on this build, logs may still go to stdout; our redirect_* will capture them.
            pass

        # Apply internal time limit (does not include model build time; kept simple by design)
        if timeout is not None and timeout > 0:
            try:
                model.setRealParam("limits/time", float(timeout))
            except Exception:
                model.setParam("limits/time", float(timeout))

        class _LineWriter:
            """Thread-safe, line-buffered writer pushing lines to asyncio queue on the main loop."""

            __slots__ = ("_buf", "_lock", "_loop", "_queue")

            def __init__(self, loop_, queue_):
                self._buf: list[str] = []
                self._lock = threading.Lock()
                self._loop = loop_
                self._queue = queue_

            def write(self, s: str):
                with self._lock:
                    self._buf.append(s)
                    chunk = "".join(self._buf)
                    if "\n" not in chunk:
                        return
                    *lines, rest = chunk.split("\n")
                    self._buf = [rest] if rest else []
                for ln in lines:
                    ln = ln.rstrip("\r")
                    if ln:
                        # Schedule into the asyncio loop without creating a coroutine
                        self._loop.call_soon_threadsafe(self._queue.put_nowait, ln)

            def flush(self):
                pass

            def flush_leftover(self):
                with self._lock:
                    leftover = "".join(self._buf).strip()
                    self._buf.clear()
                if leftover:
                    self._loop.call_soon_threadsafe(self._queue.put_nowait, leftover)

        writer = _LineWriter(loop, log_queue)

        try:
            with redirect_stdout(writer), redirect_stderr(writer):
                model.optimize()
        finally:
            # Flush last partial line and signal completion
            try:
                writer.flush_leftover()
            except Exception:
                pass
            stop_event.set()

    def _parse_log_line(self, line: str, sequence: int) -> Optional[SolverEvent]:
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
                    sequence=sequence,
                )
            except (ValueError, IndexError):
                # Fallback for parsing errors
                return LogEvent(timestamp=ts, level="info", stage="solving", message=line.strip(), sequence=sequence)
        elif line.strip():
            # It's a standard log line
            return LogEvent(timestamp=ts, level="info", stage="presolve", message=line.strip(), sequence=sequence)
        return None

    async def _build_model(self, problem: MIPProblem, timeout: Optional[float] = None) -> Tuple[Model, Dict[str, Any]]:
        """Builds a pyscipopt.Model instance from a MIPProblem definition."""
        model = Model(problem.parameters.name)

        # Simple time limit (solver-side). This does NOT include build time (kept minimal).
        if timeout is not None and timeout > 0:
            model.setParam("limits/time", float(timeout))

        vars: Dict[str, Any] = {}
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
        status_map = {
            "optimal": "optimal",
            "infeasible": "infeasible",
            "unbounded": "unbounded",
            "timelimit": "timeout",
            "userinterrupt": "timeout",  # Map interrupt to timeout
            "gaplimit": "gaplimit",
            "solutionlimit": "solutionlimit",
            "memorylimit": "memorylimit",
            "nodelimit": "nodelimit",
        }
        raw_status = model.getStatus()
        status = status_map.get(raw_status, "not solved")

        objective_value = None
        solution_vars: Dict[str, float] = {}
        mip_gap: Optional[float] = None
        slacks: Dict[str, float] = {}
        duals: Dict[str, float] = {}
        reduced_costs: Dict[str, float] = {}

        if model.getNSols() > 0:
            # Best solution & objective
            try:
                solution = model.getBestSol()
                objective_value = model.getSolObjVal(solution)
            except Exception:
                solution = model.getBestSol()
                objective_value = model.getObjVal()

            # Variable values
            for var_name, var in vars.items():
                try:
                    solution_vars[var_name] = model.getSolVal(solution, var)
                except Exception:
                    pass

            # MIP gap if applicable
            is_mip = any(v.category != "Continuous" for v in problem.variables)
            if is_mip:
                try:
                    mip_gap = model.getGap()
                except Exception:
                    mip_gap = None

            # Slacks (named constraints only)
            for const_data in problem.constraints:
                if not const_data.name:
                    continue
                activity = 0.0
                for coeff in const_data.coefficients:
                    if coeff.name in solution_vars:
                        activity += solution_vars[coeff.name] * coeff.value

                rhs = 1e20
                lhs = -1e20
                if const_data.sense == -1:  # LEQ
                    rhs = -const_data.constant if const_data.constant is not None else 0.0
                elif const_data.sense == 1:  # GEQ
                    lhs = -const_data.constant if const_data.constant is not None else 0.0
                elif const_data.sense == 0:  # EQ
                    rhs = -const_data.constant if const_data.constant is not None else 0.0
                    lhs = rhs

                if rhs < 1e20:
                    slacks[const_data.name] = rhs - activity
                elif lhs > -1e20:
                    slacks[const_data.name] = activity - lhs

            # Duals & reduced costs for LPs
            if not is_mip:
                try:
                    for c in model.getConss():
                        if c.isLinear():
                            duals[c.name] = model.getDualSolVal(c)
                    for v_name, v_obj in vars.items():
                        reduced_costs[v_name] = model.getVarRedcost(v_obj)
                except Exception:
                    pass

        return MIPSolution(
            name=problem.parameters.name,
            status=status,
            objective_value=objective_value,
            variables=solution_vars,
            mip_gap=mip_gap,
            slacks=slacks or None,
            duals=duals or None,
            reduced_costs=reduced_costs or None,
        )
