import zmq
import json

import logging

logger = logging.getLogger(__name__)


class Reader:
    """
    Reader binds to a port and pulls messages.
    Multiple writers can push to this reader.
    """

    def __init__(self, configuration):
        self.configuration = configuration
        self.recv_timeout_milliseconds = int(
            configuration.get("recv_timeout_milliseconds", 0)
        )
        self.context = None
        self.socket = None
        self.poller = None
        self.is_activated = False
        self.descriptor = "zmq_pullpush client to " + configuration["endpoint"]

        self.count = 0

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

            # Buffer only one message at a time.
            self.socket.set_hwm(1)

        # Not already activated?
        if not self.is_activated:
            endpoint = self.configuration["endpoint"]

            logger.info(
                "%s binding with recv_timeout_milliseconds %s"
                % (self.descriptor, self.recv_timeout_milliseconds)
            )

            self.socket.bind(endpoint)

            # Release port as soon as it is closed.
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

        self.count = self.count + 1

        # Receive frames of the message.
        frames = self.socket.recv_multipart(0, False)

        # Verify we got the two frames we expect as part of Valkyrie protocol.
        if len(frames) != 2:
            logger.debug(
                "%s at message %d contained %d frames but expected 2..."
                % (self.descriptor, self.count, len(frames))
            )
            for i in range(0, len(frames)):
                try:
                    content = frames[i].bytes.decode("utf-8")
                    content = json.loads(content)
                    content = json.dumps(content)
                except Exception as exception:
                    if len(content) > 100:
                        content = content[0:100] + "..."
                    content = 'non-json length %d "%s"' % (
                        len(frames[i].bytes),
                        content,
                    )
                logger.debug("  %d. %s" % (i, content))
            raise RuntimeError(
                "%s at message %d contained %d frames but expected 2"
                % (self.descriptor, self.count, len(frames))
            )

        # Parse meta.
        try:
            meta.update(json.loads(frames[0].bytes.decode("utf-8")))
        except Exception as exception:
            raise RuntimeError("%s meta is not json: %s" % (self.descriptor, exception))

        # Return mapped (not copied) raw buffer which was received.
        data.memoryview = frames[1].buffer

        # logger.debug("raw data of %d bytes" % (data.memoryview.nbytes))
