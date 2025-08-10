import asyncio
import tempfile
import os
from ..models import MIPProblem, MIPSolution
from ..config import settings
from typing import AsyncGenerator

class ScipSolverWrapper:
    """
    A wrapper for the SCIP solver command-line interface.
    """

    async def solve(self, problem: MIPProblem) -> MIPSolution:
        """
        Solves a MIP problem using the SCIP command-line tool.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False) as lp_file:
            lp_file_path = lp_file.name
            lp_file.write(self._convert_to_lp_format(problem))

        sol_file_path = f"{lp_file_path}.sol"

        try:
            # Run SCIP solver
            process = await asyncio.create_subprocess_exec(
                settings.solver_path,
                "-f", lp_file_path,
                "-l", "/dev/null", # Disable interactive log
                "-q", # Quiet mode
                "-w", sol_file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"SCIP solver failed with error: {stderr.decode()}")

            # Parse the solution
            solution = self._parse_solution(sol_file_path, problem)
            return solution

        finally:
            # Clean up temporary files
            if os.path.exists(lp_file_path):
                os.remove(lp_file_path)
            if os.path.exists(sol_file_path):
                os.remove(sol_file_path)

    def _convert_to_lp_format(self, problem: MIPProblem) -> str:
        lp_string = ""

        # Objective
        if problem.sense == 1:
            lp_string += "Minimize\n"
        else:
            lp_string += "Maximize\n"
        
        obj_terms = []
        for coeff in problem.objective.coefficients:
            obj_terms.append(f"{coeff.value} {coeff.name}")
        lp_string += f"  obj: {' + '.join(obj_terms)}\n"

        # Constraints
        lp_string += "Subject To\n"
        for i, const in enumerate(problem.constraints):
            const_terms = []
            for coeff in const['coefficients']:
                const_terms.append(f"{coeff['value']} {coeff['name']}")
            
            sense = const['sense']
            rhs = const['rhs']
            
            if sense == 0: # EQ
                sense_str = "="
            elif sense == -1: # LEQ
                sense_str = "<="
            else: # GEQ
                sense_str = ">="

            lp_string += f"  c{i}: {' + '.join(const_terms)} {sense_str} {rhs}\n"

        # Bounds
        lp_string += "Bounds\n"
        for var in problem.variables.values():
            if var.lowBound is not None:
                lp_string += f"  {var.lowBound} <= {var.name}\n"
            if var.upBound is not None:
                lp_string += f"  {var.name} <= {var.upBound}\n"

        # Variable types
        generals = []
        for var in problem.variables.values():
            if var.cat == 'Integer':
                generals.append(var.name)
        
        if generals:
            lp_string += "Generals\n"
            lp_string += "  " + " ".join(generals) + "\n"

        lp_string += "End\n"
        return lp_string

    def _parse_solution(self, sol_file_path: str, problem: MIPProblem) -> MIPSolution:
        status = "Unknown"
        objective_value = 0.0
        variables = {}

        with open(sol_file_path, "r") as f:
            for line in f:
                if line.startswith("solution status:"):
                    status = line.split(":")[1].strip()
                elif line.startswith("objective value:"):
                    objective_value = float(line.split(":")[1].strip())
                elif "=" in line:
                    parts = line.split("=")
                    var_name = parts[0].strip()
                    try:
                        value = float(parts[1].strip())
                        variables[var_name] = value
                    except (ValueError, IndexError):
                        # Handle cases where the line is not a valid variable assignment
                        pass

        return MIPSolution(
            name=problem.name,
            status=status,
            objective_value=objective_value,
            variables=variables
        )


    async def solve_and_stream_logs(self, problem: MIPProblem) -> AsyncGenerator[str, None]:
        """
        Solves a MIP problem and streams the logs from the SCIP command-line tool.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False) as lp_file:
            lp_file_path = lp_file.name
            lp_file.write(self._convert_to_lp_format(problem))

        try:
            process = await asyncio.create_subprocess_exec(
                settings.solver_path,
                "-f", lp_file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT, # Redirect stderr to stdout
            )

            if process.stdout:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    yield line.decode()
            
            await process.wait()

        finally:
            if os.path.exists(lp_file_path):
                os.remove(lp_file_path)