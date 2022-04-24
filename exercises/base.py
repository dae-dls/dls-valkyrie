# Runtime support such as configuration.
from lib_dls_runtime.runtime import Runtime

from lib_dls_runtime.with_timing import WithTiming

import logging

logger = logging.getLogger(__name__)


class Base:
    """
    Object representing an exercise command line program.
    """

    # -----------------------------------------------------------------
    def __init__(self):
        self.runtime = Runtime()
        self.runtime.configure_from_command_line()

    # -----------------------------------------------------------------
    def with_timing(self, tag):
        return WithTiming(self.runtime, tag)
