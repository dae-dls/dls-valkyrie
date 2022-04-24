import json

import logging

logger = logging.getLogger(__name__)


class Writer:
    def __init__(self, configuration):
        self.configuration = configuration
        self.count = 0
        self.descriptor = "writing to " + self.configuration["filename_pattern"]

    # ------------------------------------------------------------
    # Activate the server.  Gives already-waiting clients a chance to connect.
    def activate(self):
        pass

    # ------------------------------------------------------------
    def write(self, meta, data):
        # Convert meta dict into json string.
        metadata_json = json.dumps(meta, indent=4)

        json_filename = self.configuration["filename_pattern"] % (self.count) + ".json"

        with open(json_filename, "w") as output_file:
            output_file.write(metadata_json)

        data_filename = self.configuration["filename_pattern"] % (self.count) + ".data"

        with open(data_filename, "wb") as output_file:
            output_file.write(data.memoryview)

        self.count = self.count + 1
