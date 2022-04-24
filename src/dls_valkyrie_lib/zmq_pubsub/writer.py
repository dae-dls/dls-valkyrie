import zmq
import json
import base64

import logging

logger = logging.getLogger(__name__)


class Writer:
    def __init__(self, configuration):
        self.configuration = configuration
        self.context = None
        self.socket = None
        self.is_activated = False
        self.descriptor = "zmq pubsub server to " + configuration["endpoint"]

        try:
            # Get configured high water mark.
            # This is how much to keep in the send buffer.  
            # Recommend low, even 1 should be ok unless a slow reader.
            self._high_water_mark = int(
                configuration.get("high_water_mark", 10)
            )
        except Exception as exception:
            raise RuntimeError("%s unable to get high_water_mark from configuration" % (self.descriptor))

    # ----------------------------------------------------------------
    def __del__(self):

        if self.socket is not None:
            rc = self.socket.close()
            logger.debug("%s closed socket" % (self.descriptor))

        if self.context is not None:
            rc = self.context.destroy()
            logger.debug("%s destroyed context" % (self.descriptor))

    # ------------------------------------------------------------
    # Activate the server.  Gives already-waiting clients a chance to connect.
    def activate(self):

        if self.context is None:
            # Create zmq context.
            self.context = zmq.Context()

            # Create a zmq socket.
            self.socket = self.context.socket(zmq.PUB)

            # Buffer messages according to configuration.
            self.socket.set_hwm(self._high_water_mark)

        # Not already activated?
        if not self.is_activated:
            endpoint = self.configuration["endpoint"]

            logger.info("%s binding with high_water_mark %d" % (self.descriptor, self._high_water_mark))

            self.socket.bind(endpoint)

            # Release port as soon as it is closed.
            self.socket.setsockopt(zmq.LINGER, 0)

            self.is_activated = True

    # ------------------------------------------------------------
    def write(self, meta, data):

        if not self.is_activated:
            self.activate()

        # Convert meta dict into json string.
        metadata_json = json.dumps(meta)

        # logger.debug("%s writing meta %s" % (self.descriptor, metadata_json))

        # Send meta string.
        self.socket.send_string(metadata_json, zmq.SNDMORE)

        # logger.debug("%s writing data length %d" % (self.descriptor, data.memoryview.nbytes))

        # Send data entire.
        self.socket.send(data.memoryview)
