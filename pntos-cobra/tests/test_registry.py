import io
import pickle
import unittest
from unittest.mock import patch

import numpy as np
from aspn23 import (
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    TypeHeader,
    TypeTimestamp,
)
from numpy import float64
from numpy.typing import NDArray
from pntos.api import (
    CommonPlugin,
    ControllerPlugin,
    KeyValueStore,
    LoggingLevel,
    Mediator,
    Message,
    Registry,
    RegistryValueTypeUnion,
)
from pntos.cobra import (
    SimpleRegistryPlugin,
)
from pntos.cobra.config import (
    AlignmentConfig,
    ConfigTypeUnion,
    ImuConfig,
    SensorConfig,
    config_from_registry,
)
from pntos.cobra.SimpleRegistryPlugin import (
    SimpleKeyValueStore,
)

my_config: list[ConfigTypeUnion] = [
    ImuConfig(
        accel_bias_sigma=(0.0098, 0.0098, 0.0098),
        accel_bias_tau=(3600.0, 3600.0, 3600.0),
        accel_rw_sigma=(0.001, 0.001, 0.001),
        gyro_bias_sigma=(1.234e-6, 1.234e-6, 1.234e-6),
        gyro_bias_tau=(3600.0, 3600.0, 3600.0),
        gyro_rw_sigma=(0.001, 0.001, 0.001),
        group='config/default/test',
    ),
    AlignmentConfig(
        initial_pos=(1, 2, 3),
        initial_vel=(4, 5, 6),
        initial_rpy=(7, 8, 9),
        initial_accel_bias=(10, 11, 12),
        initial_gyro_bias=(13, 14, 15),
        initial_time=1.23,
        initial_pos_var=(9.0, 9.0, 9.0),
        initial_vel_var=(0.1, 0.1, 0.1),
        initial_tilt_var=(0.01, 0.01, 0.01),
        initial_accel_bias_var=(9.604e-5, 9.604e-5, 9.604e-5),
        initial_gyro_bias_var=(2.3504074e-11, 2.3504074e-11, 2.3504074e-11),
        group='config/default/test',
    ),
    SensorConfig(
        lever_arm=(0.0, 0.0, 0.0),
        orientation=(0.0, 0.0, 0.0, 0.0),
        source_identifier='lcm://cobranav/novatel',
        destination_identifier='gps_measurement_processor',
        use_for_alignment=True,
        sensor_name='novatel',
        group='config/default/test',
    ),
]

Dummy_log_out: str = ''


def dummy_log(level: LoggingLevel, message: str) -> None:
    global Dummy_log_out
    if level == LoggingLevel.ERROR:
        Dummy_log_out = message


class DummyMediator(Mediator):
    registry: Registry

    def get_filter_description_list(self) -> list[str]:
        return []

    def request_solutions(
        self,
        solution_times: list[TypeTimestamp],
        filter_description: str | None = None,
    ) -> list[Message]:
        return []

    def process_pntos_message(self, message: Message) -> None:
        return

    def broadcast_aspn_message(
        self,
        message: Message,
        transport: str | None = None,
        destination_identifier: str | None = None,
    ) -> None:
        return

    def log_message(self, level: LoggingLevel, message: str) -> None:
        dummy_log(level, message)


class DummyControllerPlugin(ControllerPlugin):
    plugins: list[CommonPlugin]

    def __init__(self, identifier: str):
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        return

    def shutdown_plugin(self) -> None:
        for plugin in self.plugins:
            plugin.shutdown_plugin()

    def take_control(
        self,
        plugins: list[CommonPlugin],
        plugin_resources_locations: list[str | None] | None = None,
        initial_config: str | None = None,
    ) -> None:
        self.plugins = plugins
        for plugin in self.plugins:
            plugin.init_plugin(mediator=DummyMediator())


class TestRegistry(unittest.TestCase):
    registry: SimpleRegistryPlugin
    reg: Registry
    test_message: Message

    def __init__(self, name: str):
        self.registry = SimpleRegistryPlugin('Simple registry 1')
        self.registry.init_plugin(mediator=DummyMediator())
        self.reg = self.registry.new_registry(None)
        DummyMediator.registry = self.reg

        self.test_message = Message(
            MeasurementPositionVelocityAttitude(
                TypeHeader(0, 0, 0, 0),
                TypeTimestamp(0),
                MeasurementPositionVelocityAttitudeReferenceFrame.ECI,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                np.array([]),
                MeasurementPositionVelocityAttitudeErrorModel.NONE,
                np.array([]),
                [],
            ),
            'Genesis planet',
        )
        self._test_types = [
            str,
            list[str],
            int,
            bool,
            float,
            NDArray[float64],
            Message,
        ]
        self._test_keys = [str(n) for n in self._test_types]
        self._test_vals: list[RegistryValueTypeUnion] = [
            'Wassup',
            ['What', 'is', 'up'],
            42,
            True,
            3.14159,
            np.array([[0.0, 0.1], [0.2, 0.3]], dtype=float64),
            self.test_message,
        ]
        self._test_err = [
            'for str field failed.',
            'for list[str] field failed.',
            'for int field failed.',
            'for bool field failed.',
            'for float field failed.',
            'for NDArray field failed.',
            'for Message field failed.',
        ]

        super().__init__(name)

    @property
    def test_types(self) -> list[type[RegistryValueTypeUnion]]:
        return self._test_types

    @property
    def test_keys(self) -> list[str]:
        return self._test_keys

    @property
    def test_vals(self) -> list[RegistryValueTypeUnion]:
        return self._test_vals

    @property
    def test_err(self) -> list[str]:
        return self._test_err

    @property
    def test_group(self) -> str:
        return 'generic_test_group'

    def set_up_store_with_all_types(self, group: str | None = None) -> KeyValueStore:
        """NOTE: Assumes :meth:`KeyValueStore.clear()` works."""
        if group is None:
            group = self.test_group
        test_kv = self.reg.batch_start(group)
        test_kv.clear()

        # Initializing kvstore with all keys and values
        for i, key in enumerate(self.test_keys):
            test_kv[key] = self.test_vals[i]

        return test_kv

    def test_clear(self) -> None:
        test_kv = self.reg.batch_start(self.test_group)

        # Initializing kvstore with all keys and values
        for i, key in enumerate(self.test_keys):
            test_kv[key] = self.test_vals[i]

        # Test clear, which should remove all keys, values, and callbacks
        test_kv.clear()
        for i, key in enumerate(self.test_keys):
            assert key not in test_kv, 'clear() ' + self.test_err[i]

    def test_initial_config(self) -> None:
        registry = SimpleRegistryPlugin('Simple registry', config=my_config)
        registry.init_plugin(mediator=DummyMediator())
        reg = registry.new_registry(None)
        for expected in my_config:
            collected = config_from_registry(  # type: ignore[type-var]
                type(expected), registry.mediator, self.test_group
            )
            for expected_attr, collected_attr in zip(dir(expected), dir(collected)):
                if not expected_attr.startswith('__'):  # Don't check dunders
                    exp_val = getattr(expected, expected_attr)
                    col_val = getattr(collected, collected_attr)
                    assert type(exp_val) == type(col_val)
                    if type(exp_val) == np.ndarray:
                        assert np.all(exp_val == col_val)
                    else:
                        assert exp_val == col_val

    def test_add_to_registry(self) -> None:
        kv: KeyValueStore = self.reg.batch_start(self.test_group)
        for i in range(10):
            kv.set_value(f'Key {i}', i)
        kv.batch_end()
        kv = self.reg.batch_start(self.test_group)
        key_array = kv.keys()
        assert key_array is not None, 'key_array is None...'
        for i, a in enumerate(key_array):
            assert a == f'Key {i}', 'Incorrect key'
            assert kv.get_value(a, int) == i, 'Incorrect value'
        kv.batch_end()

    def test_request_notify_new_group_registry(self) -> None:
        callbacked_group: str = ''

        # Make test callback
        def test_callback(group: str) -> None:
            nonlocal callbacked_group
            callbacked_group = group

        # Register callback
        assert self.reg.request_notify_new_group(
            test_callback
        ), 'Failed to register notify new group.'

        # Make group
        kv: KeyValueStore = self.reg.batch_start(self.test_group)

        # See if callback happened
        assert (
            callbacked_group != ''
        ), 'Callback for request notify new group not called.'
        assert callbacked_group == self.test_group, 'Request notify new group failed.'

    def test_any_value_to_str(self) -> None:
        """NOTE: Message types are treated differently - not converted to str."""

        test_str = 'Hello There!'
        test_list_str = ['Hello', 'There']
        test_int = 42
        test_bool = True
        test_float = 3.1415927
        test_np_array = np.array([1.0, 1.1, 1.2])

        test_s_str = test_str
        test_s_list_str = str(test_list_str)
        test_s_int = str(test_int)
        test_s_bool = str(test_bool)
        test_s_float = str(test_float)
        test_s_np_array = None

        m_str = 'String to string failed.'
        m_list_str = 'list of strings to string failed.'
        m_int = 'Int to string failed.'
        m_bool = 'Bool to string failed.'
        m_float = 'Float to string failed.'
        m_np_array = 'Numpy array to string failed.'

        kv = self.reg.batch_start(self.test_group)
        kv.set_value('str', test_str)
        kv.set_value('list[str]', test_list_str)
        kv.set_value('int', test_int)
        kv.set_value('bool', test_bool)
        kv.set_value('float', test_float)
        kv.set_value('np_array', test_np_array)
        kv.batch_end()

        kv = self.reg.batch_start(self.test_group)
        assert kv.get_value('str', str) == test_s_str, m_str
        assert kv.get_value('list[str]', str) == test_s_list_str, m_list_str
        assert kv.get_value('int', str) == test_s_int, m_int
        assert kv.get_value('bool', str) == test_s_bool, m_bool
        assert kv.get_value('float', str) == test_s_float, m_float
        assert kv.get_value('np_array', str) == test_s_np_array, m_np_array

    def test_str_to_int(self) -> None:
        test_str_1 = '42'
        test_int_1 = 42
        test_str_2 = 'Not a number'

        kv = self.reg.batch_start(self.test_group)
        kv.set_value('str1', test_str_1)
        kv.set_value('str2', test_str_2)
        kv.batch_end()

        kv.batch_restart()
        assert kv.get_value('str1', int) == test_int_1, 'Str to int failed.'
        assert kv.get_value('str2', int) is None, 'Expected None, did not receive None.'

    def test_np_array_to_np_array(self) -> None:
        test_array_1 = np.array([i for i in range(20)], dtype=float64)
        test_array_2 = np.array([[0, 1], [2, 3]], dtype=float64)
        test_array_3 = np.array([[[0, 1], [2, 3]], [[4, 5], [6, 7]]], dtype=float64)

        kv = self.reg.batch_start(self.test_group)
        kv.set_value('array1', test_array_1)
        kv.set_value('array2', test_array_2)
        kv.set_value('array3', test_array_3)
        kv.batch_end()

        kv.batch_restart()
        assert (
            kv.get_value('array1', float) is None
        ), 'Got an unexpected return for ndarray->float conversion.'
        out_1 = kv.get_value('array1', np.ndarray)
        out_2 = kv.get_value('array2', np.ndarray)
        out_3 = kv.get_value('array3', np.ndarray)
        assert type(out_1) == np.ndarray, 'Did not receive a np array back.'
        assert type(out_2) == np.ndarray, 'Did not receive a np array back.'
        assert type(out_3) == np.ndarray, 'Did not receive a np array back.'
        assert (out_1 == test_array_1).all(), 'One-dimensional numpy array failed.'
        assert (out_2 == test_array_2).all(), 'Two-dimensional numpy array failed.'
        assert (out_3 == test_array_3).all(), 'Three-dimensional numpy array failed.'

    def test_str_to_list(self) -> None:
        test_str_1 = 'Hello there'
        test_list_1 = [test_str_1]

        kv = self.reg.batch_start(self.test_group)
        kv.set_value('str1', test_str_1)
        kv.batch_end()

        kv.batch_restart()
        assert kv.get_value('str1', list) == test_list_1, 'Str to list failed.'

    def test_number_to_list(self) -> None:
        test_num_1 = 42
        test_num_2 = 3.141597

        test_list_1 = [str(test_num_1)]
        test_list_2 = [str(test_num_2)]

        m_1 = 'Int to list failed.'
        m_2 = 'Float to list failed.'

        kv = self.reg.batch_start(self.test_group)
        kv.set_value('t1', test_num_1)
        kv.set_value('t2', test_num_2)
        kv.batch_end()

        kv.batch_restart()
        assert kv.get_value('t1', list) == test_list_1, m_1
        assert kv.get_value('t2', list) == test_list_2, m_2

    def test_messages(self) -> None:
        """Message types in registry should just stay as Messages."""

        m_message = 'Saving and retrieving Message failed.'
        expected_str = str(self.test_message)

        kv = self.reg.batch_start(self.test_group)
        kv.set_value('message', self.test_message)
        kv.batch_end()

        kv.batch_restart()
        thing = kv.get_value('message', str)
        assert kv.get_value('message', str) == None, m_message
        assert kv.get_value('message', int) == None, m_message
        assert kv.get_value('message', Message) == self.test_message, m_message

    def test_raw_string(self) -> None:
        test_string = 'test string'
        key = 'key'

        kv = self.reg.batch_start(self.test_group)
        kv.set_raw(key, test_string.encode('utf-8'))
        kv.batch_end()

        kv = self.reg.batch_start(self.test_group)
        bytes_out = kv.get_raw(key)
        assert bytes_out is not None
        assert bytes_out.decode('utf-8') == test_string
        kv.batch_end()

    def test_raw_message(self) -> None:
        key = 'key'

        kv = self.reg.batch_start(self.test_group)
        kv.set_raw(key, pickle.dumps(self.test_message))
        kv.batch_end()

        kv = self.reg.batch_start(self.test_group)
        bytes_out = kv.get_raw(key)
        assert bytes_out is not None
        message_out: Message = pickle.loads(bytes_out)
        kv.batch_end()

        assert self.test_message.source_identifier == message_out.source_identifier
        test_aspn_message = self.test_message.wrapped_message
        aspn_message_out = message_out.wrapped_message

        # Numpy fields need a different comparator. Otherwise we could just == the two messages.
        numpy_attributes = ['covariance', 'error_model_params']
        for attribute in test_aspn_message.__dict__:
            test_attribute = getattr(test_aspn_message, attribute)
            attribute_out = getattr(aspn_message_out, attribute)
            if test_attribute is None or attribute_out is None:
                continue
            if attribute in numpy_attributes:
                assert np.array_equal(test_attribute, attribute_out)
            else:
                assert test_attribute == attribute_out

    def test_assign_twice(self) -> None:
        kv = self.set_up_store_with_all_types()

        for i, key in enumerate(self.test_keys):
            kv[key] = self.test_vals[i]

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_batch_rules(self, mock_stdout: io.StringIO) -> None:
        if self.registry.mediator is None:  # Controller not implemented
            return  # type: ignore[unreachable]

        kv = self.reg.batch_start(self.test_group)
        kv.batch_end()
        kv.set_value('Enterprise', 1701)
        assert Dummy_log_out != '', 'Did not catch misuse of Registry.'

    def test_request_notify_no_key(self) -> None:
        test_keys = ['Resistance', 'is', 'futile.']
        test_kv = self.reg.batch_start(self.test_group)
        for k in test_keys:
            test_kv.set_value(k, 0)

        callbacked_group: str = ''
        callbacked_keys: list[str] = []
        callbacked_kv: KeyValueStore = SimpleKeyValueStore('', dummy_log)

        def test_callback(group: str, keys: list[str], kv: KeyValueStore) -> None:
            nonlocal callbacked_group
            nonlocal callbacked_keys
            nonlocal callbacked_kv
            callbacked_group = group
            callbacked_keys = keys
            callbacked_kv = kv

        test_kv.batch_end()

        test_kv.batch_restart()
        assert test_kv.request_notify(
            None, test_callback
        ), 'Unable to register callback.'

        for k in test_keys:
            test_kv.set_value(k, 1)
        test_kv.batch_end()

        assert callbacked_group == self.test_group, 'Callback group failed.'
        assert set(callbacked_keys) == set(test_keys), 'Callback keys failed.'
        assert callbacked_kv == test_kv, 'Callback kv failed.'

    def test_request_notify_multiple_keys(self) -> None:
        test_keys = ['Resistance', 'is', 'futile.']
        test_kv = self.reg.batch_start(self.test_group)
        for k in test_keys:
            test_kv.set_value(k, 0)

        callbacked_group: str = ''
        callbacked_keys: list[str] = []
        callbacked_kv: KeyValueStore = SimpleKeyValueStore('', dummy_log)

        def test_callback(group: str, keys: list[str], kv: KeyValueStore) -> None:
            nonlocal callbacked_group
            nonlocal callbacked_keys
            nonlocal callbacked_kv
            callbacked_group = group
            callbacked_keys = keys
            callbacked_kv = kv

        test_kv.batch_end()

        test_kv.batch_restart()
        for k in test_keys:
            assert test_kv.request_notify(
                k, test_callback
            ), 'Unable to register callback.'

        for k in test_keys:
            test_kv.set_value(k, 1)
        test_kv.batch_end()

        assert callbacked_group == self.test_group, 'Callback group failed.'
        assert set(callbacked_keys) == set(test_keys), 'Callback keys failed.'
        assert callbacked_kv == test_kv, 'Callback kv failed.'

    def test_remove_notify_no_key(self) -> None:
        test_keys = ['Resistance', 'is', 'futile.']
        test_kv = self.reg.batch_start(self.test_group)
        for k in test_keys:
            test_kv.set_value(k, 0)

        callbacked_group: str = ''
        callbacked_keys: list[str] = []
        callbacked_kv: KeyValueStore = SimpleKeyValueStore('', dummy_log)

        def test_callback(group: str, keys: list[str], kv: KeyValueStore) -> None:
            nonlocal callbacked_group
            nonlocal callbacked_keys
            nonlocal callbacked_kv
            callbacked_group = group
            callbacked_keys = keys
            callbacked_kv = kv

        test_kv.batch_end()

        test_kv.batch_restart()
        assert test_kv.request_notify(
            None, test_callback
        ), 'Unable to register callback.'

        for k in test_keys:
            test_kv.set_value(k, 1)
        test_kv.batch_end()

        assert callbacked_group == self.test_group, 'Callback group failed.'
        assert set(callbacked_keys) == set(test_keys), 'Callback keys failed.'
        assert callbacked_kv == test_kv, 'Callback kv failed.'

        test_kv.batch_restart()
        assert test_kv.remove_notify(None, test_callback)

        callbacked_group = ''
        callbacked_keys = []
        callbacked_kv = SimpleKeyValueStore('', dummy_log)

        for k in test_keys:
            test_kv.set_value(k, 2)
        test_kv.batch_end()

        assert callbacked_group != self.test_group, 'Remove notify group failed.'
        assert set(callbacked_keys) != set(test_keys), 'Remove notify keys failed.'
        assert callbacked_kv != test_kv, 'Remove notify kv failed.'

    def test_remove_notify_multiple_keys(self) -> None:
        test_keys = ['Resistance', 'is', 'futile.']
        test_kv = self.reg.batch_start(self.test_group)
        for k in test_keys:
            test_kv.set_value(k, 0)

        callbacked_group: str = ''
        callbacked_keys: list[str] = []
        callbacked_kv: KeyValueStore = SimpleKeyValueStore('', dummy_log)

        def test_callback(group: str, keys: list[str], kv: KeyValueStore) -> None:
            nonlocal callbacked_group
            nonlocal callbacked_keys
            nonlocal callbacked_kv
            callbacked_group = group
            callbacked_keys = keys
            callbacked_kv = kv

        test_kv.batch_end()

        test_kv.batch_restart()
        for k in test_keys:
            assert test_kv.request_notify(
                k, test_callback
            ), 'Unable to register callback.'

        for k in test_keys:
            test_kv.set_value(k, 1)
        test_kv.batch_end()

        assert callbacked_group == self.test_group, 'Callback group failed.'
        assert set(callbacked_keys) == set(test_keys), 'Callback keys failed.'
        assert callbacked_kv == test_kv, 'Callback kv failed.'

        test_kv.batch_restart()
        for k in test_keys:
            assert test_kv.remove_notify(k, test_callback)

        callbacked_group = ''
        callbacked_keys = []
        callbacked_kv = SimpleKeyValueStore('', dummy_log)

        for k in test_keys:
            test_kv.set_value(k, 2)
        test_kv.batch_end()

        assert callbacked_group != self.test_group, 'Remove notify group failed.'
        assert set(callbacked_keys) != set(test_keys), 'Remove notify keys failed.'
        assert callbacked_kv != test_kv, 'Remove notify kv failed.'

    def test_get_type(self) -> None:
        """NOTE: This function may not be implemented."""
        test_kv = self.set_up_store_with_all_types()

        # Check if get_type is implemented
        get_type_implemented = False
        for key in self.test_keys:
            gotten_type = test_kv.get_type(key)
            if gotten_type is not None:
                get_type_implemented = True
                break

        # test get_type
        for i, key in enumerate(self.test_keys):
            kv_type = test_kv.get_type(key)
            if get_type_implemented:  # If implemented, should return type
                assert kv_type == self.test_types[i], self.test_err[i]
            else:  # If not implemented, should return None
                assert kv_type is None, self.test_err[i]

    def test___contains__(self) -> None:
        test_kv = self.set_up_store_with_all_types()

        # Make sure all keys are in there
        for i, key in enumerate(self.test_keys):
            assert key in test_kv, f'__contains__ {self.test_err[i]}'

    def test___setitem__(self) -> None:
        test_kv = self.set_up_store_with_all_types()

        # Make sure all key/value pairs are in there
        types = [str, list, int, bool, float, np.ndarray, Message]

        # test str
        val0 = test_kv.get_value(self.test_keys[0], str)
        assert val0 is not None
        assert val0 == self.test_vals[0], f'__setitem__ {self.test_err[0]}'

        # test list
        val1 = test_kv.get_value(self.test_keys[1], list)
        assert val1 is not None
        assert val1 == self.test_vals[1], f'__setitem__ {self.test_err[1]}'

        # test int
        val2 = test_kv.get_value(self.test_keys[2], int)
        assert val2 is not None
        assert val2 == self.test_vals[2], f'__setitem__ {self.test_err[2]}'

        # test bool
        val3 = test_kv.get_value(self.test_keys[3], bool)
        assert val3 is not None
        assert val3 == self.test_vals[3], f'__setitem__ {self.test_err[3]}'

        # test float
        val4 = test_kv.get_value(self.test_keys[4], float)
        assert val4 is not None
        assert val4 == self.test_vals[4], f'__setitem__ {self.test_err[4]}'

        # test numpy array
        val5 = test_kv.get_value(self.test_keys[5], np.ndarray)
        assert val5 is not None
        assert np.all(val5 == self.test_vals[5]), f'__setitem__ {self.test_err[5]}'

        # test message
        val6 = test_kv.get_value(self.test_keys[6], Message)
        assert val6 is not None
        assert val6 == self.test_vals[6], f'__setitem__ {self.test_err[6]}'

    def test___getitem__(self) -> None:
        test_kv = self.set_up_store_with_all_types()

        # Need to first check if `get_type` is implemented
        get_type_implemented = False
        for key in self.test_keys:
            if key in test_kv:
                gotten_type = test_kv.get_type(key)
                if gotten_type is not None:
                    get_type_implemented = True
                    break

        # Need test to only be str|Message if get_type is not implemented
        test_vals = self.test_vals
        if not get_type_implemented:
            for i, val in enumerate(test_vals):
                if not issubclass(type(val), Message):
                    test_vals[i] = str(val)

        # Make sure we can get all values with __getitem__ (test_kv[key])
        for i, key in enumerate(self.test_keys):
            gotten = test_kv[key]
            if type(gotten) is np.ndarray:
                assert np.all(gotten == test_vals[i]), f'__getitem__ {self.test_err[i]}'
            else:
                assert gotten == test_vals[i], f'__getitem__ {self.test_err[i]}'

    def test___len__(self) -> None:
        test_kv = self.set_up_store_with_all_types()

        assert len(test_kv) == len(self.test_keys), '__len__ failed.'

    def test___iter__(self) -> None:
        test_kv = self.set_up_store_with_all_types()

        # Test __iter__ - should iterate over the keys
        for i, key in enumerate(test_kv):
            assert key == self.test_keys[i], '__iter__ ' + self.test_err[i]

    def test_invalid_type_in_registry(self) -> None:
        kv = self.reg.batch_start(self.test_group)
        key = 'invalid_type_key'
        value = ImuConfig(
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
            group='config/default/test',
        )
        # Have to type ignore this one because it's exactly what we're testing:
        kv[key] = value  # type: ignore[assignment]
        assert key not in kv, 'Expected failure to insert value - but key exists.'

    def test___delitem__(self) -> None:
        test_kv = self.set_up_store_with_all_types()

        # Test __delitem__
        for i, key in enumerate(self.test_keys):
            del test_kv[key]
            assert key not in test_kv

    def test_items(self) -> None:
        test_kv = self.set_up_store_with_all_types()

        # Test items which should return tuple (key, value) pairs
        for i, (key, val) in enumerate(test_kv.items()):
            assert key == self.test_keys[i], 'items() key ' + self.test_err[i]
            if type(val) == np.ndarray:
                assert np.all(val == self.test_vals[i]), (
                    'items() value ' + self.test_err[i]
                )
            else:
                assert val == self.test_vals[i], 'items() value ' + self.test_err[i]

    def test_values(self) -> None:
        test_kv = self.set_up_store_with_all_types()

        # Test values, which should return an iterable of the values
        for i, val in enumerate(test_kv.values()):
            if type(val) == np.ndarray:
                assert np.all(val == self.test_vals[i]), (
                    'items() value ' + self.test_err[i]
                )
            else:
                assert val == self.test_vals[i], 'items() value ' + self.test_err[i]

    def test_set_permanent(self) -> None:
        permanent_batch = 'permanent'
        not_permanent_batch = 'not_permanent'

        permanent_keys = [k + '_p' for k in self.test_keys]
        not_permanent_keys = [k + '_np' for k in self.test_keys]

        ### First instance of plugins ###

        # Start up this instance
        controller = DummyControllerPlugin('Dummy Controller 1')
        registry = SimpleRegistryPlugin('Simple registry 1')
        controller.take_control(
            [registry],
            [None],
            None,
        )
        controller.init_plugin(None, None)
        reg = registry.new_registry(None)

        # Get kv store and set permanent values
        kv_permanent = reg.batch_start(permanent_batch)
        kv_permanent.set_permanent(True)
        for i, key in enumerate(permanent_keys):
            kv_permanent[key] = self.test_vals[i]

        # Set non-permanent values
        kv_permanent.set_permanent(False)
        for i, key in enumerate(not_permanent_keys):
            kv_permanent[key] = self.test_vals[i]

        kv_permanent.batch_end()

        # Get non_permanent kv store and set non-permanent values
        kv_not_permanent = reg.batch_start(not_permanent_batch)
        kv_not_permanent.set_permanent(False)
        for i, key in enumerate(not_permanent_keys):
            kv_not_permanent[key] = self.test_vals[i]
        kv_not_permanent.batch_end()

        # Shutdown registry plugin - simulate pntOS shutting down.
        registry.shutdown_plugin()

        ### Second instance of plugins ### (Pretend it's a fresh start of pntOS)

        # Set up the instance
        controller = DummyControllerPlugin('Dummy Controller 2')
        registry = SimpleRegistryPlugin('Simple registry 2')
        controller.take_control(
            [registry],
            [None],
            None,
        )
        controller.init_plugin(None, None)
        reg = registry.new_registry(None)

        # Test if the right groups persisted with the right number of keys
        kv_permanent = reg.batch_start(permanent_batch)
        kv_not_permanent = reg.batch_start(not_permanent_batch)
        assert len(kv_not_permanent) == 0, 'Non-permanent group persisted unexpectedly.'
        assert len(kv_permanent) == len(
            permanent_keys
        ), 'Wrong number of permanent keys persisted.'

        # Make sure the wrong keys are not there and the right ones are
        for key in self.test_keys:
            assert (
                key + '_np' not in kv_permanent
            ), f'Unexpected key {key} in permanent store.'
            assert (
                key + '_p' in kv_permanent
            ), f'Expected key {key}, but could not find in store.'

        # See if get_type is enabled
        get_type_enabled = False
        for key in permanent_keys:
            gotten_type = kv_permanent.get_type(key)
            if gotten_type is not None:
                get_type_enabled = True
                break

        # Determine expected value
        expected_vals = self.test_vals
        if not get_type_enabled:  # Need only strings and messages if so
            expected_vals = [
                str(v) if not issubclass(type(v), Message) else v for v in expected_vals
            ]

        # Test expected values
        for i, key in enumerate(permanent_keys):
            actual_val = kv_permanent[key]
            if isinstance(actual_val, np.ndarray):
                assert np.all(expected_vals[i] == actual_val), (
                    'set_permanent() ' + self.test_err[i]
                )
            elif isinstance(actual_val, Message):
                assert self.compare_messages(actual_val, expected_vals[i]), (
                    'set_permanent() ' + self.test_err[i]
                )
            else:
                assert expected_vals[i] == actual_val, (
                    'set_permanent() ' + self.test_err[i]
                )

    def compare_messages(self, m1: object, m2: object, depth: int = 0) -> bool:
        """The numpy arrays in Message objects do not seem to compare nicely
        with "==" after coming out of permanency. This is a hacky workaround to
        run np.all() on any np elements, and run normal comparison otherwise."""
        if hasattr(m1, '__dict__') and depth < 3:
            for attr in m1.__dict__:
                value1 = getattr(m1, attr)
                value2 = getattr(m2, attr)

                if isinstance(value1, np.ndarray) and isinstance(value2, np.ndarray):
                    if not np.array_equal(value1, value2):
                        return False
                else:
                    if not self.compare_messages(value1, value2, depth + 1):
                        return False
            return True
        else:
            return m1 == m2


def suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    tests = [m for m in dir(TestRegistry) if m.startswith('test_')]
    for test in tests:
        suite.addTest(TestRegistry(test))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
