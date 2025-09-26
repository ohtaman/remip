import sys
from unittest.mock import MagicMock


from remip_client.environment import get_environment


def test_get_environment_cpython():
    """
    Verify that get_environment() returns 'cpython' when not in a Pyodide environment.
    """
    assert get_environment() == "cpython"


def test_get_environment_pyodide_node(monkeypatch):
    """
    Verify that get_environment() returns 'pyodide-node' in a mocked Pyodide/Node environment.
    """
    monkeypatch.setitem(sys.modules, "pyodide", MagicMock())
    mock_js = MagicMock()
    mock_js.process = MagicMock()
    monkeypatch.setitem(sys.modules, "js", mock_js)
    assert get_environment() == "pyodide-node"


def test_get_environment_pyodide_browser(monkeypatch):
    """
    Verify that get_environment() returns 'pyodide-browser' in a mocked Pyodide/Browser environment.
    """
    monkeypatch.setitem(sys.modules, "pyodide", MagicMock())
    # Mock the 'js' module but remove the 'process' attribute
    mock_js = MagicMock()
    del mock_js.process
    monkeypatch.setitem(sys.modules, "js", mock_js)
    assert get_environment() == "pyodide-browser"
