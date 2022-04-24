import numpy

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
    def test_02_pubsub(self):
        """
        Run the test.
        """

        self.writer_configuration = {}
        self.reader_configuration = {}

        self.writer_configuration["class_name"] = "dls_::valkyrie::zmq_pubsub"
        self.writer_configuration["endpoint"] = "tcp://*:15002"

        self.reader_configuration["class_name"] = "dls_::valkyrie::zmq_pubsub"
        self.reader_configuration["endpoint"] = "tcp://localhost:15002"
        self.reader_configuration["recv_timeout_milliseconds"] = "100"

        self.run_one()

    # ----------------------------------------------------------------------------------------
    def run_one(self):

        writer = new_WriterInterface(self.writer_configuration)
        writer.activate()

        reader = new_ReaderInterface(self.reader_configuration)
        reader.activate()

        meta = {}

        # Make a data array and initialize with some known values.
        write_numpy_array = numpy.ndarray(shape=(COUNT), dtype=numpy.dtype(DTYPE))
        for i in range(0, COUNT):
            write_numpy_array[i] = i + 1

        write_packet_count = 100

        # Write a few packets into the queue.
        for loop in range(0, write_packet_count):
            meta[ValkyrieMetaKeyword.PACKET_SEQUENCE_NUMBER] = "%d" % (loop)
            writer.write(meta, ValkyrieData(write_numpy_array.tobytes()))

        meta = {}
        data = ValkyrieData()
        read_packet_count = 0

        # Read back all the packets that are available.
        while True:
            reader.read(meta, data)
            # No more messages in the queue?
            if data.memoryview is None:
                break
            read_packet_count = read_packet_count + 1
            logger.debug(
                "read number %d got packet sequence number %s"
                % (read_packet_count, meta[ValkyrieMetaKeyword.PACKET_SEQUENCE_NUMBER])
            )
            # Convert the data raw bytes to numpy array.
            read_numpy_array = numpy.ndarray(
                shape=(COUNT), dtype=numpy.dtype(DTYPE), buffer=data.memoryview
            )

            # Check data contents.
            assert write_numpy_array.all() == read_numpy_array.all()

        # The actual packets we get is indeterminate.  We just want less than those sent so we know some got dropped.
        assert read_packet_count > 0
        assert read_packet_count < write_packet_count
