import zmq
import json
import base64

import logging

logger = logging.getLogger(__name__)


class WriterThread(Hazzathread):
    def __init__(self, socket, message):
        self._socket = socket
        self._message = message

    # ------------------------------------------------------------

    def _run(self):

        self._set_ready()

        while True:
            # Get zmq req/rep request.
            meta, data = self.wait()

            if self._should_stop():
                break

            # Not timeout?
            if meta is not None:
                # Send last message.
                self.send(self._message["meta"], self._message["data"])

    # ------------------------------------------------------------
    def wait(self):

        meta.clear()
        data.memoryview = None

        # There is a timeout configured?
        if self.recv_timeout_milliseconds > 0:
            # Wait until timeout reached for input to arrive.
            events = self.poller.poll(self.recv_timeout_milliseconds)
            if len(events) == 0:
                return None, None

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

        return meta, data

    # ------------------------------------------------------------
    # Write response.
    def send(self, meta, data):

        # Convert meta dict into json string.
        metadata_json = json.dumps(meta)

        # logger.debug("%s writing meta %s" % (self.descriptor, metadata_json))

        try:
            # Send meta string with noblock.
            self.socket.send_string(metadata_json, (zmq.SNDMORE | zmq.NOBLOCK))
            ok_to_send_data = True

        except zmq.ZMQError as exception:
            # Errno 11 means there is no listener, which we want to tolerate.
            if exception.errno == 11:
                ok_to_send_data = False
            else:
                raise RuntimeError("%s: unable to rep data due to %s: (%d) %s" % (self.descriptor, type(exception).__name__, exception.errno, str(exception)))

        if ok_to_send_data:
            # Send data entire, this time don't block.
            # logger.debug("%s writing data length %d" % (self.descriptor, data.memoryview.nbytes))
            # TODO: See if copy=False is appropriate in pushpul writer.
            self.socket.send(data.memoryview)
