# Technical Design: Pyodide Support for remip-client

## 1. Introduction

This document provides the technical design for adding Pyodide support to the `remip-client` library, as specified in the approved requirements document. The core of this design is to abstract the HTTP communication layer to work in both standard Python and Pyodide environments without altering the public API of the `ReMIPSolver`.

## 2. Proposed Architecture

We will introduce an HTTP client abstraction to handle the differences between the `requests` library (for CPython) and the `pyodide.http` module (for Pyodide). This logic will reside in a new `http_client.py` module.

### 2.1. Environment Detection
A utility function will be used to determine the current execution environment.

```python
# remip_client/environment.py
import sys
import js

def get_environment():
    """Checks if the code is running in CPython, Pyodide/Node, or Pyodide/Browser."""
    if "pyodide" not in sys.modules:
        return "cpython"
    if hasattr(js, "process"):
        return "pyodide-node"
    return "pyodide-browser"
```

### 2.2. HTTP Client Abstraction
...
#### 2.2.3. Pyodide Implementation (`PyodideHttpClient`)
This class will use `js.fetch` to make requests within the Node.js environment. Since `fetch` is asynchronous, we will use `pyodide.ffi.run_sync` to bridge the async call.

```python
# remip_client/http_client.py
import json
from urllib.parse import urlencode
from pyodide.ffi import run_sync
import js

class PyodideHttpClient(HttpClient):
    async def _post_async(self, url, params, json_data, timeout, stream):
        kwargs = {
            "method": "POST",
            "body": json.dumps(json_data),
            "headers": js.Headers.new({"Content-Type": "application/json"}),
        }
        # Note: timeout is not directly supported in node-fetch like in requests
        full_url = f"{url}?{urlencode(params)}" if params else url
        response = await js.fetch(full_url, **kwargs)
        if not response.ok:
            raise Exception(f"HTTP Error: {response.status} {response.statusText}")
        return response

    def post(self, url, params, json, timeout, stream=False):
        return run_sync(self._post_async(url, params, json, timeout, stream))
```
*Note: The response object from `js.fetch` is a JavaScript Response. We will need to create a wrapper/adapter to provide a consistent interface for methods like `json()` and `iter_lines()`.*

### 2.3. `ReMIPSolver` Integration
The `ReMIPSolver` will be modified to use the new HTTP client abstraction.

```python
# remip_client/solver.py
from .environment import get_environment
from .http_client import RequestsHttpClient, PyodideHttpClient

class ReMIPSolver(LpSolver):
    def __init__(self, base_url="http://localhost:8000", ...):
        super().__init__(**kwargs)
        # ...
        self.environment = get_environment()
        if self.environment == "pyodide-node":
            self._client = PyodideHttpClient()
        elif self.environment == "cpython":
            self._client = RequestsHttpClient()
        else:
            # Or raise an error for unsupported environments like pyodide-browser
            raise NotImplementedError("This environment is not supported.")
...
```
### 2.4. Streaming Response Handling in Pyodide
The streaming implementation will be similar to the browser approach, as Node.js `fetch` also provides a `ReadableStream` (`response.body`). The logic for reading from the stream, decoding, and yielding lines remains conceptually the same, but will use the stream implementation provided by the Node.js environment via `js`.


## 3. File Modifications

- **`remip-client/src/remip_client/solver.py`**: Will be updated to remove direct `requests` calls and use the `HttpClient` abstraction.
- **`remip-client/src/remip_client/http_client.py`** (New File): Will contain the `HttpClient` ABC and its two concrete implementations.
- **`remip-client/src/remip_client/environment.py`** (New File): Will contain the `is_pyodide` utility function.

## 4. Summary

This design introduces a clean abstraction over the HTTP communication layer, allowing `remip-client` to support both CPython and Pyodide environments with minimal changes to the core solver logic. It addresses the key challenges of asynchronous APIs in a synchronous context and streaming data handling.
