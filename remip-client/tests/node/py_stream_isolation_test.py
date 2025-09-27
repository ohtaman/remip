import asyncio
import json
import js
from pyodide.ffi import create_proxy
from remip_client.http_client import PyodideResponse


# A utility to encode SSE messages correctly
def create_sse_message(event, data):
    """Encodes an event and data into a properly formatted SSE message."""
    data_str = json.dumps(data)
    # The literal line breaks are crucial for the SSE format
    return f"event: {event}\ndata: {data_str}\n\n".encode("utf-8")


# This test isolates the streaming response logic.
async def main():
    print("--- Running Stream Isolation Test ---")

    # 1. Check if ReadableStream is available, otherwise use Node.js streams
    try:
        ReadableStream = getattr(js, "ReadableStream")
        TextEncoder = getattr(js, "TextEncoder")
        print(f"ReadableStream: {ReadableStream}")
        print(f"TextEncoder: {TextEncoder}")

        if ReadableStream is None:
            print("⚠️  ReadableStream is not available, creating a simple mock stream")

            # Create a simple mock stream that mimics ReadableStream behavior
            class MockReadableStream:
                def __init__(self, options):
                    self.options = options
                    self.controller = None
                    if "start" in options:
                        # Call the start function with a mock controller
                        mock_controller = MockController()
                        options["start"](mock_controller)
                        self.controller = mock_controller

                def getReader(self):
                    return MockReader(self.controller)

            class MockController:
                def __init__(self):
                    self.data = []
                    self.closed = False

                def enqueue(self, data):
                    if not self.closed:
                        self.data.append(data)

                def close(self):
                    self.closed = True

            class MockReader:
                def __init__(self, controller):
                    self.controller = controller
                    self.index = 0

                async def read(self):
                    if self.index < len(self.controller.data):
                        data = self.controller.data[self.index]
                        self.index += 1
                        return {"done": False, "value": data}
                    else:
                        return {"done": True, "value": None}

            ReadableStream = MockReadableStream
            print("✅ Using mock ReadableStream for streaming test")
        else:
            print("✅ Successfully accessed Web ReadableStream.")
    except AttributeError as e:
        print(f"❌ FAILED to access JS classes: {e}")
        return

    # 2. Create a mock JavaScript streaming response body
    solution = {"name": "Stream_Test", "status": "Optimal"}
    sse_message = create_sse_message("result", {"solution": solution})

    # This controller is a JS object that we can push data into
    controller = None

    def start_stream(c):
        nonlocal controller
        controller = c

    # Convert the Python function to a JavaScript function (Pyodide-safe)
    js_start_func = create_proxy(start_stream)

    # Create stream using the appropriate API
    if hasattr(ReadableStream, "new"):
        # Web ReadableStream API
        stream = ReadableStream.new({"start": js_start_func})
    else:
        # Mock ReadableStream API
        stream = ReadableStream({"start": js_start_func})

    # 3. Create a mock JS Response object
    class MockResponse:
        def __init__(self, body):
            self.body = body

    # 4. Wrap the mock JS response in our Python PyodideResponse
    py_response = PyodideResponse(MockResponse(stream))
    print("✅ Created mock streaming response.")

    # 5. Push data into the stream from the 'JS side'
    # and start reading it on the 'Python side' concurrently.
    async def stream_reader():
        lines_received = []
        print("Python: Starting to read from stream...")
        async for line in py_response.iter_lines():
            print(f"Python: Received line: {line}")
            lines_received.append(line)
        return lines_received

    reader_task = asyncio.create_task(stream_reader())

    # Wait for the reader to start processing
    while controller is None:
        await asyncio.sleep(0.01)

    print("JavaScript: Pushing data to stream...")
    # Enqueue the properly formatted SSE message
    encoder = TextEncoder.new()
    controller.enqueue(encoder.encode(sse_message))
    print("JavaScript: Closing stream...")
    controller.close()

    # 6. Check the result
    final_lines = await reader_task
    # Cleanup proxy to avoid memory leak in tests
    try:
        js_start_func.destroy()
    except Exception:
        pass

    print("\n--- Results ---")
    print(f"Final lines received by Python: {final_lines}")

    expected_line_part = b"data: "
    if final_lines and expected_line_part in final_lines[0]:
        print("✅ SUCCESS: Python correctly received the streaming data.")
    else:
        print("❌ FAILURE: Python did not receive the correct streaming data.")


# We need json for this test
main_coro = main()
