import json
from abc import ABC, abstractmethod

try:
    import js
except ImportError:
    # These modules are only available in the Pyodide environment
    pass


class Response(ABC):
    @abstractmethod
    def json(self):
        pass

    @abstractmethod
    def iter_lines(self):
        pass

    @abstractmethod
    def raise_for_status(self):
        pass


class RequestsResponse(Response):
    def __init__(self, response):
        self._response = response

    def json(self):
        return self._response.json()

    def iter_lines(self):
        return self._response.iter_lines()

    def raise_for_status(self):
        return self._response.raise_for_status()


class ErrorResponse(Response):
    def __init__(self, error_message: str):
        self._error_message = error_message

    def json(self):
        raise IOError(self._error_message)

    def iter_lines(self):
        raise IOError(self._error_message)

    def raise_for_status(self):
        raise IOError(self._error_message)


class HttpClient(ABC):
    def __init__(self, base_url: str, stream: bool):
        self.base_url = base_url
        self.stream = stream

    def _build_url(self) -> str:
        url = f"{self.base_url}/solve"
        if self.stream:
            url += "?stream=sse"
        return url

    @abstractmethod
    def solve(self, json_data: dict) -> Response:
        pass

    def close(self):
        pass


class RequestsHttpClient(HttpClient):
    """HttpClient implementation using the requests library for CPython."""

    def __init__(self, base_url: str, stream: bool):
        import requests

        self.session = requests.Session()
        super().__init__(base_url, stream)

    def solve(self, json_data: dict, timeout: float | None) -> Response:
        import requests

        full_url = self._build_url()
        try:
            response = self.session.post(
                full_url,
                json=json_data,
                stream=self.stream,
                params={"timeout": timeout},
            )
            response.raise_for_status()
            return RequestsResponse(response)
        except requests.exceptions.RequestException as e:
            # TODO: Add more specific error handling
            print(f"An error occurred: {e}")
            return ErrorResponse(str(e))


class PyodideResponse:
    def __init__(self, js_response):
        self._js_response = js_response

    async def json(self):
        if not self._js_response.body:
            return None
        # pyodide.ffi.JsProxy.to_py() is needed to recursively convert the JS object
        return (await self._js_response.json()).to_py()

    async def iter_lines(self):
        if not self._js_response.body:
            yield b""
            return
        # Based on https://pyodide.org/en/stable/usage/api/python-api/http.html#pyodide.http.pyfetch
        reader = self._js_response.body.getReader()
        decoder = js.TextDecoder.new()
        buffer = ""

        while True:
            chunk = await reader.read()
            # Handle both JS objects with .done attribute and Python dicts
            done = chunk.done if hasattr(chunk, "done") else chunk.get("done", False)
            if done:
                if buffer:
                    yield buffer.encode("utf-8")
                break

            # Handle both JS objects with .value attribute and Python dicts
            value = chunk.value if hasattr(chunk, "value") else chunk.get("value")
            if value:
                buffer += decoder.decode(value)

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                yield line.encode("utf-8")

    def raise_for_status(self):
        # The check is done in the client, so this can pass
        pass


class PyodideHttpClient(HttpClient):
    async def solve(self, json_data: dict, timeout: float | None = None) -> Response:
        return await self._post_async(json_data, timeout)

    async def _post_async(
        self, json_data: dict, timeout: float | None = None
    ) -> Response:
        full_url = self._build_url()

        try:
            from js import solverMockFetch

            fetch_func = solverMockFetch
        except ImportError:
            fetch_func = js.fetch

        headers = js.Headers.new()
        headers.append("Content-Type", "application/json")
        kwargs = {
            "method": "POST",
            "body": json.dumps(json_data),
            "headers": headers,
        }
        response = await fetch_func(full_url, **kwargs)

        if not response.ok:
            raise IOError(f"HTTP Error: {response.status} {response.statusText}")

        return PyodideResponse(response)
