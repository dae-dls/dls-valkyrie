import time

from dls_valkyrie_lib.valkyrie import new_WriterInterface
from dls_valkyrie_lib.valkyrie import new_ReaderInterface
from dls_valkyrie_lib.valkyrie import Data as ValkyrieData

import logging

logger = logging.getLogger(__name__)

# Use biggish packet size to make unread packets disappear faster.
COUNT = 1000000
DTYPE = "uint8"


class Test:

    # ----------------------------------------------------------------------------------------
    def test_04_pubsub(self):
        """
        Run the test.
        """

        self.writer_configuration = {}
        self.reader_configuration = {}

        self.writer_configuration["class_name"] = "dls_::valkyrie::zmq_pubsub"
        self.writer_configuration["endpoint"] = "tcp://*:15004"

        self.reader_configuration["class_name"] = "dls_::valkyrie::zmq_pubsub"
        self.reader_configuration["endpoint"] = "tcp://localhost:15004"

        self.run_one()

    # ----------------------------------------------------------------------------------------
    def test_04_pushpull(self):
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
    def run_one(self):

        writer = new_WriterInterface(self.writer_configuration)
        writer.activate()

        reader = new_ReaderInterface(self.reader_configuration)
        reader.activate()

        time.sleep(0.1)

        meta = {}
        writer.write(meta, ValkyrieData(bytearray(0)))

        meta = {}
        data = ValkyrieData()
        reader.read(meta, data)

        # Check data contents.
        assert data.memoryview.nbytes == 0
