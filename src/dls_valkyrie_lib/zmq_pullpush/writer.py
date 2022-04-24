import zmq
import json
import base64

import logging

logger = logging.getLogger(__name__)


class Writer:
    """
    Writer connects to a server and pushes.
    Multiple writers can push to the same reader.
    """

    def __init__(self, configuration):
        self.configuration = configuration
        self.context = None
        self.socket = None
        self.is_activated = False
        self.descriptor = "zmq pullpush server to " + configuration["endpoint"]

        try:
            # Get configured high water mark.
            # This is how much to keep in the send buffer.  
            # Recommend low, even 1 should be ok unless a slow reader.
            self._high_water_mark = int(
                configuration.get("high_water_mark", 10)
            )
        except Exception as exception:
            raise RuntimeError("%s unable to get high_water_mark from configuration due to exception: %s" % (self.descriptor, str(exception)))

    # ----------------------------------------------------------------
    def __del__(self):

        if self.socket is not None:
            logger.info("%s closed socket" % (self.descriptor))
            self.socket.close()

        if self.context is not None:
            self.context.destroy()
            logger.info("%s destroyed context" % (self.descriptor))

    # ------------------------------------------------------------
    # Activate the server.
    def activate(self):

        if self.context is None:
            # Create zmq context.
            self.context = zmq.Context()
            # Create a zmq socket.
            self.socket = self.context.socket(zmq.PUSH)

            # Buffer messages according to configuration.
            self.socket.set_hwm(self._high_water_mark)

        # Not already activated?
        if not self.is_activated:
            endpoint = self.configuration["endpoint"]

            logger.info("%s connecting with high_water_mark %d" % (self.descriptor, self._high_water_mark))

            self.socket.connect(endpoint)

            self.socket.setsockopt(zmq.LINGER, 0)

            self.is_activated = True

    # ------------------------------------------------------------
    def write(self, meta, data):

        if not self.is_activated:
            self.activate()

        # Convert meta dict into json string.
        metadata_json = json.dumps(meta)

        try:
            # Send meta string with noblock.
            self.socket.send_string(metadata_json, (zmq.SNDMORE | zmq.NOBLOCK))
            ok_to_send_data = True

        except zmq.ZMQError as exception:
            # Errno 11 means there is no listener, which we want to tolerate.
            if exception.errno == 11:
                ok_to_send_data = False
            else:
                raise RuntimeError("%s: unable to push data due to %s: (%d) %s" % (self.descriptor, type(exception).__name__, exception.errno, str(exception)))

        if ok_to_send_data:
            # Send data entire, this time don't block.
            # logger.debug("%s writing data length %d" % (self.descriptor, data.memoryview.nbytes))
            # TODO: See if copy=False is appropriate in pushpull writer.
            self.socket.send(data.memoryview)
        # else:
        #     logger.warning("%s write failed on noblock" % (self.descriptor))
