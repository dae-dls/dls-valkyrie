import zmq
import json
import base64

import logging

logger = logging.getLogger(__name__)


class Reader:
    def __init__(self, configuration):
        self.configuration = configuration
        self.context = None
        self.socket = None
        self.is_activated = False
        self.send_timeout_milliseconds = configuration.get("send_timeout", 100)
        self.recv_timeout_milliseconds = configuration.get("recv_timeout", 3000)
        self.descriptor = "client to " + configuration["endpoint"]

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
            self.context.RCVTIMEO = self.recv_timeout_milliseconds
            self.context.SNDTIMEO = self.send_timeout_milliseconds
            # Create a zmq socket.
            self.socket = self.context.socket(zmq.REQ)

        # Not already activated?
        if not self.is_activated:
            endpoint = self.configuration["endpoint"]

            logger.debug("%s connecting" % (self.descriptor))
            self.socket.connect(endpoint)

            self.socket.setsockopt(zmq.LINGER, 0)

            self.is_activated = True

    # ------------------------------------------------------------
    def wait_for_send(self):

        return

    # ------------------------------------------------------------
    def wait_for_recv(self):

        return

    # ------------------------------------------------------------
    # Write response.
    def send(self, request, response):
        # Make sure we are active.
        self.activate()

        # Check that socket is immediately ready, throwing exception if not.
        self.wait_for_send()

        # Serialize request to json.
        request_json = json.dumps(request)

        # logger.debug("sending: %s" % (request_json))

        # Send request.
        self.socket.send_string(request_json)

        # Wait for response.
        self.wait_for_recv()

        # Receive the response.
        response_json = self.socket.recv(0)

        # Parse response.
        try:
            response.update(json.loads(response_json.decode("utf-8")))
        except Exception as exception:
            raise RuntimeError("response is not json: %s" % (exception))
