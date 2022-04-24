import time

from dls_valkyrie_lib.valkyrie import new_WriterInterface
from dls_valkyrie_lib.valkyrie import MetaKeyword
from exercises.base import Base

import logging

logger = logging.getLogger(__name__)


class Exerciser(Base):

    # -----------------------------------------------------------------
    def send_in_loop(self, writer):

        packet_sequence_number = 0
        loops = 2
        for loop in range(0, loops):
            logger.debug("loop %d" % (loop))

            meta = {}
            meta[MetaKeyword.PACKET_SEQUENCE_NUMBER] = packet_sequence_number
            packet_sequence_number = packet_sequence_number + 1

            meta[MetaKeyword.TIMESTAMP] = time.time()

            data = bytearray(10)

            writer.write(meta, data)

            if loop < loops - 1:
                time.sleep(1.0)

        logger.debug("exiting send_in_loop")

    # -----------------------------------------------------------------
    def run(self):
        """
        Run the exercise.
        """

        logger.debug("starting")

        try:
            configuration = {}
            configuration["class_name"] = "dls_::valkyrie::websockets"
            configuration["endpoint"] = "ws://*:15081"
            writer = new_WriterInterface(self.runtime, configuration)
            writer.activate()
            self.send_in_loop(writer)

        except KeyboardInterrupt:
            self.runtime.exit_due_to_interrupt()

        except Exception as exception:
            self.runtime.exit_due_to_exception(
                "unexpected exception: %s" % (exception), exception
            )

        logger.debug("exited try")


"""
Run the exercise class.
"""
exerciser = Exerciser()
exerciser.run()
