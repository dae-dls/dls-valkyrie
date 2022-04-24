import multiprocessing
import numpy
import time
import queue

from dls_valkyrie_lib.valkyrie import new_WriterInterface
from dls_valkyrie_lib.valkyrie import new_ReaderInterface
from dls_valkyrie_lib.valkyrie import Data as ValkyrieData

import logging

logger = logging.getLogger(__name__)

COUNT = 3
DTYPE = "uint32"


class Test:

    # ----------------------------------------------------------------------------------------
    def test_06_pullpush(self):
        """
        Run the test.
        """

        self.writer_configuration = {}
        self.reader_configuration = {}

        self.writer_configuration["class_name"] = "dls_::valkyrie::zmq_pullpush"
        self.writer_configuration["endpoint"] = "tcp://localhost:15006"

        self.reader_configuration["class_name"] = "dls_::valkyrie::zmq_pullpush"
        self.reader_configuration["endpoint"] = "tcp://*:15006"
        self.reader_configuration["recv_timeout_milliseconds"] = 500

        self.run_one()

    # ----------------------------------------------------------------------------------------
    def run_one(self):

        received_queue = multiprocessing.Queue()

        reader_process = ReaderProcess(self.reader_configuration, received_queue)
        reader_process.start()
        reader_process.wait_up()

        writer_count = 20
        writer_processes = []

        # Create all the writer processes.
        for i in range(0, writer_count):
            writer_processes.append(
                WriterProcess(self.writer_configuration, "writer%d" % (i))
            )

        # Start all the writer processes.
        for writer_process in writer_processes:
            writer_process.start()

        # Wait for all the writer processes.
        for writer_process in writer_processes:
            writer_process.join()

        # Stop the reader and wait for it to stop.
        reader_process.stop()
        reader_process.join()

        # Make a data array and initialize with some known values.
        expect_data = generate_data()

        # Check results.
        message_count = 0
        while True:
            try:
                meta, data = received_queue.get_nowait()
                message_count += 1
                assert numpy.array_equal(expect_data, data)
                logger.debug("%s" % (meta.get("writer_name")))
            except queue.Empty:
                break

        assert writer_count == message_count


# ----------------------------------------------------------------------------------------
def generate_data():
    data = numpy.ndarray(shape=(COUNT), dtype=numpy.dtype(DTYPE))
    for i in range(0, COUNT):
        data[i] = i + 1
    return data


# ----------------------------------------------------------------------------------------
class WriterProcess(multiprocessing.Process):
    def __init__(self, writer_configuration, writer_name):
        multiprocessing.Process.__init__(self)
        self.writer_configuration = writer_configuration
        self.writer_name = writer_name

    # ----------------------------------------------------------------------------------------
    def run(self):

        writer = new_WriterInterface(self.writer_configuration)
        writer.activate()

        # Let the reader get acquainted so it does not miss the first packet.
        time.sleep(0.5)

        meta = {}
        meta["writer_name"] = self.writer_name

        # Make a data array and initialize with some known values.
        data = generate_data()

        # logger.debug("writing %s" % (binascii.hexlify(numpy_array.tobytes())))

        # Write the data.
        writer.write(meta, ValkyrieData(data.tobytes()))


# ----------------------------------------------------------------------------------------
class ReaderProcess(multiprocessing.Process):
    def __init__(self, reader_configuration, received_queue):
        multiprocessing.Process.__init__(self)
        self.reader_configuration = reader_configuration
        self.received_queue = received_queue

        self.up_event = multiprocessing.Event()
        self.stop_event = multiprocessing.Event()

    # ----------------------------------------------------------------------------------------
    def run(self):

        reader = new_ReaderInterface(self.reader_configuration)
        reader.activate()

        # Let the caller know we are listening.
        self.up_event.set()

        while True:
            if self.stop_event.is_set():
                break

            # Read the meta and the data.
            meta = {}
            data = ValkyrieData()
            reader.read(meta, data)

            # Timeout?
            if data.memoryview is None:
                continue

            # Convert the data raw bytes to numpy array.
            data = numpy.ndarray(
                shape=(COUNT), dtype=numpy.dtype(DTYPE), buffer=data.memoryview
            )

            self.received_queue.put((meta, data))

        logger.debug("reader thread finished")

    # ----------------------------------------------------------------------------------------
    def wait_up(self):
        self.up_event.wait()

    # ----------------------------------------------------------------------------------------
    def stop(self):
        self.stop_event.set()
