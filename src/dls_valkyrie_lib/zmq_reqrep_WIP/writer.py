import zmq

from dls_valkyrie_lib.zmq_reqrep.writer_thread import WriterThread
import logging

logger = logging.getLogger(__name__)


class Writer:
    def __init__(self, configuration):
        self.configuration = configuration
        self.context = None
        self.socket = None
        self.is_activated = False
        self.descriptor = "server to " + configuration["endpoint"]

        self._thread_message = {}
        self._writer_thread = None

    # ----------------------------------------------------------------
    def __del__(self):

        if self._writer_thread is not None:
            # Stop and join writer thread.
            self._writer_thread.stop()
            self._writer_thread.wait_stopped(timeout=1.0)

        if self.socket is not None:
            rc = self.socket.close()
            logger.debug("%s closed socket" % (self.descriptor))

        if self.context is not None:
            rc = self.context.destroy()
            logger.debug("%s destroyed context rc %s" % (self.descriptor, str(rc)))

    # ------------------------------------------------------------
    # Activate the server.  Gives already-waiting clients a chance to connect.
    def activate(self):

        if self.context is None:
            # Create zmq context.
            self.context = zmq.Context()
            # Create a zmq socket.
            self.socket = self.context.socket(zmq.REP)

        # Not already activated?
        if not self.is_activated:
            endpoint = self.configuration["endpoint"]

            logger.debug("%s binding" % (self.descriptor))

            self.socket.bind(endpoint)

            # Create and start the writer thread.
            # Listens for requests and responds with latest (meta, data).
            self._writer_thread = WriterThread(self.socket, self._thread_message)
            self._writer_thread.start()

            self.is_activated = True

    # ------------------------------------------------------------
    # Write response.
    def write(self, meta, data):

        # Save the meta and data to be sent as response to next request by reader.
        self._thread_message["meta"] = meta
        self._thread_message["data"] = data
