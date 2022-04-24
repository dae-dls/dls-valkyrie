import multiprocessing
import numpy
import time
import queue

# Library constants.
from dls_valkyrie_lib.valkyrie import MetaKeyword

from dls_valkyrie_lib.valkyrie import new_WriterInterface
from dls_valkyrie_lib.valkyrie import Data as ValkyrieData

import logging

logger = logging.getLogger(__name__)


class Test:

    # ----------------------------------------------------------------------------------------
    def test_07(self):
        """
        Creates process which writes 10 packets into an open websocket.
        No reader at this time.
        Verifies by incidents count.
        """
        print("")

        self.writer_configuration = {}

        self.writer_configuration["class_name"] = "dls_::valkyrie::websockets"
        self.writer_configuration["endpoint"] = "ws://*:15087"

        self.run_one()

    # ----------------------------------------------------------------------------------------
    def run_one(self):

        # Create the writer processes.
        writer_process = WriterProcess(self.writer_configuration)

        # Start the writer process.
        writer_process.start()

        # Wait for the writer process to be up.
        writer_process.wait_up()

        # Wait one second while the writer process does its thing.
        time.sleep(1.0)

        # Stop the writer process and wait for it to stop.
        writer_process.request_stop()
        writer_process.join()


# ----------------------------------------------------------------------------------------
def generate_data():
    COUNT = 3
    DTYPE = "uint32"
    data = numpy.ndarray(shape=(COUNT), dtype=numpy.dtype(DTYPE))
    for i in range(0, COUNT):
        data[i] = i + 1
    return data


# ----------------------------------------------------------------------------------------
class WriterProcess(multiprocessing.Process):
    def __init__(self, writer_configuration):
        multiprocessing.Process.__init__(self)

        self.writer_configuration = writer_configuration
        self.up_event = multiprocessing.Event()
        self.stop_event = multiprocessing.Event()

    # ----------------------------------------------------------------------------------------
    def run(self):

        writer = new_WriterInterface(self.writer_configuration)
        writer.activate()

        # Tell listeners ok to contact now.
        self.up_event.set()

        packet_sequence_number = 0

        while True:
            if self.stop_event.is_set():
                break

            meta = {}
            meta[MetaKeyword.PACKET_SEQUENCE_NUMBER] = packet_sequence_number
            timestamp = time.time()
            meta[MetaKeyword.TIMESTAMP] = timestamp

            logger.debug("writing %s" % (meta))

            packet_sequence_number = packet_sequence_number + 1

            # Make a data array and initialize with some known values.
            data = generate_data()

            # Write the data.
            writer.write(meta, ValkyrieData(data.tobytes()))

            time.sleep(0.1)

    # ----------------------------------------------------------------------------------------
    def wait_up(self):
        self.up_event.wait()

    # ----------------------------------------------------------------------------------------
    def request_stop(self):
        self.stop_event.set()
