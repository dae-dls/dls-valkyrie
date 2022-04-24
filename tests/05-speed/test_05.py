import threading
import numpy
import time

from dls_valkyrie_lib.valkyrie import new_WriterInterface
from dls_valkyrie_lib.valkyrie import new_ReaderInterface
from dls_valkyrie_lib.valkyrie import Data as ValkyrieData
from dls_valkyrie_lib.valkyrie import MetaKeyword as ValkyrieMetaKeyword

import logging

logger = logging.getLogger(__name__)

# Use biggish packet size to make unread packets disappear faster.
COUNT = 10000000
DTYPE = "uint8"


class Test:

    # ----------------------------------------------------------------------------------------
    def test_05(self):
        """
        Run the test.
        """

        self.writer_configuration = {}
        self.reader_configuration = {}

        self.writer_configuration["class_name"] = "dls_::valkyrie::zmq_pubsub"
        self.writer_configuration["endpoint"] = "tcp://*:15005"

        self.reader_configuration["class_name"] = "dls_::valkyrie::zmq_pubsub"
        self.reader_configuration["endpoint"] = "tcp://localhost:15005"
        self.reader_configuration["recv_timeout_milliseconds"] = "100"

        self.run_one()

    # ----------------------------------------------------------------------------------------
    def run_one(self):
        writer = new_WriterInterface(self.writer_configuration)
        writer.activate()

        reader = new_ReaderInterface(self.reader_configuration)
        reader.activate()

        # Give the reader thread a chance to get acquainted.
        time.sleep(0.5)

        writer_lock = threading.Lock()

        writer_thread = WriterThread(writer, writer_lock)
        writer_thread.start()

        # Wait for writer to publish its first packet.
        writer_lock.acquire()

        reader_thread = ReaderThread(reader)
        reader_thread.start()

        writer_thread.join()
        reader_thread.join()

        # Emit timing summaries to the INFO stream.
        # self.info_timing()

        # The actual packets we get is indeterminate.  We just want less than those sent so we know some got dropped.
        assert reader_thread.read_packet_count > 0
        assert reader_thread.read_packet_count < writer_thread.write_packet_count

        # Check final data contents.
        assert writer_thread.numpy_array.all() == reader_thread.numpy_array.all()


# ----------------------------------------------------------------------------------------
class WriterThread(threading.Thread):
    def __init__(self, writer, writer_lock):
        threading.Thread.__init__(self)
        self.writer = writer
        self.write_packet_count = 0
        self.writer_lock = writer_lock
        self.writer_lock.acquire()

    # ----------------------------------------------------------------------------------------
    def run(self):

        meta = {}

        # Make a data array and initialize with some known values.
        self.numpy_array = numpy.ndarray(shape=(COUNT), dtype=numpy.dtype(DTYPE))
        for i in range(0, COUNT):
            self.numpy_array[i] = i + 1

        # Wrap a data object around the numby bytes.
        data = ValkyrieData(self.numpy_array.tobytes())

        # Write a bunch of packets as fast as possible.
        for loop in range(0, 1000):
            meta[ValkyrieMetaKeyword.PACKET_SEQUENCE_NUMBER] = "%d" % (loop)
            self.writer.write(meta, data)
            self.write_packet_count = self.write_packet_count + 1
            if loop == 0:
                # Release the lock after first data is on the wire.
                # This will make sure the reader has a zero-wait time for its first read.
                self.writer_lock.release()


# ----------------------------------------------------------------------------------------
class ReaderThread(threading.Thread):
    def __init__(self, reader):
        threading.Thread.__init__(self)
        self.reader = reader
        self.read_packet_count = 0

    # ----------------------------------------------------------------------------------------
    def run(self):

        meta = {}
        data = ValkyrieData()
        last = None
        while True:
            self.reader.read(meta, data)
            # No more messages in the queue?
            if data.memoryview is None:
                break

            # Remember the last data we got.
            last = ValkyrieData(data.memoryview)

            self.read_packet_count = self.read_packet_count + 1

            # self.log_debug("read number %d got packet sequence number %s" % (self.read_packet_count, meta[ValkyrieMetaKeyword.PACKET_SEQUENCE_NUMBER]))

        # We got any data?
        if last is not None:
            # Convert the data raw bytes to numpy array.
            self.numpy_array = numpy.ndarray(
                shape=(COUNT), dtype=numpy.dtype(DTYPE), buffer=last.memoryview
            )
