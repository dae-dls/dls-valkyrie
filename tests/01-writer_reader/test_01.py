import threading
import numpy
import time

from dls_valkyrie_lib.valkyrie import new_WriterInterface
from dls_valkyrie_lib.valkyrie import new_ReaderInterface
from dls_valkyrie_lib.valkyrie import Data as ValkyrieData

import logging

logger = logging.getLogger(__name__)

COUNT = 3
DTYPE = "uint32"


class Test:

    # ----------------------------------------------------------------------------------------
    def test_01_pubsub(self, logging_setup):
        """
        Run the test.
        """

        self.writer_configuration = {}
        self.reader_configuration = {}

        self.writer_configuration["class_name"] = "dls_::valkyrie::zmq_pubsub"
        self.writer_configuration["endpoint"] = "tcp://*:14001"

        self.reader_configuration["class_name"] = "dls_::valkyrie::zmq_pubsub"
        self.reader_configuration["endpoint"] = "tcp://localhost:14001"

        self.run_one()

    # ----------------------------------------------------------------------------------------
    def test_01_pushpull(self, logging_setup):
        """
        Run the test.
        """

        self.writer_configuration = {}
        self.reader_configuration = {}

        self.writer_configuration["class_name"] = "dls_::valkyrie::zmq_pushpull"
        self.writer_configuration["endpoint"] = "tcp://*:15001"

        self.reader_configuration["class_name"] = "dls_::valkyrie::zmq_pushpull"
        self.reader_configuration["endpoint"] = "tcp://localhost:15001"

        self.run_one()

    # ----------------------------------------------------------------------------------------
    def test_01_pullpush(self, logging_setup):
        """
        Run the test.
        """

        self.writer_configuration = {}
        self.reader_configuration = {}

        self.writer_configuration["class_name"] = "dls_::valkyrie::zmq_pullpush"
        self.writer_configuration["endpoint"] = "tcp://localhost:16001"

        self.reader_configuration["class_name"] = "dls_::valkyrie::zmq_pullpush"
        self.reader_configuration["endpoint"] = "tcp://*:16001"

        self.run_one()

    # ----------------------------------------------------------------------------------------
    def run_one(self):

        reader_thread = ReaderThread(self.reader_configuration)
        reader_thread.start()
        reader_thread.wait_up()

        writer_thread = WriterThread(self.writer_configuration)
        writer_thread.start()

        time.sleep(1.0)

        logger.info("waiting for writer to join...")
        writer_thread.join()
        logger.info("waiting for reader to join...")
        reader_thread.join()

        # Verify the meta contents.
        assert reader_thread.meta["some"] == "thing"

        # Verify the data contents.
        for i in range(0, reader_thread.numpy_array.shape[0]):
            assert reader_thread.numpy_array[i] == i + 1, "element %d got 0x%08x" % (
                i,
                reader_thread.numpy_array[i],
            )


# ----------------------------------------------------------------------------------------
class WriterThread(threading.Thread):
    def __init__(self, writer_configuration):
        threading.Thread.__init__(self)
        self.writer_configuration = writer_configuration

    # ----------------------------------------------------------------------------------------
    def run(self):

        writer = new_WriterInterface(self.writer_configuration)
        writer.activate()

        # Let the reader get acquainted so they don't miss the first packet.
        time.sleep(0.5)

        for i in range(0, 10):
            meta = {}
            meta["message_sequence_number"] = i
            meta["some"] = "thing"

            # Make a data array and initialize with some known values.
            numpy_array = numpy.ndarray(shape=(COUNT), dtype=numpy.dtype(DTYPE))
            for i in range(0, COUNT):
                numpy_array[i] = i + 1

            # logger.debug("writing %s" % (binascii.hexlify(numpy_array.tobytes())))

            # Write the data.
            writer.write(meta, ValkyrieData(numpy_array.tobytes()))

            #logger.debug("wrote %d" % (meta["message_sequence_number"]))

        logger.debug("writer thread finished")


# ----------------------------------------------------------------------------------------
class ReaderThread(threading.Thread):
    def __init__(self, reader_configuration):
        threading.Thread.__init__(self)
        self.reader_configuration = reader_configuration

        self.up_event = threading.Event()

    # ----------------------------------------------------------------------------------------
    def run(self):

        reader = new_ReaderInterface(self.reader_configuration)
        reader.activate()

        # Let the caller know we are listening.
        self.up_event.set()

        for i in range(0, 10):
            # Read the meta and the data.
            self.meta = {}
            data = ValkyrieData()
            reader.read(self.meta, data)

            # logger.debug("read %d" % (self.meta["message_sequence_number"]))
            # logger.debug("read %s" % (binascii.hexlify(data.memoryview)))

            # Convert the data raw bytes to numpy array.
            self.numpy_array = numpy.ndarray(
                shape=(COUNT), dtype=numpy.dtype(DTYPE), buffer=data.memoryview
            )

        logger.debug("reader thread finished")

    # ----------------------------------------------------------------------------------------
    def wait_up(self):
        self.up_event.wait()
        # TODO: Why is this needed in gitlab test environments?
        time.sleep(1.0)
