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
COUNT = 1000000
DTYPE = "uint8"


class Test:

    # ----------------------------------------------------------------------------------------
    def test_03_pubsub(self):
        """
        Run the test.
        """

        self.writer_configuration = {}
        self.reader_configuration = {}

        self.writer_configuration["class_name"] = "dls_::valkyrie::zmq_pubsub"
        self.writer_configuration["endpoint"] = "tcp://*:15003"

        self.reader_configuration["class_name"] = "dls_::valkyrie::zmq_pubsub"
        self.reader_configuration["endpoint"] = "tcp://localhost:15003"
        self.reader_configuration["recv_timeout_milliseconds"] = "500"

        self.run_one()

    # ----------------------------------------------------------------------------------------
    def run_one(self):

        writer_thread = WriterThread(self.writer_configuration)
        writer_thread.start()

        reader_thread = ReaderThread(self.reader_configuration)
        reader_thread.start()

        writer_thread.join()
        reader_thread.join()

        # The actual packets we get is indeterminate.
        # We just want less than those sent so we know some got dropped.
        assert reader_thread.read_packet_count > 0
        assert reader_thread.read_packet_count < writer_thread.write_packet_count

        # Check final data contents.
        assert writer_thread.numpy_array.all() == reader_thread.numpy_array.all()


# ----------------------------------------------------------------------------------------
class WriterThread(threading.Thread):
    def __init__(self, writer_configuration):
        threading.Thread.__init__(self)
        self.writer_configuration = writer_configuration
        self.write_packet_count = 0

    # ----------------------------------------------------------------------------------------
    def run(self):

        writer = new_WriterInterface(self.writer_configuration)
        writer.activate()
        time.sleep(0.05)

        meta = {}

        # Make a data array and initialize with some known values.
        self.numpy_array = numpy.ndarray(shape=(COUNT), dtype=numpy.dtype(DTYPE))
        for i in range(0, COUNT):
            self.numpy_array[i] = i + 1

        # logger.debug("writing %s" % (binascii.hexlify(numpy_array.tobytes())))

        for loop in range(0, 100):
            meta[ValkyrieMetaKeyword.PACKET_SEQUENCE_NUMBER] = "%d" % (loop)
            writer.write(meta, ValkyrieData(self.numpy_array.tobytes()))
            self.write_packet_count = self.write_packet_count + 1


# ----------------------------------------------------------------------------------------
class ReaderThread(threading.Thread):
    def __init__(self, reader_configuration):
        threading.Thread.__init__(self)
        self.reader_configuration = reader_configuration
        self.read_packet_count = 0

    # ----------------------------------------------------------------------------------------
    def run(self):

        reader = new_ReaderInterface(self.reader_configuration)
        reader.activate()

        meta = {}
        data = ValkyrieData()
        reader.read(meta, data)
        # No more messages in the queue?
        # if data.memoryview is None:
        #     pass
        self.read_packet_count = self.read_packet_count + 1
        logger.debug(
            "read number %d got packet sequence number %s"
            % (self.read_packet_count, meta[ValkyrieMetaKeyword.PACKET_SEQUENCE_NUMBER])
        )

        # Convert the data raw bytes to numpy array.
        self.numpy_array = numpy.ndarray(
            shape=(COUNT), dtype=numpy.dtype(DTYPE), buffer=data.memoryview
        )
