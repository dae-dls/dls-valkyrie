from multiprocessing.pool import RUN
import zmq
import json
import base64

import logging

logger = logging.getLogger(__name__)


class TrackedBuffer:
    """
    Object which keeps a zmq MessageTracker along with reference to the data being tracked.
    """

    def __init__(self, zmq_tracker, data):
        self.zmq_tracker = zmq_tracker
        self.data = data


class Tracker:
    """
    Object which tracks data sent with nocopy.
    """

    # ------------------------------------------------------------------------------------
    def __init__(self):
        self._list = []

    # ------------------------------------------------------------------------------------
    def release_done_messages(self):
        """
        Release all done messages.
        """
        if len(self._list) == 0:
            return

        keep_list = []
        for tracked_buffer in self._list:
            if not tracked_buffer.zmq_tracker.done:
                keep_list.append(tracked_buffer)

        # logger.critical("%s released %d, remaining %d" % (self.descriptor, len(self._list)-len(keep_list), len(self._list)))
        self._list = keep_list

        return len(self._list)

    # ------------------------------------------------------------------------------------
    def wait_all_messages_done(self):
        """
        Wait for all messages to be done.
        """
        # logger.critical("%s %d to wait and release" % (self.descriptor, len(self._list)))

        for tracked_buffer in self._list:
            tracked_buffer.zmq_tracker.wait()

        self._list = []

    # ------------------------------------------------------------------------------------
    def add_message(self, zmq_tracker, data):
        """
        Add message to be tracked.
        """
        if zmq_tracker is None:
            return

        self._list.append(TrackedBuffer(zmq_tracker, data))


# ------------------------------------------------------------------------------------
class Writer:
    def __init__(self, configuration):
        self.configuration = configuration
        self.send_timeout_milliseconds = int(
            configuration.get("send_timeout_milliseconds", 0)
        )

        self.context = None
        self.socket = None
        self.poller = None
        self.is_activated = False
        self._should_copy = self.configuration.get("should_copy", True)
        self._should_block = self.configuration.get("should_block", True)

        self.descriptor = "zmq pushpull server to " + configuration["endpoint"]

        # Object which tracks data sent with nocopy.
        self._tracker = Tracker()

        try:
            # Get configured high water mark.
            # This is how much to keep in the send buffer.
            # Recommend low, even 1 should be ok unless a slow reader.
            self._high_water_mark = int(configuration.get("high_water_mark", 10))
        except Exception as exception:
            raise RuntimeError(
                "%s unable to get high_water_mark from configuration"
                % (self.descriptor)
            )

    # ----------------------------------------------------------------
    def __del__(self):
        # Wait for tracked messages to flush.
        self._tracker.wait_all_messages_done()

        if self.socket is not None:
            if self.poller is not None:
                self.poller.register(self.socket, 0)

            rc = self.socket.close()
            logger.info("%s closed socket, rc %s" % (self.descriptor, str(rc)))

        if self.context is not None:
            rc = self.context.destroy()
            logger.info("%s destroyed context, rc %s" % (self.descriptor, str(rc)))

    # ------------------------------------------------------------
    # Activate the server.  Gives already-waiting clients a chance to connect.
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

            logger.info(
                "%s binding with send_timeout_milliseconds %d, high_water_mark %d, copy=%s, block=%s"
                % (
                    self.descriptor,
                    self.send_timeout_milliseconds,
                    self._high_water_mark,
                    self._should_copy,
                    self._should_block,
                )
            )

            self.socket.bind(endpoint)

            # Release port as soon as it is closed.
            self.socket.setsockopt(zmq.LINGER, 0)

            self.poller = zmq.Poller()
            self.poller.register(self.socket, zmq.POLLOUT)

            self.is_activated = True

    # ------------------------------------------------------------
    def write(self, meta, data):
        if self._should_block:
            self.__write_blocking(meta, data)
        else:
            self.__write_nonblocking(meta, data)

    # ------------------------------------------------------------
    def __write_blocking(self, meta, data):

        if not self.is_activated:
            self.activate()

        # Let the tracker release former messages.
        self._tracker.release_done_messages()

        # There is a timeout configured?
        if self.send_timeout_milliseconds > 0:
            # Wait until timeout reached for input to arrive.
            events = self.poller.poll(self.send_timeout_milliseconds)
            if len(events) == 0:
                raise RuntimeError(
                    "%s unable to write data within timeout %s seconds"
                    % (self.descriptor, self.send_timeout_milliseconds)
                )

        # Convert meta dict into json string.
        metadata_json = json.dumps(meta)

        # logger.debug("%s writing meta %s" % (self.descriptor, metadata_json))

        self.socket.send_string(metadata_json, zmq.SNDMORE)

        if self._should_copy:
            zmq_tracker = self.socket.send(data.memoryview, copy=False, track=True)
            self._tracker.add_message(zmq_tracker, data.memoryview)
        else:
            self.socket.send(data.memoryview)

    # ------------------------------------------------------------
    def __write_nonblocking(self, meta, data):

        if not self.is_activated:
            self.activate()

        # Let the tracker release former messages.
        self._tracker.release_done_messages()

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
                raise RuntimeError(
                    "%s: unable to push data due to %s: (%d) %s"
                    % (
                        self.descriptor,
                        type(exception).__name__,
                        exception.errno,
                        str(exception),
                    )
                )

        if ok_to_send_data:
            # Send data entire, this time don't block.
            # logger.debug("%s writing data length %d" % (self.descriptor, data.memoryview.nbytes))
            # TODO: See if copy=False is appropriate in pushpull writer.

            if self._should_copy:
                zmq_tracker = self.socket.send(data.memoryview, copy=False, track=True)
                self._tracker.add_message(zmq_tracker, data.memoryview)
            else:
                self.socket.send(data.memoryview)
