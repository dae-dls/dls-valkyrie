class Writer:
    def __init__(self, configuration):
        self.configuration = configuration
        self.descriptor = "server to dummy"

    # ------------------------------------------------------------
    # Activate the server.  Gives already-waiting clients a chance to connect.
    def activate(self):
        pass

    # ------------------------------------------------------------
    def write(self, meta, data):
        pass
