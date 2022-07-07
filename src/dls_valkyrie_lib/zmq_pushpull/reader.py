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
        self.descriptor = "zmq_pushpull client to " + configuration["endpoint"]

        try:
            # Get configured high water mark.
            # This is how much to keep in the send buffer.
            self._high_water_mark = int(configuration.get("high_water_mark", 10000))
        except Exception as exception:
            raise RuntimeError(
                "%s unable to get high_water_mark from configuration"
                % (self.descriptor)
            )

    # ----------------------------------------------------------------
    def __del__(self):

        if self.socket is not None:
            if self.poller is not None:
                self.poller.register(self.socket, 0)

            self.socket.close()
            logger.info("%s closed socket" % (self.descriptor))

        if self.context is not None:
            self.context.destroy()
            logger.info("%s destroyed context" % (self.descriptor))

    # ------------------------------------------------------------
    # Activate the server.  Gives already-waiting clients a chance to connect.
    def activate(self):

        if self.context is None:
            # Create zmq context.
            self.context = zmq.Context()
            # Create a zmq socket.
            self.socket = self.context.socket(zmq.PULL)

            # Buffer messages according to configuration.
            self.socket.set_hwm(self._high_water_mark)

        # Not already activated?
        if not self.is_activated:
            endpoint = self.configuration["endpoint"]

            logger.info(
                "%s connecting with recv_timeout_milliseconds %d and high_water_mark %s"
                % (
                    self.descriptor,
                    self.recv_timeout_milliseconds,
                    self._high_water_mark,
                )
            )
            self.socket.connect(endpoint)

            self.socket.setsockopt(zmq.LINGER, 0)

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
