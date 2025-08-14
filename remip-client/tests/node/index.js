const { loadPyodide } = require("pyodide");
const path = require("path");

async function main() {
    console.log("--- Loading Pyodide for Node.js ---");
    const pyodide = await loadPyodide();

    console.log("--- Loading micropip ---");
    await pyodide.loadPackage("micropip");
    const micropip = pyodide.pyimport("micropip");

    console.log("--- Installing remip-client wheel ---");
    const wheelPath = path.resolve(__dirname, '..', '..', 'dist', 'remip_client-0.1.0-py3-none-any.whl');
    await micropip.install(`file://${wheelPath}`);

    console.log("--- Running Python test script in Node.js ---");

    const pythonCode = `
import asyncio
from pulp import LpProblem, LpVariable, lpSum, LpMaximize, LpStatus
from remip_client.solver import MipApiSolver

async def run_test():
    try:
        print("--- Node.js Test: Defining problem ---")
        prob = LpProblem("test_problem_node", LpMaximize)
        x = LpVariable("x", 0, 1, cat='Binary')
        y = LpVariable("y", 0, 1, cat='Binary')
        prob += x + y, "objective"
        prob += 2*x + y <= 2, "constraint1"
        print("--- Node.js Test: Problem defined ---")

        print("--- Node.js Test: Initializing solver ---")
        async with MipApiSolver(base_url="http://127.0.0.1:8000") as solver:
            print("--- Node.js Test: Calling solver.solve() ---")
            status = await solver.solve(prob)
            print("--- Node.js Test: solver.solve() finished ---")

        print("--- Node.js Test: Printing results ---")
        print(f"Status: {LpStatus[status]}")
        for v in prob.variables():
            print(f"{v.name} = {v.varValue}")

        assert status == 1 # LpStatusOptimal
        assert prob.status == 1 # LpStatusOptimal
        assert x.varValue == 1.0
        assert y.varValue == 0.0
        print("--- Node.js Test: Assertions Passed ---")

    except Exception as e:
        print(f"--- Node.js Test: ERROR during test: {e} ---")
        import traceback
        traceback.print_exc()
        raise

asyncio.run(run_test())
`;

    try {
        await pyodide.runPythonAsync(pythonCode);
        console.log("--- Node.js Test Succeeded! ---");
    } catch (e) {
        console.error("--- Node.js Test Failed ---");
        console.error(e);
        process.exit(1);
    }
}

main();
