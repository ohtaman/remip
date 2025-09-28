const { loadPyodide } = require("pyodide");
const path = require("path");
const fs = require("fs");
const http = require("http");
const nodeFetch = require("node-fetch");

const PORT = 8888;
const PROJECT_ROOT = path.join(__dirname, "..", "..");

// --- Simple HTTP Server ---
const server = http.createServer((req, res) => {
    const filePath = path.join(PROJECT_ROOT, req.url);
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

// Use real fetch for the environment
global.fetch = nodeFetch.default;
global.Response = nodeFetch.Response;
global.ReadableStream = nodeFetch.ReadableStream;

// --- Mock for the Solver API ---
const solverMockFetch = async (url, options) => {
    console.log(`Solver mock fetch intercepted: ${options.method} ${url}`);
    const body = JSON.parse(options.body);

    if (body.name === "Error_Problem") {
        return new nodeFetch.Response("Internal Server Error", { status: 500 });
    }

    const isStreaming = url.includes("stream=sse");
            const solution = {
                name: body.name? body.name : "Default_Problem",
                status: "Optimal",
                objective_value: isStreaming ? 2.0 : 1.0,
                variables: isStreaming ? { "x_stream": 2.0 } : { "x": 1.0 },
            };
    console.log("Mocking solution:", solution);
    if (isStreaming) {
        const stream = new nodeFetch.ReadableStream({
            start(controller) {
                const sse_data = `event: result\ndata: ${JSON.stringify({solution})}\n\n`;
                controller.enqueue(new TextEncoder().encode(sse_data));
                controller.close();
            }
        });
        return new nodeFetch.Response(stream, { status: 200, headers: { "Content-Type": "text/event-stream" } });
    } else {
        return new nodeFetch.Response(JSON.stringify(solution), { status: 200, headers: { "Content-Type": "application/json" } });
    }
};


async function main() {
    server.listen(PORT, () => console.log(`HTTP server listening on port ${PORT}`));

    try {
        console.log("Loading Pyodide...");
        const pyodide = await loadPyodide();

        // Inject the mock fetch for the solver into the global scope so Python can import it
        global.solverMockFetch = solverMockFetch;

        console.log("Finding wheel...");
        const distDir = path.join(PROJECT_ROOT, "dist");
        console.log(`distDir ----- ${distDir}`)
        const wheelFile = fs.readdirSync(distDir).find(file => file.endsWith(".whl"));
        if (!wheelFile) {
            throw new Error(`Could not find wheel file in ${distDir}.`);
        }
        const wheelURL = `http://localhost:${PORT}/dist/${wheelFile}`;

        console.log(`Installing wheel from URL: ${wheelURL}`);
        await pyodide.loadPackage("micropip");
        const micropip = pyodide.pyimport("micropip");
        await micropip.install(wheelURL);

        console.log("Running Python Stream Isolation Test...");
        const pythonTestScript = fs.readFileSync(path.join(__dirname, "py_stream_isolation_test.py"), "utf8");
        pyodide.runPython(pythonTestScript);
        const mainCoro = pyodide.globals.get("main_coro");
        await mainCoro;
        console.log("\n✅ Stream isolation test complete.");

    } catch (e) {
        console.error("\n❌ Pyodide/Node.js tests failed:");
        console.error(e);
        process.exit(1);
    } finally {
        console.log("Shutting down HTTP server.");
        server.close();
    }
}

main();
