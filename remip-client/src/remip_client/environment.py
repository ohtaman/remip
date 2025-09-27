import sys


def get_environment():
    """Checks if the code is running in CPython, Pyodide/Node, or Pyodide/Browser."""
    if "pyodide" not in sys.modules:
        return "cpython"

    # js module is only available in pyodide
    import js

    if hasattr(js, "process"):
        return "pyodide-node"

    return "pyodide-browser"
