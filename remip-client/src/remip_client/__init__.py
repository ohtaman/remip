import sys
import types

# If running in a Pyodide environment, apply a hack to create a fake 'ssl' module.
# This is necessary because some libraries (like pulp) try to import 'ssl' even if they
# don't use it, which causes a ModuleNotFoundError in Pyodide.
if "pyodide" in sys.modules:
    # A dummy class for the context object returned by ssl.create_default_context()
    class DummyContext:
        def __setattr__(self, name, value):
            pass

        def __getattr__(self, name):
            return lambda *args, **kwargs: None

    # The fake ssl module itself
    class FakeSSL(types.ModuleType):
        def __init__(self, name):
            super().__init__(name)
            self.OPENSSL_VERSION = "dummy"
            self.SSLContext = lambda *args, **kwargs: DummyContext()
            self.create_default_context = lambda *args, **kwargs: DummyContext()
            self.PROTOCOL_TLS_CLIENT = "dummy_protocol"
            self.CERT_NONE = "dummy_cert_none"

    sys.modules["ssl"] = FakeSSL("ssl")
