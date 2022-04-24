import threading

from dls_valkyrie_lib.valkyrie import new_WriterInterface
from dls_valkyrie_lib.valkyrie import new_ReaderInterface
from dls_valkyrie_lib.valkyrie import Data as ValkyrieData

from lib_dls_protocolj.protocolj import new_ServerInterface

from exercises.base import Base

import logging

logger = logging.getLogger(__name__)


class Keywords:
    COMMAND = "Keywords::COMMAND"
    STATE = "Keywords::STATE"
    ERROR = "Keywords::ERROR"
    CONFIRMATION = "Keywords::CONFIRMATION"
    INCIDENT_SUMMARIES = "Keywords::INCIDENT_SUMMARIES"


class Commands:
    STOP = "Commands::STOP"
    EXIT = "Commands::EXIT"
    GET_STATE = "Commands::GET_STATE"
    GET_INCIDENT_SUMMARIES = "Commands::GET_INCIDENT_SUMMARIES"


class Main(Base):
    def __init__(self):
        super().__init__()
        self.ok_to_continue = True

    # -----------------------------------------------------------------
    def run(self):

        try:
            # Start the ProtocolJ control servers per configuration.
            self.start_controls()

            # Instantiate a reader and a writer.
            writer = new_WriterInterface(self.runtime, self.runtime.get("writer"))
            reader = new_ReaderInterface(self.runtime, self.runtime.get("reader"))

            # Loop until some other thread says not to continue.
            while self.ok_to_continue:
                # Wrap this section in a instrumentation metric.
                with self.runtime.with_timing("cycle") as with_timing:
                    meta = {}
                    data = ValkyrieData()

                    logger.debug("reading")
                    # Read from the source.
                    reader.read(meta, data)

                    # Write to the destination.
                    writer.write(meta, data)

                    logger.debug("writing done, now looping")

                    # For this loop, tell the instrumentation how many bytes we did.
                    with_timing.incident.volume = data.memoryview.nbytes

        except KeyboardInterrupt:
            self.runtime.exit_due_to_interrupt()

        except Exception as exception:
            self.runtime.exit_due_to_exception(
                "unexpected exception: %s" % (exception), exception
            )

    # -----------------------------------------------------------------

    def start_controls(self):
        """
        Configure all ProtocolJ control servers and start them running.
        The configuration may specify several ProtocolJ servers if different protocols are wanted.
        """

        # All the controls are configured in one place in the runtime configuration.
        controls = self.runtime.get("controls")

        for i in range(0, 10):
            control_configuration = controls.get("control%d" % i)
            if control_configuration is not None:
                self.start_control(control_configuration)

    # -----------------------------------------------------------------

    def start_control(self, control_configuration):
        """
        Configure a ProtocolJ control server and start it running in a new thread.
        """

        # Make a new thread for this ProtocolJ server.
        server_thread = ProtcolJServerThread(self.runtime, self, control_configuration)
        server_thread.start()

    # ----------------------------------------------------------------

    def dispatch(self, request, response):
        """
        Callback from within ProtocolJ server.loop when it gets a POST.
        Request and response are both dictionaries, serializable to json.
        """

        command = request.get(Keywords.COMMAND, "*unset*")

        error = ""
        if command == Commands.GET_INCIDENT_SUMMARIES:
            response["confirmation"] = "ok"
            summaries = self.runtime.timing_incidents.make_summaries()

            response[Keywords.INCIDENT_SUMMARIES] = summaries
        elif command == Commands.EXIT:
            response["confirmation"] = "ok, quitting"
            self.ok_to_continue = False
        else:
            error = 'invalid command "%s"' % (command)

        # Always return the state in the response.
        response[Keywords.STATE] = "ACTIVE"

        # Only return error keyword in the response if there was an error.
        if error != "":
            self.error(error)
            response[Keywords.ERROR] = error

        # logger.debug("returning %s" % (str(self.ok_to_continue)))
        return self.ok_to_continue


# ----------------------------------------------------------------------------------------
class ProtcolJServerThread(threading.Thread):
    """
    Thread run method, starts a ProtcolJ server.
    Thread exits when ProtocolJ server loop exits, which is typically upon remote command to exit.
    """

    def __init__(self, runtime, dispatcher, configuration):
        threading.Thread.__init__(self)
        self.runtime = runtime
        self.dispatcher = dispatcher
        self.configuration = configuration

    # ----------------------------------------------------------------------------------------
    def run(self):

        try:
            server = new_ServerInterface(self.runtime, self.configuration)
            server.activate()

            # Loop until commanded to exit by remote request.
            server.loop(self.dispatcher)

        except KeyboardInterrupt:
            self.runtime.exit_due_to_interrupt("keyboard interrupt")

        except Exception as exception:
            self.runtime.exit_due_to_exception(
                "unexpected exception: %s" % (exception), exception
            )


"""
Run the main class.
"""
main = Main()
main.run()
