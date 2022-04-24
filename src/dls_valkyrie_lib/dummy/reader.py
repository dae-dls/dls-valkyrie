class Reader:
    def __init__(self, configuration):
        self.configuration = configuration
        self.descriptor = "client to dummy"

    # ------------------------------------------------------------
    # Activate the server.  Gives already-waiting clients a chance to connect.
    def activate(self):
        pass

    # ------------------------------------------------------------
    def read(self, meta, data):
        meta.clear()
        data.memoryview = None

        return
