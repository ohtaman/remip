# ReMIP Client

**ReMIP Client** is a Python client for the ReMIP optimization server. It lets you solve complex Mixed-Integer Programming (MIP) problems using a remote, high-performance solver, and it's compatible with the popular [PuLP](https://coin-or.github.io/pulp/) modeling library.

You can use this client in standard Python scripts, in a web browser, or in a Node.js application.

## Key Features

- **PuLP Compatible**: Integrates seamlessly with your existing PuLP models.
- **Remote Solving**: Offload heavy optimization tasks to a powerful remote server. No local solver installation is needed.
- **Cross-Environment**: Run the same optimization code in Python, a browser (with Pyodide), or Node.js.
- **Real-time Monitoring**: Use streaming mode to get live updates on the solver's progress.

## Prerequisites

**The ReMIP server must be running** for the client to work. The examples below assume the server is running and accessible at `http://localhost:8000`.

For instructions on how to run the server, please see the documentation in the `remip/` directory.

## Installation

### For a Standard Python (CPython) Project

```bash
# Navigate to the remip-client directory
cd remip-client

# Install the client and its dependencies
uv pip install -e .
```

### For Browser or Node.js (Pyodide)

When using the client with Pyodide, you first need to **build and serve** the client's `.whl` file. Pyodide installs packages from URLs.

```bash
# 1. Navigate to the remip-client directory
cd remip-client

# 2. Build the wheel file
uv run python -m build --wheel
# This creates a file like `dist/remip_client-0.1.0-py3-none-any.whl`

# 3. Start a local server to provide this file to Pyodide
python -m http.server 8888
# Now the wheel is available at http://localhost:8888/dist/remip_client-0.1.0-py3-none-any.whl
```

## Usage Examples

### Example 1: Standard Python Environment

This is the most common use case. The client integrates directly with PuLP's synchronous `solve()` method.

> **Note:** Ensure the ReMIP server is running before executing this code.

```python
from pulp import LpProblem, LpVariable, LpMaximize, LpStatus
from remip_client.solver import ReMIPSolver

# 1. Define a PuLP problem
prob = LpProblem("simple_test", LpMaximize)
x = LpVariable("x", 0, 1, cat='Binary')
y = LpVariable("y", 0, 1, cat='Binary')
prob += x + y, "objective"
prob += 2*x + y <= 2, "constraint1"

# 2. Initialize the remote solver
solver = ReMIPSolver(url="http://localhost:8000", stream=False)

# 3. Solve the problem using PuLP's standard method
prob.solve(solver)

# 4. Print the results
print(f"Status: {LpStatus[prob.status]}")
for v in prob.variables():
    print(f"{v.name} = {v.varValue}")
```

### Example 2: In a Web Browser with Pyodide

This example creates a self-contained HTML file that runs a ReMIP optimization problem in the browser.

> **Note:** Ensure the ReMIP server is running. You must also serve this HTML file and the `dist` directory from a local web server (e.g., by running `python -m http.server 8888` in the `remip-client` directory).

```html
<!-- index.html -->
<html>
  <head>
    <title>ReMIP Client - Browser Demo</title>
    <meta charset="UTF-8">
    <script src="https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js"></script>
    <style>
      body { font-family: sans-serif; line-height: 1.5; }
      h2, h3 { color: #333; }
      pre { background-color: #f4f4f4; padding: 1em; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; }
      #output-display { border: 1px solid #ccc; }
    </style>
  </head>
  <body>
    <h2>ReMIP Client Browser Demo</h2>
    <p>This example runs a PuLP optimization problem entirely in your browser using Pyodide and the ReMIP Client.</p>

    <h3>Python Code</h3>
    <pre id="code-display"></pre>

    <h3>Live Output</h3>
    <pre id="output-display">Loading Pyodide and setting up environment...</pre>

    <script type="text/javascript">
      const pythonCode = `
from pulp import LpProblem, LpVariable, LpMaximize, LpStatus
from remip_client.solver import ReMIPSolver

async def solve_problem():
    print("--- Defining PuLP Problem ---")
    prob = LpProblem("browser_test", LpMaximize)
    x = LpVariable("x", 0, 1, cat='Binary')
    prob += x, "objective"

    print("--- Initializing Solver ---")
    # Make sure your ReMIP server is running and accessible
    solver = ReMIPSolver(url="http://localhost:8000")

    print("--- Solving Problem (asynchronously) ---")
    await solver.solve(prob)

    print("\n--- Results ---")
    print(f"Status: {LpStatus[prob.status]}")
    print(f"Result for x: {x.varValue}")

# Return the coroutine to be awaited by JavaScript
solve_problem()
`;

      // Display the code on the page
      document.getElementById("code-display").textContent = pythonCode.trim();
      const outputElement = document.getElementById("output-display");

      function printToPage(text) {
        outputElement.textContent += text + "\n";
      }

      async function main() {
        try {
          // Load Pyodide and set up the output stream
          let pyodide = await loadPyodide({
            stdout: printToPage,
            stderr: printToPage
          });

          outputElement.textContent = "Pyodide loaded. Installing packages...\n";
          await pyodide.loadPackage("micropip");
          const micropip = pyodide.pyimport("micropip");

          // Install the ReMIP client wheel from your local server
          const wheelUrl = "http://localhost:8888/dist/remip_client-0.1.0-py3-none-any.whl";
          printToPage(`Installing wheel from ${wheelUrl}...`);
          await micropip.install(wheelUrl);
          printToPage("Installation complete.\n");

          // Run the main Python code
          await pyodide.runPythonAsync(pythonCode);
          printToPage("\n✅ Demo finished successfully!");

        } catch (error) {
          printToPage(`\n❌ An error occurred: ${error}`);
        }
      }
      main();
    </script>
  </body>
</html>
```

### Example 3: In a Node.js Environment with Pyodide

This example uses the client in a Node.js script.

> **Note:** Ensure the ReMIP server is running before executing this code.

```javascript
// solve.js
const { loadPyodide } = require("pyodide");
const path = require("path");
const fs = require("fs");
const http = require("http");

// --- Simple HTTP Server to serve the wheel file ---
const server = http.createServer((req, res) => {
    const filePath = path.join(__dirname, req.url);
    fs.readFile(filePath, (err, data) => {
        if (err) {
            res.writeHead(404);
            res.end(JSON.stringify(err));
            return;
        }
        res.writeHead(200);
        res.end(data);
    });
});

const PORT = 8888;

async function main() {
    server.listen(PORT, () => console.log(`Server listening on http://localhost:${PORT}`));

    try {
        console.log("Loading Pyodide in Node.js...");
        const pyodide = await loadPyodide();

        const distDir = path.join(__dirname, "dist");
        const wheelFile = fs.readdirSync(distDir).find(f => f.endsWith(".whl"));
        if (!wheelFile) throw new Error("Wheel file not found. Run 'uv run python -m build --wheel' first.");

        await pyodide.loadPackage("micropip");
        const micropip = pyodide.pyimport("micropip");

        const wheelUrl = `http://localhost:${PORT}/dist/${wheelFile}`;
        console.log(`Installing wheel from ${wheelUrl}`);
        await micropip.install(wheelUrl);

        const pythonCode = `
from pulp import LpProblem, LpVariable, LpMaximize, LpStatus
from remip_client.solver import ReMIPSolver

async def solve_problem():
    print("--- Defining PuLP Problem in Node.js ---")
    prob = LpProblem("node_js_test", LpMaximize)
    x = LpVariable("x", 0, 1, cat='Binary')
    prob += x, "objective"

    solver = ReMIPSolver(url="http://localhost:8000")

    print("--- Solving Problem (asynchronously) ---")
    await solver.solve(prob)

    print("--- Results ---")
    print(f"Status: {LpStatus[prob.status]}")
    print(f"Result for x: {x.varValue}")

# Return the coroutine to be awaited by JavaScript
solve_problem()
`;
        await pyodide.runPythonAsync(pythonCode);
    } finally {
        server.close();
    }
}

main().catch(err => {
    console.error(err);
    server.close();
    process.exit(1);
});
```

## Solver Options

You can customize the solver's behavior when you create a `ReMIPSolver` instance.

- `url` (str): The URL of your ReMIP server. Defaults to `"http://localhost:8000"`.
- `stream` (bool): If `True`, the solver requests a stream of live progress from the server. Defaults to `False`.
- `timeout` (float): The maximum time in seconds for the solver to run. If the time limit is reached, the solver returns the best solution found so far. Defaults to `60`.

## License

This project is licensed under the Apache License 2.0.
