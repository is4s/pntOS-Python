import cProfile
import pstats

from pntos.cobra import LcmLogTransportPlugin


class LcmLogTransportPluginWithProfiling(LcmLogTransportPlugin):
    """A transport plugin which process LCM messages from a log with profiling enabled.

    To use, simply swap out the LcmLogTransportPlugin in your app for this one, using
    the same LcmLogTransportConfig.

    NOTE: This plugin uses a simple profiling method that only profiles the thread used
    to read the data from the LCM log. Thus, if this plugin is used with a controller
    plugin that utilizes a multi-threaded or multi-processed concurrency model, this
    plugin has very limited usefulness.
    """

    def read_log(self) -> None:
        """Process messages from LCM log, with profiling enabled."""
        profile = cProfile.Profile()
        profile.enable()
        super().read_log()
        profile.disable()
        pstats.Stats(profile).sort_stats('cumtime').print_stats(100)
