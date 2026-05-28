import threading
import time
from uuid import uuid4

import pytest
from pntos.api import Registry, RegistryValueTypeUnion
from pntos.cobra.advanced_plugins.ui.models import (
    Snapshot,
    Subscription,
    SubscriptionMode,
    Write,
)
from pntos.cobra.advanced_plugins.ui.utils import (
    CallbackRegistrar,
    KeyInfo,
    LockedSequenceGenerator,
    RegistryManager,
    SequenceBuffer,
)
from pntos.cobra.dummy_plugins.DummyMediator import DummyMediator
from pntos.cobra.standard_plugins.StandardRegistryPlugin import StandardRegistryPlugin


@pytest.fixture
def registry_plugin() -> StandardRegistryPlugin:
    plugin = StandardRegistryPlugin('Test UI Utils')
    mediator = DummyMediator()
    plugin.init_plugin(mediator=mediator)
    return plugin


@pytest.fixture
def registry(registry_plugin: StandardRegistryPlugin) -> Registry:
    reg = registry_plugin.new_registry(None)
    DummyMediator.registry = reg
    return reg


@pytest.fixture
def mediator() -> DummyMediator:
    return DummyMediator()


@pytest.fixture
def registry_manager(mediator: DummyMediator, registry: Registry) -> RegistryManager:
    mediator.registry = registry
    return RegistryManager(mediator)


@pytest.fixture
def test_subscription() -> Subscription:
    return Subscription(
        id=uuid4(),
        group='test_group',
        key='test_key',
        mode=SubscriptionMode.LAST,
    )


class TestSequenceBuffer:
    def test_initialization(self) -> None:
        buffer: SequenceBuffer[dict[str, int | str]] = SequenceBuffer(
            lambda x: x['seq']  # type: ignore[arg-type, return-value]
        )
        assert buffer._next_id == 0
        assert len(buffer._pending) == 0

    def test_add_items_in_order_returns_immediately(self) -> None:
        buffer: SequenceBuffer[dict[str, int | str]] = SequenceBuffer(
            lambda x: x['seq']  # type: ignore[arg-type, return-value]
        )

        result1 = buffer.add({'seq': 0, 'data': 'first'})
        assert len(result1) == 1
        assert result1[0]['data'] == 'first'

        result2 = buffer.add({'seq': 1, 'data': 'second'})
        assert len(result2) == 1
        assert result2[0]['data'] == 'second'

        result3 = buffer.add({'seq': 2, 'data': 'third'})
        assert len(result3) == 1
        assert result3[0]['data'] == 'third'

    def test_add_items_out_of_order_buffers_them(self) -> None:
        buffer: SequenceBuffer[dict[str, int | str]] = SequenceBuffer(
            lambda x: x['seq']  # type: ignore[arg-type, return-value]
        )

        result1 = buffer.add({'seq': 2, 'data': 'third'})
        assert len(result1) == 0
        assert len(buffer._pending) == 1

        result2 = buffer.add({'seq': 1, 'data': 'second'})
        assert len(result2) == 0
        assert len(buffer._pending) == 2

    def test_adding_missing_sequence_releases_buffered_items(self) -> None:
        buffer: SequenceBuffer[dict[str, int | str]] = SequenceBuffer(
            lambda x: x['seq']  # type: ignore[arg-type, return-value]
        )

        buffer.add({'seq': 2, 'data': 'third'})
        buffer.add({'seq': 1, 'data': 'second'})

        result = buffer.add({'seq': 0, 'data': 'first'})

        assert len(result) == 3
        assert result[0]['data'] == 'first'
        assert result[1]['data'] == 'second'
        assert result[2]['data'] == 'third'
        assert len(buffer._pending) == 0

    def test_multiple_gaps_in_sequence(self) -> None:
        buffer: SequenceBuffer[dict[str, int | str]] = SequenceBuffer(
            lambda x: x['seq']  # type: ignore[arg-type, return-value]
        )

        buffer.add({'seq': 0, 'data': 'first'})
        buffer.add({'seq': 3, 'data': 'fourth'})
        buffer.add({'seq': 5, 'data': 'sixth'})

        assert buffer._next_id == 1
        assert len(buffer._pending) == 2

        result = buffer.add({'seq': 1, 'data': 'second'})
        assert len(result) == 1
        assert result[0]['data'] == 'second'
        assert len(buffer._pending) == 2

        result = buffer.add({'seq': 2, 'data': 'third'})
        assert len(result) == 2
        assert result[0]['data'] == 'third'
        assert result[1]['data'] == 'fourth'
        assert len(buffer._pending) == 1

    def test_duplicate_sequence_ids(self) -> None:
        buffer: SequenceBuffer[dict[str, int | str]] = SequenceBuffer(
            lambda x: x['seq']  # type: ignore[arg-type, return-value]
        )

        buffer.add({'seq': 1, 'data': 'first_version'})
        buffer.add({'seq': 1, 'data': 'second_version'})

        result = buffer.add({'seq': 0, 'data': 'zero'})

        assert len(result) == 2
        assert result[0]['data'] == 'zero'
        assert result[1]['data'] == 'second_version'

    def test_large_sequence_gap(self) -> None:
        buffer: SequenceBuffer[dict[str, int | str]] = SequenceBuffer(
            lambda x: x['seq']  # type: ignore[arg-type, return-value]
        )

        buffer.add({'seq': 1000, 'data': 'far_future'})
        assert len(buffer._pending) == 1
        assert buffer._next_id == 0

        for i in range(1000):
            result = buffer.add({'seq': i, 'data': f'item_{i}'})
            if i == 0:
                assert len(result) == 1
            elif i == 999:
                assert len(result) == 2
                assert result[0]['data'] == 'item_999'
                assert result[1]['data'] == 'far_future'
            else:
                assert len(result) == 1

    def test_thread_safety_with_concurrent_adds(self) -> None:
        buffer: SequenceBuffer[dict[str, int | str]] = SequenceBuffer(
            lambda x: x['seq']  # type: ignore[arg-type, return-value]
        )
        results = []
        errors = []
        lock = threading.Lock()

        def add_items(start: int, count: int) -> None:
            try:
                for i in range(start, start + count):
                    result = buffer.add({'seq': i, 'data': f'item_{i}'})
                    with lock:
                        results.extend(result)
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        threads = [
            threading.Thread(target=add_items, args=(0, 50)),
            threading.Thread(target=add_items, args=(50, 50)),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0
        assert buffer._next_id == 100


class TestLockedSequenceGenerator:
    def test_initialization_starts_at_zero(self) -> None:
        gen = LockedSequenceGenerator()
        assert gen._n == 0

    def test_next_property_returns_incrementing_values(self) -> None:
        gen = LockedSequenceGenerator()

        assert gen.next == 0
        assert gen.next == 1
        assert gen.next == 2
        assert gen.next == 3

    def test_reset_resets_counter_to_zero(self) -> None:
        gen = LockedSequenceGenerator()

        gen.next  # noqa: B018
        gen.next  # noqa: B018
        gen.next  # noqa: B018
        assert gen._n == 3

        gen.reset()
        assert gen._n == 0
        assert gen.next == 0

    def test_thread_safety_with_concurrent_next_calls(self) -> None:
        gen = LockedSequenceGenerator()
        results = []
        errors = []
        lock = threading.Lock()

        def get_next_values(count: int) -> None:
            try:
                for _ in range(count):
                    val = gen.next
                    with lock:
                        results.append(val)
                    time.sleep(0.0001)
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        threads = [
            threading.Thread(target=get_next_values, args=(50,)),
            threading.Thread(target=get_next_values, args=(50,)),
            threading.Thread(target=get_next_values, args=(50,)),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0
        assert len(results) == 150
        assert len(set(results)) == 150
        assert set(results) == set(range(150))

    def test_sequential_consistency_across_threads(self) -> None:
        gen = LockedSequenceGenerator()
        results = []
        errors = []

        def get_sequences(count: int) -> None:
            try:
                local_results = [gen.next for _ in range(count)]
                results.append(local_results)
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        threads = [
            threading.Thread(target=get_sequences, args=(100,)),
            threading.Thread(target=get_sequences, args=(100,)),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0
        all_values = [val for sublist in results for val in sublist]
        assert len(all_values) == 200
        assert set(all_values) == set(range(200))


class TestKeyInfo:
    def test_initialization(self, registry: Registry) -> None:
        callback_registrar = CallbackRegistrar()
        key_info: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            registry, 'test_group', 'test_key', callback_registrar
        )

        assert key_info.group == 'test_group'
        assert key_info.key == 'test_key'
        assert len(key_info._subscriptions) == 0
        assert key_info.value is None

    def test_inherits_mutable_value_view_functionality(
        self, registry: Registry
    ) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 42
        kv.batch_end()

        callback_registrar = CallbackRegistrar()
        key_info: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            registry, 'test_group', 'test_key', callback_registrar
        )

        assert key_info.value == 42

    def test_add_subscription(
        self, registry: Registry, test_subscription: Subscription
    ) -> None:
        callback_registrar = CallbackRegistrar()
        key_info: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            registry, 'test_group', 'test_key', callback_registrar
        )

        key_info.add(test_subscription)

        assert test_subscription.id in key_info._subscriptions
        assert key_info._subscriptions[test_subscription.id] == test_subscription

    def test_remove_subscription(
        self, registry: Registry, test_subscription: Subscription
    ) -> None:
        callback_registrar = CallbackRegistrar()
        key_info: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            registry, 'test_group', 'test_key', callback_registrar
        )

        key_info.add(test_subscription)
        assert test_subscription.id in key_info._subscriptions

        key_info.remove(test_subscription.id)
        assert test_subscription.id not in key_info._subscriptions

    def test_remove_nonexistent_subscription(self, registry: Registry) -> None:
        callback_registrar = CallbackRegistrar()
        key_info: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            registry, 'test_group', 'test_key', callback_registrar
        )

        nonexistent_id = uuid4()
        key_info.remove(nonexistent_id)

        assert len(key_info._subscriptions) == 0

    def test_add_duplicate_subscription(
        self, registry: Registry, test_subscription: Subscription
    ) -> None:
        callback_registrar = CallbackRegistrar()
        key_info: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            registry, 'test_group', 'test_key', callback_registrar
        )

        key_info.add(test_subscription)
        assert test_subscription.id in key_info._subscriptions

        # Should handle duplicate gracefully
        key_info.add(test_subscription)
        assert test_subscription.id in key_info._subscriptions

        key_info.remove(test_subscription.id)
        assert test_subscription.id not in key_info._subscriptions

    def test_subscription_ids_property(self, registry: Registry) -> None:
        callback_registrar = CallbackRegistrar()
        key_info: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            registry, 'test_group', 'test_key', callback_registrar
        )

        sub1 = Subscription(id=uuid4(), group='g', key='k', mode=SubscriptionMode.LAST)
        sub2 = Subscription(id=uuid4(), group='g', key='k', mode=SubscriptionMode.LAST)

        key_info.add(sub1)
        key_info.add(sub2)

        sub_ids = key_info.subscription_ids
        assert len(sub_ids) == 2
        assert sub1.id in sub_ids
        assert sub2.id in sub_ids

    def test_callback_registers_change_with_registrar(self, registry: Registry) -> None:
        callback_registrar = CallbackRegistrar()
        key_info: KeyInfo[RegistryValueTypeUnion] = KeyInfo(  # noqa: F841
            registry, 'test_group', 'test_key', callback_registrar
        )

        kv = registry.batch_start('test_group')
        kv['test_key'] = 100
        kv.batch_end()

        assert callback_registrar.data.is_set()
        changes = callback_registrar.pop()
        assert 'test_group' in changes
        assert 'test_key' in changes['test_group']

    def test_set_value_prevents_frontend_update(self, registry: Registry) -> None:
        callback_registrar = CallbackRegistrar()
        key_info: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            registry, 'test_group', 'test_key', callback_registrar
        )

        key_info.set_value(42)

        assert not callback_registrar.data.is_set()

        changes = callback_registrar.pop()
        assert len(changes) == 0

    def test_multiple_subscriptions_to_same_key(self, registry: Registry) -> None:
        callback_registrar = CallbackRegistrar()
        key_info: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            registry, 'test_group', 'test_key', callback_registrar
        )

        subs = [
            Subscription(
                id=uuid4(),
                group='test_group',
                key='test_key',
                mode=SubscriptionMode.LAST,
            )
            for _ in range(5)
        ]

        for sub in subs:
            key_info.add(sub)

        assert len(key_info._subscriptions) == 5
        assert len(key_info.subscription_ids) == 5


class TestCallbackRegistrar:
    def test_initialization_creates_empty_state(self) -> None:
        registrar = CallbackRegistrar()

        assert len(registrar._dict) == 0
        assert not registrar.data.is_set()

    def test_data_event_starts_cleared(self) -> None:
        registrar = CallbackRegistrar()

        assert not registrar.data.is_set()

    def test_register_change_sets_data_event(self, registry: Registry) -> None:
        registrar = CallbackRegistrar()
        key_info: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            registry, 'test_group', 'test_key', registrar
        )

        registrar.register_change(key_info)

        assert registrar.data.is_set()

    def test_register_change_adds_key_info_to_dict(self, registry: Registry) -> None:
        registrar = CallbackRegistrar()
        key_info: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            registry, 'test_group', 'test_key', registrar
        )

        registrar.register_change(key_info)

        assert 'test_group' in registrar._dict
        assert 'test_key' in registrar._dict['test_group']
        assert registrar._dict['test_group']['test_key'] is key_info

    def test_register_change_same_key_twice_uses_same_instance(
        self, registry: Registry
    ) -> None:
        registrar = CallbackRegistrar()
        key_info: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            registry, 'test_group', 'test_key', registrar
        )

        registrar.register_change(key_info)
        registrar.register_change(key_info)

        assert registrar._dict['test_group']['test_key'] is key_info

    def test_register_change_raises_error_for_different_instances(
        self, registry: Registry
    ) -> None:
        registrar = CallbackRegistrar()
        key_info1: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            registry, 'test_group', 'test_key', registrar
        )
        key_info2: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            registry, 'test_group', 'test_key', registrar
        )

        registrar.register_change(key_info1)

        with pytest.raises(RuntimeError, match='Multiple KeyInfo objects'):
            registrar.register_change(key_info2)

    def test_pop_returns_all_registered_changes(self, registry: Registry) -> None:
        registrar = CallbackRegistrar()
        key_info1: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            registry, 'group1', 'key1', registrar
        )
        key_info2: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            registry, 'group2', 'key2', registrar
        )

        registrar.register_change(key_info1)
        registrar.register_change(key_info2)

        changes = registrar.pop()

        assert 'group1' in changes
        assert 'key1' in changes['group1']
        assert 'group2' in changes
        assert 'key2' in changes['group2']

    def test_pop_clears_internal_dict_and_event(self, registry: Registry) -> None:
        registrar = CallbackRegistrar()
        key_info: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            registry, 'test_group', 'test_key', registrar
        )

        registrar.register_change(key_info)
        assert registrar.data.is_set()

        registrar.pop()

        assert not registrar.data.is_set()
        assert len(registrar._dict) == 0

    def test_pop_when_empty_returns_empty_dict(self) -> None:
        registrar = CallbackRegistrar()

        changes = registrar.pop()

        assert len(changes) == 0
        assert not registrar.data.is_set()

    def test_thread_safety_with_concurrent_register_change(
        self, registry: Registry
    ) -> None:
        registrar = CallbackRegistrar()
        errors = []

        def register_changes(group: str, count: int) -> None:
            try:
                for i in range(count):
                    key_info: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
                        registry, group, f'key_{i}', registrar
                    )
                    registrar.register_change(key_info)
                    time.sleep(0.0001)
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        threads = [
            threading.Thread(target=register_changes, args=('group1', 20)),
            threading.Thread(target=register_changes, args=('group2', 20)),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0
        changes = registrar.pop()
        assert 'group1' in changes
        assert 'group2' in changes

    def test_thread_safety_register_and_pop(self, registry: Registry) -> None:
        registrar = CallbackRegistrar()
        errors = []
        pop_results = []

        def register_changes(count: int) -> None:
            try:
                for i in range(count):
                    key_info: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
                        registry, 'test_group', f'key_{i}', registrar
                    )
                    registrar.register_change(key_info)
                    time.sleep(0.001)
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        def pop_changes(count: int) -> None:
            try:
                for _ in range(count):
                    time.sleep(0.005)
                    changes = registrar.pop()
                    pop_results.append(changes)
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        register_thread = threading.Thread(target=register_changes, args=(50,))
        pop_thread = threading.Thread(target=pop_changes, args=(10,))

        register_thread.start()
        pop_thread.start()

        register_thread.join()
        pop_thread.join()

        assert len(errors) == 0


class TestRegistryManager:
    def test_initialization_with_mediator(
        self, mediator: DummyMediator, registry: Registry
    ) -> None:
        mediator.registry = registry
        manager = RegistryManager(mediator)

        assert manager.mediator is mediator
        assert len(manager.subscriptions_map) == 0
        assert len(manager.key_info_map) == 0

    def test_subscribe_creates_new_key_info(
        self, registry_manager: RegistryManager, test_subscription: Subscription
    ) -> None:
        registry_manager.subscribe(test_subscription)

        assert test_subscription.id in registry_manager.subscriptions_map
        group_key = (test_subscription.group, test_subscription.key)
        assert group_key in registry_manager.key_info_map

    def test_subscribe_to_existing_key_reuses_key_info(
        self, registry_manager: RegistryManager
    ) -> None:
        sub1 = Subscription(
            id=uuid4(), group='test_group', key='test_key', mode=SubscriptionMode.LAST
        )
        sub2 = Subscription(
            id=uuid4(), group='test_group', key='test_key', mode=SubscriptionMode.LAST
        )

        registry_manager.subscribe(sub1)
        registry_manager.subscribe(sub2)

        group_key = ('test_group', 'test_key')
        key_info = registry_manager.key_info_map[group_key]
        assert len(key_info.subscription_ids) == 2

    def test_unsubscribe_removes_subscription(
        self, registry_manager: RegistryManager, test_subscription: Subscription
    ) -> None:
        registry_manager.subscribe(test_subscription)
        assert test_subscription.id in registry_manager.subscriptions_map

        registry_manager.unsubscribe(test_subscription)

        assert test_subscription.id not in registry_manager.subscriptions_map

    def test_unsubscribe_removes_key_info_when_no_subscriptions_remain(
        self, registry_manager: RegistryManager, test_subscription: Subscription
    ) -> None:
        registry_manager.subscribe(test_subscription)
        group_key = (test_subscription.group, test_subscription.key)
        assert group_key in registry_manager.key_info_map

        registry_manager.unsubscribe(test_subscription)

        assert group_key not in registry_manager.key_info_map

    def test_unsubscribe_nonexistent_subscription_does_nothing(
        self, registry_manager: RegistryManager
    ) -> None:
        nonexistent_sub = Subscription(
            id=uuid4(), group='fake', key='fake', mode=SubscriptionMode.LAST
        )

        registry_manager.unsubscribe(nonexistent_sub)

        assert len(registry_manager.subscriptions_map) == 0

    def test_snapshot_returns_current_values(
        self, registry_manager: RegistryManager, registry: Registry
    ) -> None:
        kv = registry.batch_start('test_group')
        kv['key1'] = 100
        kv['key2'] = 'hello'
        kv.batch_end()

        sub1 = Subscription(
            id=uuid4(), group='test_group', key='key1', mode=SubscriptionMode.LAST
        )
        sub2 = Subscription(
            id=uuid4(), group='test_group', key='key2', mode=SubscriptionMode.LAST
        )
        registry_manager.subscribe(sub1)
        registry_manager.subscribe(sub2)

        snapshot = registry_manager.snapshot()

        assert isinstance(snapshot, Snapshot)
        assert 'test_group' in snapshot.data
        assert snapshot.data['test_group']['key1'] == 100
        assert snapshot.data['test_group']['key2'] == 'hello'

    def test_snapshot_skips_none_values(
        self, registry_manager: RegistryManager
    ) -> None:
        sub = Subscription(
            id=uuid4(),
            group='test_group',
            key='nonexistent',
            mode=SubscriptionMode.LAST,
        )
        registry_manager.subscribe(sub)

        snapshot = registry_manager.snapshot()

        assert (
            'test_group' not in snapshot.data
            or 'nonexistent' not in snapshot.data.get('test_group', {})
        )

    def test_write_updates_registry_values(
        self, registry_manager: RegistryManager, registry: Registry
    ) -> None:
        sub = Subscription(
            id=uuid4(), group='test_group', key='test_key', mode=SubscriptionMode.LAST
        )
        registry_manager.subscribe(sub)

        write_request = Write(
            data={'test_group': {'test_key': 999}},
            sequence_id=1,
        )

        registry_manager.write(write_request)

        kv = registry.batch_start('test_group')
        assert kv['test_key'] == 999
        kv.batch_end()

    def test_write_uses_batch_operations(
        self, registry_manager: RegistryManager, registry: Registry
    ) -> None:
        sub1 = Subscription(
            id=uuid4(), group='test_group', key='key1', mode=SubscriptionMode.LAST
        )
        sub2 = Subscription(
            id=uuid4(), group='test_group', key='key2', mode=SubscriptionMode.LAST
        )
        registry_manager.subscribe(sub1)
        registry_manager.subscribe(sub2)

        write_request = Write(
            data={'test_group': {'key1': 111, 'key2': 222}},
            sequence_id=1,
        )

        registry_manager.write(write_request)

        kv = registry.batch_start('test_group')
        assert kv['key1'] == 111
        assert kv['key2'] == 222
        kv.batch_end()

    def test_pop_waits_for_callback_data(
        self, registry_manager: RegistryManager, registry: Registry
    ) -> None:
        sub = Subscription(
            id=uuid4(), group='test_group', key='test_key', mode=SubscriptionMode.LAST
        )
        registry_manager.subscribe(sub)

        def trigger_update() -> None:
            time.sleep(0.1)
            kv = registry.batch_start('test_group')
            kv['test_key'] = 42
            kv.batch_end()

        thread = threading.Thread(target=trigger_update)
        thread.start()

        chunk_update = registry_manager.pop(timeout=1.0)

        thread.join()

        assert chunk_update is not None
        assert 'test_group' in chunk_update.unordered_updates

    def test_pop_with_timeout_returns_none_when_no_data(
        self, registry_manager: RegistryManager
    ) -> None:
        result = registry_manager.pop(timeout=0.1)

        assert result is None

    def test_pop_returns_chunk_update_with_sequence_ids(
        self, registry_manager: RegistryManager, registry: Registry
    ) -> None:
        sub = Subscription(
            id=uuid4(), group='test_group', key='test_key', mode=SubscriptionMode.LAST
        )
        registry_manager.subscribe(sub)

        kv = registry.batch_start('test_group')
        kv['test_key'] = 100
        kv.batch_end()

        chunk_update = registry_manager.pop(timeout=0.5)

        assert chunk_update is not None
        assert 'test_group' in chunk_update.unordered_updates
        key_update = chunk_update.unordered_updates['test_group']['test_key']
        assert key_update.val == 100
        assert key_update.sequence_id == 0

    def test_pop_includes_subscription_ids(
        self, registry_manager: RegistryManager, registry: Registry
    ) -> None:
        sub = Subscription(
            id=uuid4(), group='test_group', key='test_key', mode=SubscriptionMode.LAST
        )
        registry_manager.subscribe(sub)

        kv = registry.batch_start('test_group')
        kv['test_key'] = 42
        kv.batch_end()

        chunk_update = registry_manager.pop(timeout=0.5)

        assert chunk_update is not None
        key_update = chunk_update.unordered_updates['test_group']['test_key']
        assert str(sub.id) in key_update.subscription_ids

    def test_multiple_subscriptions_to_different_keys(
        self, registry_manager: RegistryManager, registry: Registry
    ) -> None:
        sub1 = Subscription(
            id=uuid4(), group='group1', key='key1', mode=SubscriptionMode.LAST
        )
        sub2 = Subscription(
            id=uuid4(), group='group2', key='key2', mode=SubscriptionMode.LAST
        )

        registry_manager.subscribe(sub1)
        registry_manager.subscribe(sub2)

        assert len(registry_manager.subscriptions_map) == 2
        assert len(registry_manager.key_info_map) == 2

    def test_shutdown_method(self, registry_manager: RegistryManager) -> None:
        registry_manager.shutdown()


class TestRegistryManagerIntegration:
    def test_subscribe_write_pop_cycle(
        self, registry_manager: RegistryManager, registry: Registry
    ) -> None:
        sub = Subscription(
            id=uuid4(), group='test_group', key='test_key', mode=SubscriptionMode.LAST
        )
        registry_manager.subscribe(sub)

        write_request = Write(
            data={'test_group': {'test_key': 777}},
            sequence_id=1,
        )
        registry_manager.write(write_request)

        snapshot = registry_manager.snapshot()
        assert snapshot.data['test_group']['test_key'] == 777

    def test_multiple_clients_subscribing_to_same_key(
        self, registry_manager: RegistryManager, registry: Registry
    ) -> None:
        sub1 = Subscription(
            id=uuid4(), group='test_group', key='shared_key', mode=SubscriptionMode.LAST
        )
        sub2 = Subscription(
            id=uuid4(), group='test_group', key='shared_key', mode=SubscriptionMode.LAST
        )

        registry_manager.subscribe(sub1)
        registry_manager.subscribe(sub2)

        kv = registry.batch_start('test_group')
        kv['shared_key'] = 123
        kv.batch_end()

        chunk_update = registry_manager.pop(timeout=0.5)

        assert chunk_update is not None
        key_update = chunk_update.unordered_updates['test_group']['shared_key']
        assert str(sub1.id) in key_update.subscription_ids
        assert str(sub2.id) in key_update.subscription_ids

    def test_concurrent_subscribe_unsubscribe_operations(
        self, registry_manager: RegistryManager
    ) -> None:
        errors = []

        def subscribe_unsubscribe(thread_id: int) -> None:
            try:
                for i in range(10):
                    sub = Subscription(
                        id=uuid4(),
                        group=f'group_{thread_id}',
                        key=f'key_{i}',
                        mode=SubscriptionMode.LAST,
                    )
                    registry_manager.subscribe(sub)
                    time.sleep(0.001)
                    registry_manager.unsubscribe(sub)
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        threads = [
            threading.Thread(target=subscribe_unsubscribe, args=(i,)) for i in range(3)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0

    def test_registry_updates_trigger_callbacks_and_appear_in_pop(
        self, registry_manager: RegistryManager, registry: Registry
    ) -> None:
        sub = Subscription(
            id=uuid4(), group='test_group', key='test_key', mode=SubscriptionMode.LAST
        )
        registry_manager.subscribe(sub)

        kv = registry.batch_start('test_group')
        kv['test_key'] = 'initial'
        kv.batch_end()

        chunk_update = registry_manager.pop(timeout=0.5)
        assert chunk_update is not None
        assert chunk_update.unordered_updates['test_group']['test_key'].val == 'initial'

        kv = registry.batch_start('test_group')
        kv['test_key'] = 'updated'
        kv.batch_end()

        chunk_update = registry_manager.pop(timeout=0.5)
        assert chunk_update is not None
        assert chunk_update.unordered_updates['test_group']['test_key'].val == 'updated'

    def test_sequence_id_ordering_in_updates(
        self, registry_manager: RegistryManager, registry: Registry
    ) -> None:
        sub = Subscription(
            id=uuid4(), group='test_group', key='test_key', mode=SubscriptionMode.LAST
        )
        registry_manager.subscribe(sub)

        kv = registry.batch_start('test_group')
        kv['test_key'] = 1
        kv.batch_end()

        chunk1 = registry_manager.pop(timeout=0.5)
        assert chunk1 is not None
        seq1 = chunk1.unordered_updates['test_group']['test_key'].sequence_id

        kv = registry.batch_start('test_group')
        kv['test_key'] = 2
        kv.batch_end()

        chunk2 = registry_manager.pop(timeout=0.5)
        assert chunk2 is not None
        seq2 = chunk2.unordered_updates['test_group']['test_key'].sequence_id

        assert seq2 > seq1

    def test_external_registry_writes_appear_in_pop(
        self, registry_manager: RegistryManager, registry: Registry
    ) -> None:
        sub = Subscription(
            id=uuid4(), group='test_group', key='test_key', mode=SubscriptionMode.LAST
        )
        registry_manager.subscribe(sub)

        kv = registry.batch_start('test_group')
        kv['test_key'] = 'external_write'
        kv.batch_end()

        chunk_update = registry_manager.pop(timeout=0.5)

        assert chunk_update is not None
        assert (
            chunk_update.unordered_updates['test_group']['test_key'].val
            == 'external_write'
        )
