import zmq
import json

import logging

logger = logging.getLogger(__name__)


class Reader:
    def __init__(self, configuration):
        self.configuration = configuration
        self.recv_timeout_milliseconds = int(
            configuration.get("recv_timeout_milliseconds", 0)
        )
        self.context = None
        self.socket = None
        self.poller = None
        self.is_activated = False
        self.descriptor = "client to " + configuration["endpoint"]

    # ----------------------------------------------------------------
    def __del__(self):

        if self.socket is not None:
            if self.poller is not None:
                self.poller.register(self.socket, 0)

            self.socket.close()
            logger.debug("%s closed socket" % (self.descriptor))

        if self.context is not None:
            self.context.destroy()
            logger.debug("%s destroyed context" % (self.descriptor))

    # ------------------------------------------------------------
    # Activate the server.  Gives already-waiting clients a chance to connect.
    def activate(self):

        if self.context is None:
            # Create zmq context.
            self.context = zmq.Context()
            # Create a zmq socket.
            self.socket = self.context.socket(zmq.SUB)

        # Not already activated?
        if not self.is_activated:
            endpoint = self.configuration["endpoint"]

            logger.debug("%s connecting" % (self.descriptor))
            self.socket.connect(endpoint)

            self.socket.setsockopt(zmq.LINGER, 0)

            # Newly created ZMQ_SUB sockets shall filter out all incoming messages.
            # Therefore you should call this option to establish an initial message filter.
            # An empty option_value of length zero shall subscribe to all incoming messages.
            self.socket.setsockopt_string(zmq.SUBSCRIBE, "")

            self.poller = zmq.Poller()
            self.poller.register(self.socket, zmq.POLLIN)

            self.is_activated = True

    # ------------------------------------------------------------
    def read(self, meta, data):

        if not self.is_activated:
            self.activate()

        meta.clear()
        data.memoryview = None

        # There is a timeout configured?
        if self.recv_timeout_milliseconds > 0:
            # Wait until timeout reached for input to arrive.
            events = self.poller.poll(self.recv_timeout_milliseconds)
            if len(events) == 0:
                return

        # Receive frames of the message.
        frames = self.socket.recv_multipart(0, False)

        # Verify we got the two frames we expect as part of Valkyrie protocol.
        if len(frames) != 2:
            raise RuntimeError("frames count was %d but expected 2" % len(frames))

        # Parse meta.
        try:
            meta.update(json.loads(frames[0].bytes.decode("utf-8")))
        except Exception as exception:
            raise RuntimeError("meta is not json: %s" % (exception))

        # Return mapped (not copied) raw buffer which was received.
        data.memoryview = frames[1].buffer

        # logger.debug("raw data of %d bytes" % (data.memoryview.nbytes))
