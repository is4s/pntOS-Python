import tempfile
from collections.abc import Generator
from io import BytesIO
from pathlib import Path
from threading import Event
from unittest.mock import patch
from uuid import uuid4

import pytest
from flask_socketio import SocketIOTestClient
from pntos.api import Registry
from pntos.cobra.advanced_plugins.ui.ExperimentalCobraUiPlugin import (
    ExperimentalCobraUiPlugin,
)
from pntos.cobra.advanced_plugins.ui.models import Subscription, SubscriptionMode
from pntos.cobra.config import ExperimentalCobraUiConfig
from pntos.cobra.dummy_plugins.DummyMediator import DummyMediator
from pntos.cobra.standard_plugins.StandardRegistryPlugin import StandardRegistryPlugin


@pytest.fixture
def registry_plugin() -> StandardRegistryPlugin:
    plugin = StandardRegistryPlugin('Test CobraUI')
    mediator = DummyMediator()
    plugin.init_plugin(mediator=mediator)
    return plugin


@pytest.fixture
def registry(registry_plugin: StandardRegistryPlugin) -> Registry:
    reg = registry_plugin.new_registry(None)
    DummyMediator.registry = reg
    return reg


@pytest.fixture
def mediator(registry: Registry) -> DummyMediator:
    med = DummyMediator()
    med.registry = registry
    return med


@pytest.fixture
def temp_static_folder() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        static_path = Path(tmpdir) / 'static'
        static_path.mkdir()
        index_file = static_path / 'index.html'
        index_file.write_text('<html><body>Test Index</body></html>')
        test_file = static_path / 'test.txt'
        test_file.write_text('test content')
        yield static_path


@pytest.fixture
def mock_config(temp_static_folder: Path) -> ExperimentalCobraUiConfig:
    import socket

    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()

    return ExperimentalCobraUiConfig(
        group='config/test_cobra_ui',
        static_folder=str(temp_static_folder),
        port=port,
    )


class TestCobraUiPluginAPI:
    """Tests for CobraUiPlugin public API methods."""

    def test_init(self) -> None:
        plugin = ExperimentalCobraUiPlugin('test-plugin', 'config/test')
        assert plugin.identifier == 'test-plugin'
        assert plugin.config_group == 'config/test'
        assert plugin.write_buffer is not None
        assert isinstance(plugin._shutdown_event, Event)
        assert not plugin._shutdown_event.is_set()

    def test_init_default_config_group(self) -> None:
        plugin = ExperimentalCobraUiPlugin('test-plugin')
        assert plugin.identifier == 'test-plugin'
        assert plugin.config_group == 'config/cobra_ui'

    def test_init_plugin(
        self, mediator: DummyMediator, mock_config: ExperimentalCobraUiConfig
    ) -> None:
        plugin = ExperimentalCobraUiPlugin('test-plugin')

        with patch(
            'pntos.cobra.advanced_plugins.ui.ExperimentalCobraUiPlugin.config_from_registry',
            return_value=mock_config,
        ):
            plugin.init_plugin(mediator=mediator)

        assert plugin.mediator is mediator
        assert plugin.registry_manager is not None
        assert plugin.config == mock_config
        assert plugin.app is not None
        assert plugin.socket is not None

    def test_init_plugin_config_failure(self, mediator: DummyMediator) -> None:
        plugin = ExperimentalCobraUiPlugin('test-plugin')

        with patch(
            'pntos.cobra.advanced_plugins.ui.ExperimentalCobraUiPlugin.config_from_registry',
            return_value=None,
        ):
            plugin.init_plugin(mediator=mediator)

        assert not hasattr(plugin, 'app')

    def test_shutdown_plugin(
        self, mediator: DummyMediator, mock_config: ExperimentalCobraUiConfig
    ) -> None:
        plugin = ExperimentalCobraUiPlugin('test-plugin')

        with patch(
            'pntos.cobra.advanced_plugins.ui.ExperimentalCobraUiPlugin.config_from_registry',
            return_value=mock_config,
        ):
            plugin.init_plugin(mediator=mediator)

        assert not plugin._shutdown_event.is_set()
        plugin.shutdown_plugin()
        assert plugin._shutdown_event.is_set()

    def test_requires_main_thread(self) -> None:
        plugin = ExperimentalCobraUiPlugin('test-plugin')
        assert plugin.requires_main_thread() is False

    def test_run_main_thread(self) -> None:
        plugin = ExperimentalCobraUiPlugin('test-plugin')
        plugin.run_main_thread()


class TestCobraUiPluginFlaskRoutes:
    """Tests for CobraUiPlugin Flask HTTP routes."""

    @pytest.fixture
    def initialized_plugin(
        self, mediator: DummyMediator, mock_config: ExperimentalCobraUiConfig
    ) -> Generator[ExperimentalCobraUiPlugin, None, None]:
        plugin = ExperimentalCobraUiPlugin('test-plugin')
        with patch(
            'pntos.cobra.advanced_plugins.ui.ExperimentalCobraUiPlugin.config_from_registry',
            return_value=mock_config,
        ):
            plugin.init_plugin(mediator=mediator)
        yield plugin
        plugin.shutdown_plugin()

    def test_serve_index_success(
        self, initialized_plugin: ExperimentalCobraUiPlugin
    ) -> None:
        with initialized_plugin.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            assert b'Test Index' in response.data

    def test_serve_index_no_static(self, mediator: DummyMediator) -> None:
        plugin = ExperimentalCobraUiPlugin('test-plugin')
        config_no_static = ExperimentalCobraUiConfig(
            group='config/test_cobra_ui',
            static_folder='',
        )
        with patch(
            'pntos.cobra.advanced_plugins.ui.ExperimentalCobraUiPlugin.config_from_registry',
            return_value=config_no_static,
        ):
            plugin.init_plugin(mediator=mediator)
            plugin.app.static_folder = None

        with plugin.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            assert b'No static folder' in response.data

    def test_serve_static_file_exists(
        self, initialized_plugin: ExperimentalCobraUiPlugin
    ) -> None:
        with initialized_plugin.app.test_client() as client:
            response = client.get('/test.txt')
            assert response.status_code == 200
            assert b'test content' in response.data

    def test_serve_static_file_not_exists_fallback(
        self, initialized_plugin: ExperimentalCobraUiPlugin
    ) -> None:
        with initialized_plugin.app.test_client() as client:
            response = client.get('/nonexistent.txt')
            assert response.status_code == 200
            assert b'Test Index' in response.data

    def test_upload_success(
        self, initialized_plugin: ExperimentalCobraUiPlugin, temp_static_folder: Path
    ) -> None:
        with initialized_plugin.app.test_client() as client:
            data = {'file': (BytesIO(b'test file content'), 'test_upload.txt')}
            response = client.post(
                '/upload', data=data, content_type='multipart/form-data'
            )
            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data['path'] == 'uploads/test_upload.txt'

            uploaded_file = temp_static_folder / 'uploads' / 'test_upload.txt'
            assert uploaded_file.exists()
            assert uploaded_file.read_text() == 'test file content'

    def test_upload_no_file(
        self, initialized_plugin: ExperimentalCobraUiPlugin
    ) -> None:
        with initialized_plugin.app.test_client() as client:
            response = client.post(
                '/upload', data={}, content_type='multipart/form-data'
            )
            assert response.status_code == 400
            json_data = response.get_json()
            assert 'error' in json_data
            assert json_data['error'] == 'No file provided'

    def test_upload_invalid_file(
        self, initialized_plugin: ExperimentalCobraUiPlugin
    ) -> None:
        with initialized_plugin.app.test_client() as client:
            data = {'file': (BytesIO(b''), '')}
            response = client.post(
                '/upload', data=data, content_type='multipart/form-data'
            )
            assert response.status_code == 400
            json_data = response.get_json()
            assert 'error' in json_data
            assert json_data['error'] == 'Invalid file'

    def test_upload_exception_handling(
        self, initialized_plugin: ExperimentalCobraUiPlugin
    ) -> None:
        with (
            initialized_plugin.app.test_client() as client,
            patch('shutil.copyfileobj', side_effect=Exception('Test error')),
        ):
            data = {'file': (BytesIO(b'test content'), 'test.txt')}
            response = client.post(
                '/upload', data=data, content_type='multipart/form-data'
            )
            assert response.status_code == 500
            json_data = response.get_json()
            assert 'error' in json_data
            assert 'Upload failed' in json_data['error']


class TestCobraUiPluginSocketRoutes:
    """Tests for CobraUiPlugin SocketIO event handlers."""

    @pytest.fixture
    def initialized_plugin(
        self, mediator: DummyMediator, mock_config: ExperimentalCobraUiConfig
    ) -> Generator[ExperimentalCobraUiPlugin, None, None]:
        plugin = ExperimentalCobraUiPlugin('test-plugin')
        with patch(
            'pntos.cobra.advanced_plugins.ui.ExperimentalCobraUiPlugin.config_from_registry',
            return_value=mock_config,
        ):
            plugin.init_plugin(mediator=mediator)
        yield plugin
        plugin.shutdown_plugin()

    def test_socket_connect_emits_snapshot(
        self, initialized_plugin: ExperimentalCobraUiPlugin, registry: Registry
    ) -> None:
        kv = registry.batch_start('test_group')
        kv['test_key'] = 'test_value'
        kv.batch_end()

        sub = Subscription(
            id=uuid4(),
            group='test_group',
            key='test_key',
            mode=SubscriptionMode.LAST,
        )
        initialized_plugin.registry_manager.subscribe(sub)

        client = SocketIOTestClient(initialized_plugin.app, initialized_plugin.socket)
        client.connect()

        received = client.get_received()
        assert len(received) > 0
        snapshot_event = next((r for r in received if r['name'] == 'snapshot'), None)
        assert snapshot_event is not None
        snapshot_data = snapshot_event['args'][0]
        assert 'data' in snapshot_data
        assert 'test_group' in snapshot_data['data']
        assert snapshot_data['data']['test_group']['test_key'] == 'test_value'

        client.disconnect()

    def test_socket_subscribe_adds_subscription(
        self, initialized_plugin: ExperimentalCobraUiPlugin
    ) -> None:
        client = SocketIOTestClient(initialized_plugin.app, initialized_plugin.socket)
        client.connect()

        sub_id = str(uuid4())
        subscription_data = {
            'id': sub_id,
            'group': 'test_group',
            'key': 'test_key',
            'mode': 'last',
        }

        client.emit('subscribe', subscription_data)

        assert len(initialized_plugin.registry_manager.subscriptions_map) == 1
        sub_uuid = next(
            iter(initialized_plugin.registry_manager.subscriptions_map.keys())
        )
        assert str(sub_uuid) == sub_id

        client.disconnect()

    def test_socket_unsubscribe_removes_subscription(
        self, initialized_plugin: ExperimentalCobraUiPlugin
    ) -> None:
        sub_id = uuid4()
        sub = Subscription(
            id=sub_id,
            group='test_group',
            key='test_key',
            mode=SubscriptionMode.LAST,
        )
        initialized_plugin.registry_manager.subscribe(sub)
        assert sub_id in initialized_plugin.registry_manager.subscriptions_map

        client = SocketIOTestClient(initialized_plugin.app, initialized_plugin.socket)
        client.connect()

        unsubscribe_data = {
            'id': str(sub_id),
            'group': 'test_group',
            'key': 'test_key',
            'mode': 'last',
        }

        client.emit('unsubscribe', unsubscribe_data)
        assert sub_id not in initialized_plugin.registry_manager.subscriptions_map

        client.disconnect()

    def test_socket_writes(
        self, initialized_plugin: ExperimentalCobraUiPlugin, registry: Registry
    ) -> None:
        sub = Subscription(
            id=uuid4(),
            group='test_group',
            key='test_key',
            mode=SubscriptionMode.LAST,
        )
        initialized_plugin.registry_manager.subscribe(sub)

        client = SocketIOTestClient(initialized_plugin.app, initialized_plugin.socket)
        client.connect()

        write_data = {
            'data': {'test_group': {'test_key': 42}},
            'sequence_id': 0,
        }

        client.emit('write', write_data)

        kv = registry.batch_start('test_group')
        assert kv['test_key'] == 42
        kv.batch_end()

        client.disconnect()

    def test_socket_snapshot_returns_snapshot(
        self, initialized_plugin: ExperimentalCobraUiPlugin, registry: Registry
    ) -> None:
        kv = registry.batch_start('test_group')
        kv['key1'] = 100
        kv['key2'] = 'hello'
        kv.batch_end()

        sub1 = Subscription(
            id=uuid4(),
            group='test_group',
            key='key1',
            mode=SubscriptionMode.LAST,
        )
        sub2 = Subscription(
            id=uuid4(),
            group='test_group',
            key='key2',
            mode=SubscriptionMode.LAST,
        )
        initialized_plugin.registry_manager.subscribe(sub1)
        initialized_plugin.registry_manager.subscribe(sub2)

        client = SocketIOTestClient(initialized_plugin.app, initialized_plugin.socket)
        client.connect()

        client.emit('snapshot')
        received = client.get_received()

        snapshot_response = None
        for event in received:
            if event['name'] == 'snapshot':
                snapshot_response = event['args'][0]
                break

        assert snapshot_response is not None
        assert 'data' in snapshot_response
        assert 'test_group' in snapshot_response['data']
        assert snapshot_response['data']['test_group']['key1'] == 100
        assert snapshot_response['data']['test_group']['key2'] == 'hello'

        client.disconnect()

    def test_socket_write_out_of_order_buffering(
        self, initialized_plugin: ExperimentalCobraUiPlugin, registry: Registry
    ) -> None:
        import time

        sub = Subscription(
            id=uuid4(),
            group='test_group',
            key='test_key',
            mode=SubscriptionMode.LAST,
        )
        initialized_plugin.registry_manager.subscribe(sub)

        client = SocketIOTestClient(initialized_plugin.app, initialized_plugin.socket)
        client.connect()

        write_data_2 = {
            'data': {'test_group': {'test_key': 200}},
            'sequence_id': 2,
        }
        client.emit('write', write_data_2)
        time.sleep(0.01)

        kv = registry.batch_start('test_group')
        assert 'test_key' not in kv
        kv.batch_end()

        write_data_1 = {
            'data': {'test_group': {'test_key': 100}},
            'sequence_id': 1,
        }
        client.emit('write', write_data_1)
        time.sleep(0.01)

        kv = registry.batch_start('test_group')
        assert 'test_key' not in kv
        kv.batch_end()

        write_data_0 = {
            'data': {'test_group': {'test_key': 42}},
            'sequence_id': 0,
        }
        client.emit('write', write_data_0)
        time.sleep(0.05)

        kv = registry.batch_start('test_group')
        assert kv['test_key'] == 200
        kv.batch_end()

        client.disconnect()
