import threading
import time
from collections.abc import Sequence

import numpy as np
import pytest
from aspn23 import (
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    TypeHeader,
    TypeTimestamp,
)
from numpy import float64
from numpy.typing import NDArray
from pntos.api import Message, Registry
from pntos.cobra.dummy_plugins.DummyMediator import DummyMediator
from pntos.cobra.standard_plugins.StandardRegistryPlugin import StandardRegistryPlugin
from pntos.cobra.utils import (
    BufferedMutableValueView,
    BufferedValueView,
    GroupsView,
    MutableValueView,
    ValueView,
)


@pytest.fixture
def registry_plugin() -> StandardRegistryPlugin:
    plugin = StandardRegistryPlugin('Test Registry Views')
    mediator = DummyMediator()
    plugin.init_plugin(mediator=mediator)
    return plugin


@pytest.fixture
def registry(registry_plugin: StandardRegistryPlugin) -> Registry:
    reg = registry_plugin.new_registry(None)
    DummyMediator.registry = reg
    return reg


@pytest.fixture
def test_message() -> Message:
    return Message(
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
        'test_source',
    )


class TestGroupsView:
    def test_initialization_empty_registry(self, registry: Registry) -> None:
        view = GroupsView(registry)
        assert view.groups is None or len(view.groups) == 0

    def test_initialization_with_existing_groups(self, registry: Registry) -> None:
        kv1 = registry.batch_start('group1')
        kv1['key1'] = 'value1'
        kv1.batch_end()

        kv2 = registry.batch_start('group2')
        kv2['key2'] = 'value2'
        kv2.batch_end()

        view = GroupsView(registry)
        assert view.groups is not None
        assert 'group1' in view.groups
        assert 'group2' in view.groups

    def test_new_group_notification(self, registry: Registry) -> None:
        view = GroupsView(registry)
        initial_count = len(view.groups) if view.groups else 0

        kv = registry.batch_start('new_group')
        kv['key'] = 'value'
        kv.batch_end()

        assert view.groups is not None
        assert 'new_group' in view.groups
        assert len(view.groups) == initial_count + 1

    def test_multiple_new_groups_in_sequence(self, registry: Registry) -> None:
        view = GroupsView(registry)

        for i in range(5):
            kv = registry.batch_start(f'group_{i}')
            kv[f'key_{i}'] = f'value_{i}'
            kv.batch_end()

        assert view.groups is not None
        assert len(view.groups) >= 5
        for i in range(5):
            assert f'group_{i}' in view.groups

    def test_groups_property_returns_sequence(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['key'] = 'value'
        kv.batch_end()

        view = GroupsView(registry)
        assert view.groups is None or isinstance(view.groups, Sequence)


class TestValueView:
    def test_initialization_with_existing_value(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 42
        kv.batch_end()

        view = ValueView(registry, 'test_group', 'test_key', int)
        assert view.value == 42

    def test_initialization_with_nonexistent_key(self, registry: Registry) -> None:
        view = ValueView(registry, 'test_group', 'nonexistent_key', int)
        assert view.value is None

    def test_value_updates_via_callback(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 10
        kv.batch_end()

        view = ValueView(registry, 'test_group', 'test_key', int)
        assert view.value == 10

        kv = registry.batch_start('test_group')
        kv['test_key'] = 20
        kv.batch_end()

        assert view.value == 20

    def test_properties(self, registry: Registry) -> None:
        view = ValueView(registry, 'my_group', 'my_key', str)
        assert view.group == 'my_group'
        assert view.key == 'my_key'
        assert view.type is str
        assert view.value is None

    def test_union_mode_no_type(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 'string_value'
        kv.batch_end()

        view = ValueView(registry, 'test_group', 'test_key')
        assert view.value == 'string_value'
        assert view.type is None

        kv = registry.batch_start('test_group')
        kv['test_key'] = 42
        kv.batch_end()

        assert view.value == 42

    def test_specific_type_mode_str(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 'hello'
        kv.batch_end()

        view = ValueView(registry, 'test_group', 'test_key', str)
        assert view.value == 'hello'

    def test_specific_type_mode_int(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 123
        kv.batch_end()

        view = ValueView(registry, 'test_group', 'test_key', int)
        assert view.value == 123
        assert isinstance(view.value, int)

    def test_specific_type_mode_float(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 3.14159
        kv.batch_end()

        view = ValueView(registry, 'test_group', 'test_key', float)
        assert view.value == 3.14159

    def test_specific_type_mode_bool(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = True
        kv.batch_end()

        view = ValueView(registry, 'test_group', 'test_key', bool)
        assert view.value is True
        assert isinstance(view.value, bool)

    def test_specific_type_mode_list_str(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = ['a', 'b', 'c']
        kv.batch_end()

        view = ValueView(registry, 'test_group', 'test_key', list)
        assert view.value == ['a', 'b', 'c']
        assert isinstance(view.value, list)

    def test_specific_type_mode_ndarray(self, registry: Registry) -> None:
        test_array = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=float64)
        kv = registry.batch_start('test_group')
        kv['test_key'] = test_array
        kv.batch_end()

        view: ValueView[NDArray[float64]] = ValueView(
            registry, 'test_group', 'test_key', np.ndarray
        )
        assert view.value is not None
        assert np.array_equal(view.value, test_array)
        assert isinstance(view.value, np.ndarray)

    def test_specific_type_mode_message(
        self, registry: Registry, test_message: Message
    ) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = test_message
        kv.batch_end()

        view = ValueView(registry, 'test_group', 'test_key', Message)
        assert view.value == test_message

    def test_concurrent_value_access(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 0
        kv.batch_end()

        view = ValueView(registry, 'test_group', 'test_key', int)
        results = []
        errors = []

        def read_value() -> None:
            try:
                for _ in range(100):
                    val = view.value
                    results.append(val)
                    time.sleep(0.001)
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        def write_value() -> None:
            try:
                for i in range(100):
                    kv = registry.batch_start('test_group')
                    kv['test_key'] = i
                    kv.batch_end()
                    time.sleep(0.001)
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        reader_thread = threading.Thread(target=read_value)
        writer_thread = threading.Thread(target=write_value)

        reader_thread.start()
        writer_thread.start()

        reader_thread.join()
        writer_thread.join()

        assert len(errors) == 0
        assert len(results) > 0

    def test_callback_invoked_from_different_thread(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 0
        kv.batch_end()

        view = ValueView(registry, 'test_group', 'test_key', int)

        def update_value() -> None:
            kv = registry.batch_start('test_group')
            kv['test_key'] = 999
            kv.batch_end()

        thread = threading.Thread(target=update_value)
        thread.start()
        thread.join()

        assert view.value == 999

    def test_view_with_none_initial_value(self, registry: Registry) -> None:
        view = ValueView(registry, 'test_group', 'nonexistent', int)
        assert view.value is None

        kv = registry.batch_start('test_group')
        kv['nonexistent'] = 42
        kv.batch_end()

        assert view.value == 42

    def test_multiple_updates(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 1
        kv.batch_end()

        view = ValueView(registry, 'test_group', 'test_key', int)

        for i in range(2, 11):
            kv = registry.batch_start('test_group')
            kv['test_key'] = i
            kv.batch_end()
            assert view.value == i


class TestBufferedValueView:
    def test_buffer_starts_empty(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 10
        kv.batch_end()

        view = BufferedValueView(registry, 'test_group', 'test_key', int)
        assert len(view.buffer) == 0

    def test_buffer_accumulates_values(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 1
        kv.batch_end()

        view = BufferedValueView(registry, 'test_group', 'test_key', int)

        for i in range(2, 6):
            kv = registry.batch_start('test_group')
            kv['test_key'] = i
            kv.batch_end()

        assert isinstance(view.buffer, Sequence)
        assert len(view.buffer) == 4
        assert view.buffer == [2, 3, 4, 5]

    def test_pop_clears_returns_all_buffered_values(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 1
        kv.batch_end()

        view = BufferedValueView(registry, 'test_group', 'test_key', int)

        for i in range(2, 6):
            kv = registry.batch_start('test_group')
            kv['test_key'] = i
            kv.batch_end()

        popped = view.pop()
        assert len(popped) == 4
        assert popped == [2, 3, 4, 5]
        assert len(view.buffer) == 0

    def test_multiple_pop_operations(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 1
        kv.batch_end()

        view = BufferedValueView(registry, 'test_group', 'test_key', int)

        kv = registry.batch_start('test_group')
        kv['test_key'] = 2
        kv.batch_end()

        first_pop = view.pop()
        assert len(first_pop) == 1
        assert first_pop == [2]

        kv = registry.batch_start('test_group')
        kv['test_key'] = 3
        kv.batch_end()

        kv = registry.batch_start('test_group')
        kv['test_key'] = 4
        kv.batch_end()

        second_pop = view.pop()
        assert len(second_pop) == 2
        assert second_pop == [3, 4]

    def test_buffer_thread_safety(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 0
        kv.batch_end()

        view = BufferedValueView(registry, 'test_group', 'test_key', int)
        errors = []

        def write_values() -> None:
            try:
                for i in range(1, 51):
                    kv = registry.batch_start('test_group')
                    kv['test_key'] = i
                    kv.batch_end()
                    time.sleep(0.001)
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        def read_buffer() -> None:
            try:
                for _ in range(10):
                    _ = view.buffer
                    time.sleep(0.005)
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        writer_thread = threading.Thread(target=write_values)
        reader_thread = threading.Thread(target=read_buffer)

        writer_thread.start()
        reader_thread.start()

        writer_thread.join()
        reader_thread.join()

        assert len(errors) == 0

    def test_inherits_value_view_functionality(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 42
        kv.batch_end()

        view = BufferedValueView(registry, 'test_group', 'test_key', int)

        assert view.value == 42
        assert view.group == 'test_group'
        assert view.key == 'test_key'
        assert view.type is int

    def test_callback_updates_both_value_and_buffer(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 1
        kv.batch_end()

        view = BufferedValueView(registry, 'test_group', 'test_key', int)
        assert view.value == 1

        kv = registry.batch_start('test_group')
        kv['test_key'] = 2
        kv.batch_end()

        assert view.value == 2
        assert len(view.buffer) == 1
        assert view.buffer[0] == 2

    def test_key_dne(self, registry: Registry) -> None:
        view = BufferedValueView(registry, 'test_group', 'test_key', int)
        assert len(view.buffer) == 0

        kv = registry.batch_start('test_group')
        kv['test_key'] = 42
        kv.batch_end()

        assert len(view.buffer) == 1
        assert view.buffer[0] == 42


class TestMutableValueView:
    def test_set_value_without_kv(self, registry: Registry) -> None:
        view = MutableValueView(registry, 'test_group', 'test_key', int)
        view.set_value(42)

        kv = registry.batch_start('test_group')
        assert kv['test_key'] == 42
        kv.batch_end()

    def test_set_value_with_kv(self, registry: Registry) -> None:
        view = MutableValueView(registry, 'test_group', 'test_key', int)

        kv = registry.batch_start('test_group')
        view.set_value(99, kv)
        kv.batch_end()

        kv = registry.batch_start('test_group')
        assert kv['test_key'] == 99
        kv.batch_end()

    def test_value_property_syncs_after_set_value(self, registry: Registry) -> None:
        view = MutableValueView(registry, 'test_group', 'test_key', int)
        view.set_value(123)

        assert view.value == 123

    def test_set_value_updates_registry(self, registry: Registry) -> None:
        view = MutableValueView(registry, 'test_group', 'test_key', str)
        view.set_value('hello')

        kv = registry.batch_start('test_group')
        assert kv['test_key'] == 'hello'
        kv.batch_end()

    def test_set_value_with_batch_triggers_callback(self, registry: Registry) -> None:
        view1 = MutableValueView(registry, 'test_group', 'test_key', int)
        view2 = ValueView(registry, 'test_group', 'test_key', int)

        view1.set_value(777)

        assert view2.value == 777

    def test_set_value_with_provided_kv(self, registry: Registry) -> None:
        view = MutableValueView(registry, 'test_group', 'test_key', int)

        kv = registry.batch_start('test_group')
        view.set_value(555, kv)
        kv.batch_end()

        kv.batch_restart()
        assert kv['test_key'] == 555
        assert view.value == 555
        kv.batch_end()

    def test_set_value_with_float(self, registry: Registry) -> None:
        view = MutableValueView(registry, 'test_group', 'test_key', float)
        view.set_value(3.14159)

        assert view.value == 3.14159

    def test_set_value_with_str(self, registry: Registry) -> None:
        view = MutableValueView(registry, 'test_group', 'test_key', str)
        view.set_value('test_string')

        assert view.value == 'test_string'

    def test_set_value_with_bool(self, registry: Registry) -> None:
        view = MutableValueView(registry, 'test_group', 'test_key', bool)
        view.set_value(True)

        assert view.value is True

    def test_set_value_with_ndarray(self, registry: Registry) -> None:
        test_array = np.array([1.0, 2.0, 3.0], dtype=float64)
        view: MutableValueView[NDArray[float64]] = MutableValueView(
            registry, 'test_group', 'test_key', np.ndarray
        )
        view.set_value(test_array)

        assert view.value is not None
        assert np.array_equal(view.value, test_array)

    def test_inherits_value_view_functionality(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 100
        kv.batch_end()

        view = MutableValueView(registry, 'test_group', 'test_key', int)

        assert view.value == 100
        assert view.group == 'test_group'
        assert view.key == 'test_key'
        assert view.type is int

    def test_multiple_set_values(self, registry: Registry) -> None:
        view = MutableValueView(registry, 'test_group', 'test_key', int)

        for i in range(1, 11):
            view.set_value(i)
            assert view.value == i

    def test_incorrect_type(
        self, registry: Registry, capsys: pytest.CaptureFixture[str]
    ) -> None:
        view = MutableValueView(registry, 'test_group', 'test_key', int)

        # Clear terminal
        capsys.readouterr()

        view.set_value('I am a str!')  # type: ignore[arg-type]

        # Callback should trigger, we should get a normal error message (not a terminal
        # error message)
        out, err = capsys.readouterr()
        assert "Unable to convert from type <class 'str'> to type <class 'int'>" in out
        assert not err


class TestBufferedMutableValueView:
    def test_writes_are_buffered(self, registry: Registry) -> None:
        view = BufferedMutableValueView(registry, 'test_group', 'test_key', int)
        view.set_value(10)

        assert len(view.buffer) == 1
        assert view.buffer[0] == 10

    def test_set_value_and_buffer_interaction(self, registry: Registry) -> None:
        view = BufferedMutableValueView(registry, 'test_group', 'test_key', int)

        view.set_value(1)
        view.set_value(2)
        view.set_value(3)

        assert len(view.buffer) == 3
        assert view.buffer == [1, 2, 3]

    def test_pop_includes_self_written_values(self, registry: Registry) -> None:
        view = BufferedMutableValueView(registry, 'test_group', 'test_key', int)

        view.set_value(100)
        view.set_value(200)
        view.set_value(300)

        popped = view.pop()
        assert len(popped) == 3
        assert popped == [100, 200, 300]

    def test_inherits_mutable_value_view(self, registry: Registry) -> None:
        view = BufferedMutableValueView(registry, 'test_group', 'test_key', int)

        view.set_value(42)

        assert view.value == 42
        assert view.group == 'test_group'
        assert view.key == 'test_key'
        assert view.type is int

        kv = registry.batch_start('test_group')
        assert kv['test_key'] == 42
        kv.batch_end()

    def test_inherits_buffered_value_view(self, registry: Registry) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 1
        kv.batch_end()

        view = BufferedMutableValueView(registry, 'test_group', 'test_key', int)

        kv = registry.batch_start('test_group')
        kv['test_key'] = 2
        kv.batch_end()

        assert len(view.buffer) == 1
        assert view.buffer[0] == 2

        popped = view.pop()
        assert len(popped) == 1
        assert len(view.buffer) == 0

    def test_buffer_captures_external_and_self_written(
        self, registry: Registry
    ) -> None:
        view = BufferedMutableValueView(registry, 'test_group', 'test_key', int)

        view.set_value(10)
        assert view.value == 10

        kv = registry.batch_start('test_group')
        kv['test_key'] = 20
        kv.batch_end()
        assert view.value == 20

        view.set_value(30)
        assert view.value == 30

        assert len(view.buffer) == 3
        assert view.buffer == [10, 20, 30]

    def test_multiple_pops(self, registry: Registry) -> None:
        view = BufferedMutableValueView(registry, 'test_group', 'test_key', int)

        view.set_value(1)
        view.set_value(2)

        first_pop = view.pop()
        assert first_pop == [1, 2]
        assert len(view.buffer) == 0

        view.set_value(3)
        view.set_value(4)

        second_pop = view.pop()
        assert second_pop == [3, 4]
        assert len(view.buffer) == 0

    def test_init_both_subtypes(self, registry: Registry) -> None:
        view = BufferedMutableValueView(registry, 'test_group', 'test_key', int)
        assert not view._started_batch  # from MutableValueView.__init__
        assert len(view._buffer) == 0  # from BufferedValueView.__init__
