import threading
import asyncio
import websockets
import json

import logging

logger = logging.getLogger(__name__)


class Message:
    def __init__(self):
        self.meta = None
        self.data = None


# connect() and serve()
# max_size 1 MiB
# max_queue 32
# read_limit 64 KiB
# write_limit 64 KiB

# serve max_size=2 ** 20, max_queue=2 ** 5, read_limit=2 ** 16, write_limit=2 ** 16
# connect max_size = 2 ** 20, max_queue = 2 ** 5, read_limit = 2 ** 16, write_limit = 2 ** 16

# MAX_QUEUE = 1
# WRITE_LIMIT = 1


class Writer:
    def __init__(self, configuration):
        self.configuration = configuration
        self.event_loop = None
        self.is_activated = False

        self.endpoint = self.configuration.get("endpoint")
        if self.endpoint is None:
            raise RuntimeError("no endpoint in Writer configuration")

        parts = self.endpoint.split(":")

        if len(parts) == 0:
            raise RuntimeError("no colon in Writer endpoint %s" % self.endpoint)
        if len(parts) != 3:
            raise RuntimeError(
                "too many colons (%d) in Writer endpoint %s"
                % (len(parts) - 1, self.endpoint)
            )

        self.host = parts[0] + ":" + parts[1]
        self.port = int(parts[2])

        if not self.host.startswith("ws://"):
            raise RuntimeError("invalid protocol in Writer endpoint %s" % self.endpoint)

        self.host = self.host[5:]

        # Highwater mark for outgoing queue.
        self.high_water_mark = self.configuration.get("high_water_mark")
        if self.high_water_mark is not None:
            self.high_water_mark = self.configuration.get("highwater")

        # Default is zero backlog.
        if self.high_water_mark is None or not isinstance(self.high_water_mark, int):
            self.high_water_mark = 0

        self.descriptor = "server to " + configuration["endpoint"]

    # ------------------------------------------------------------
    # Activate the server.  Gives already-waiting clients a chance to connect.
    def activate(self):

        # Not already activated?
        if not self.is_activated:

            logger.info(
                "%s binding with high_water_mark %s" % (self.descriptor, str(self.high_water_mark))
            )

            self.event_loop = None
            self.websocket_serial_number = 0
            self.message_queue_dict = {}

            self.thread = threading.Thread(target=self.event_looper)
            self.thread.daemon = True
            self.thread.start()

            self.is_activated = True

    # ------------------------------------------------------------
    def write(self, meta, data):

        """
        API method to send a message to all subscribing clients.
        """

        if not self.is_activated:
            self.activate()

        message = Message()
        message.meta = json.dumps(meta)
        message.data = data

        if self.event_loop is not None:
            # logger.debug("now calling soon %d bytes" % (data.memoryview.nbytes))

            self.event_loop.call_soon_threadsafe(self.__send_threadsafe, message)

    # -----------------------------------------------------------------
    def event_looper(self):
        """
        Run the websocket asyncio event_loop in its own thread.
        """

        logger.info("%s websocket thread starting" % (self.descriptor))

        # Need our own asyncio event_loop since we are in a thread.
        self.event_loop = asyncio.new_event_loop()

        start_server = websockets.serve(
            self.__triggered_send,
            self.host,
            self.port,
            loop=self.event_loop,
            # max_queue=MAX_QUEUE, write_limit=WRITE_LIMIT
        )
        logger.debug("bound on %s:%d" % (self.host, self.port))

        self.event_loop.run_until_complete(start_server)

        self.event_loop.run_forever()

        logger.info("%s websocket thread ending" % (self.descriptor))

    # -----------------------------------------------------------------
    async def __triggered_send(self, websocket, path):
        """
        Coroutine called by websockets server when a new connection is initiated by a client.
        """

        # Make a unique descriptor for this connection.
        self.websocket_serial_number = self.websocket_serial_number + 1
        websocket_descriptor = "websocket #%d" % self.websocket_serial_number

        logger.debug("%s starting client connection" % (websocket_descriptor))

        # Make a queue for this webscocket's outgoing messages.
        message_queue = asyncio.Queue()

        # Add our queue to the list of queues which should receive notification of new messages.
        self.message_queue_dict[websocket_descriptor] = message_queue

        while True:
            # Wait for our queue to have something in it.
            message = await message_queue.get()

            try:
                # Send meta frame on the websocket.
                await websocket.send(message.meta)
                # Send data frame on the websocket.
                await websocket.send(message.data.memoryview)
            except websockets.exceptions.ConnectionClosedError:
                logger.debug("%s connection closed" % (websocket_descriptor))
                break
            except websockets.exceptions.ConnectionClosedOK:
                logger.debug("%s connection closed" % (websocket_descriptor))
                break

            # logger.debug("%s sent message %s" % (websocket_descriptor, message.meta))

        self.message_queue_dict[websocket_descriptor] = None

    # -----------------------------------------------------------------
    # Private method
    def __send_threadsafe(self, message):
        """
        Add the message to all the subscriber queues.
        """

        websocket_descriptors = list(self.message_queue_dict.keys())

        # if logger.isEnabledFor(logging.DEBUG):
        #     logger.debug(
        #         "sending threadsafe %d bytes to %d clients"
        #         % (message.data.memoryview.nbytes, len(websocket_descriptors))
        #     )

        is_enabled_for_debug = logger.isEnabledFor(logging.DEBUG)

        for websocket_descriptor in websocket_descriptors:
            message_queue = self.message_queue_dict[websocket_descriptor]
            if message_queue is None:
                del self.message_queue_dict[websocket_descriptor]
            else:
                dump_count = 0

                # Trim queue size to high_water_mark mark.
                while message_queue.qsize() > self.high_water_mark:
                    message_queue.get_nowait()
                    dump_count += 1

                message_queue.put_nowait(message)

                if is_enabled_for_debug:
                    logger.debug(
                        "%s after dumping %d, enqueued message with meta length %d and data length %d"
                        % (
                            websocket_descriptor,
                            dump_count,
                            len(message.meta),
                            message.data.memoryview.nbytes,
                        )
                    )
