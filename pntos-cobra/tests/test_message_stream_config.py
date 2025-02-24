import unittest

from aspn23 import (
    AspnBase,
    MeasurementAltitude,
    MeasurementAngularVelocity,
    MeasurementHeading,
    MeasurementPositionVelocityAttitude,
    MeasurementSatnav,
)
from pntos.cobra.internal import (
    SimpleMessageStreamConfig,
)


class Test_MessageStreamConfig(unittest.TestCase):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.message_types: list[type[AspnBase]] = [
            MeasurementPositionVelocityAttitude,
            MeasurementAltitude,
            MeasurementAngularVelocity,
            MeasurementHeading,
            MeasurementSatnav,
        ]

    def test_SimpleMessageStreamConfig_immediate_stream_all_no_stream_conf(
        self,
    ) -> None:
        conf = SimpleMessageStreamConfig()
        conf.immediate_stream_all(True)
        for message_type in self.message_types:
            assert not conf.is_sequenced(message_type)

    def test_SimpleMessageStreamConfig_sequenced_stream_all_no_stream_conf(
        self,
    ) -> None:
        conf = SimpleMessageStreamConfig()
        conf.sequenced_stream_all(True)
        for message_type in self.message_types:
            assert conf.is_sequenced(message_type)

    def test_SimpleMessageStreamConfig_immediate_stream_add_no_stream_conf(
        self,
    ) -> None:
        conf = SimpleMessageStreamConfig()
        conf.sequenced_stream_all(True)  # Start with all sequenced
        n = 3
        for i in range(n):
            conf.immediate_stream_add(self.message_types[i])
        for message_type in self.message_types[:n]:
            assert not conf.is_sequenced(message_type)
        for message_type in self.message_types[n:]:
            assert conf.is_sequenced(message_type)

    def test_SimpleMessageStreamConfig_sequenced_stream_add_no_stream_conf(
        self,
    ) -> None:
        conf = SimpleMessageStreamConfig()
        conf.immediate_stream_all(True)  # Start with all immediate
        n = 3
        for i in range(n):
            conf.sequenced_stream_add(self.message_types[i])
        for message_type in self.message_types[:n]:
            assert conf.is_sequenced(message_type)
        for message_type in self.message_types[n:]:
            assert not conf.is_sequenced(message_type)

    def test_SimpleMessageStreamConfig_immediate_stream_remove_no_stream_conf(
        self,
    ) -> None:
        conf = SimpleMessageStreamConfig()
        conf.sequenced_stream_all(True)  # Start with all sequenced
        n = 3

        # Add some to immediate stream
        for i in range(n):
            conf.immediate_stream_add(self.message_types[i])
        for message_type in self.message_types[:n]:
            assert not conf.is_sequenced(message_type)
        for message_type in self.message_types[n:]:
            assert conf.is_sequenced(message_type)

        # Remove the ones we added to immediate stream - all should be sequenced
        for i in range(n):
            conf.immediate_stream_remove(self.message_types[i])
        for message_type in self.message_types:
            assert conf.is_sequenced(message_type)

    def test_SimpleMessageStreamConfig_sequenced_stream_remove_no_stream_conf(
        self,
    ) -> None:
        conf = SimpleMessageStreamConfig()
        conf.immediate_stream_all(True)  # Start with all immediate
        n = 3

        # Add some to sequenced stream
        for i in range(n):
            conf.sequenced_stream_add(self.message_types[i])
        for message_type in self.message_types[:n]:
            assert conf.is_sequenced(message_type)
        for message_type in self.message_types[n:]:
            assert not conf.is_sequenced(message_type)

        # Remove the ones we added to sequenced stream - all should be immediate
        for i in range(n):
            conf.sequenced_stream_remove(self.message_types[i])
        for message_type in self.message_types:
            assert not conf.is_sequenced(message_type)

    def test_SimpleMessageStreamConfig_immediate_add_after_sequenced_add(
        self,
    ) -> None:
        conf = SimpleMessageStreamConfig()
        conf.immediate_stream_all(True)  # Start with all immediate
        n = 3

        # Add some to sequenced stream
        for i in range(n):
            conf.sequenced_stream_add(self.message_types[i])
        for message_type in self.message_types[:n]:
            assert conf.is_sequenced(message_type)
        for message_type in self.message_types[n:]:
            assert not conf.is_sequenced(message_type)

        # immediate stream the ones we added to sequenced stream - all should be immediate
        for i in range(n):
            conf.immediate_stream_add(self.message_types[i])
        for message_type in self.message_types:
            assert not conf.is_sequenced(message_type)

    def test_SimpleMessageStreamConfig_sequenced_add_after_immediate_add(
        self,
    ) -> None:
        conf = SimpleMessageStreamConfig()
        conf.sequenced_stream_all(True)  # Start with all sequenced
        n = 3

        # Add some to immediate stream
        for i in range(n):
            conf.immediate_stream_add(self.message_types[i])
        for message_type in self.message_types[:n]:
            assert not conf.is_sequenced(message_type)
        for message_type in self.message_types[n:]:
            assert conf.is_sequenced(message_type)

        # Sequence stream the ones we added to immediate stream - all should be sequenced
        for i in range(n):
            conf.sequenced_stream_add(self.message_types[i])
        for message_type in self.message_types:
            assert conf.is_sequenced(message_type)


def suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    tests = [m for m in dir(Test_MessageStreamConfig) if m.startswith('test_')]
    for test in tests:
        suite.addTest(Test_MessageStreamConfig(test))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
