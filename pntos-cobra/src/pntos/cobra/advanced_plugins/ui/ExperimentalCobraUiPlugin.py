"""
Cobra UI Plugin for pntOS.

Main plugin implementation providing Flask/SocketIO-based WebSocket API
for real-time registry updates and subscriptions.
"""

import shutil
from importlib.resources import files
from logging import ERROR, getLogger
from pathlib import Path
from threading import Event, Thread
from time import sleep, time  # noqa: F401
from typing import Literal

from engineio.payload import Payload
from flask import Flask, Response, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from pntos.api import LoggingLevel, Mediator, UiPlugin
from pntos.cobra.config import ExperimentalCobraUiConfig, config_from_registry
from pntos.cobra.utils import UiMetadataInterface
from typing_extensions import Unpack
from werkzeug.exceptions import NotFound
from werkzeug.utils import secure_filename

from .models import ChunkUpdate, Snapshot, Subscription, Write
from .utils import RegistryManager, SequenceBuffer

# Resolves #361 for now
Payload.max_decode_packets = 500


class ExperimentalCobraUiPlugin(UiPlugin):
    """
    Flask/SocketIO-based UI plugin for pntOS.

    Provides WebSocket API for:
    - Real-time registry subscriptions
    - Snapshot retrieval
    - Update notifications
    """

    mediator: Mediator
    registry_manager: RegistryManager
    identifier: str
    _shutdown_event: Event
    app: Flask
    socket: SocketIO
    config: ExperimentalCobraUiConfig
    config_group: str
    write_buffer: SequenceBuffer[Write]
    _metadata_manager: UiMetadataInterface
    static_folder: Path

    def __init__(
        self,
        identifier: str,
        config_group: str = 'config/cobra_ui',
    ) -> None:
        self.identifier = identifier
        self.config_group = config_group
        self.write_buffer = SequenceBuffer(key=lambda x: x.sequence_id)
        self._shutdown_event = Event()
        self._server_thread: Thread | None = None
        self._emitter_thread: Thread | None = None

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        assert mediator is not None
        self.mediator = mediator
        self._metadata_manager = UiMetadataInterface(self.mediator.registry)
        self.registry_manager = RegistryManager(self.mediator)

        config = config_from_registry(
            ExperimentalCobraUiConfig, self.mediator, self.config_group
        )
        if config is None:
            self._error('Config from registry failed.')
            return
        self.config = config
        if config.static_folder:
            self.static_folder = Path(config.static_folder)
        else:
            self.static_folder = files('pntos.cobra').joinpath(  # type: ignore[call-arg, assignment]
                'advanced_plugins', 'ui', '_static', 'dist'
            )

        werkz_logger = getLogger('werkzeug')
        werkz_logger.setLevel(ERROR)
        if not self._runtime_assets_exist(self.static_folder):
            self._error(
                f'Cannot find front-end runtime assets at {self.static_folder.resolve().as_posix()}. '
                'Runtime assets must be built prior to using the ExperimentalCobraUiPlugin.'
            )
            return
        self.app = Flask(__name__, static_folder=self.static_folder.resolve())
        self._route_app()
        self.socket = SocketIO(
            self.app,
            cors_allowed_origins=list(self.config.cors_allowed_origins),
            logger=False,
            engineio_logger=False,
            async_mode='threading',
        )
        self._route_socket()
        self._registry_updates_thread = Thread(
            target=self._run_registry_updates_thread, daemon=True
        )
        self._registry_updates_thread.start()
        self._server_thread = Thread(target=self._run_server_thread, daemon=True)
        self._server_thread.start()
        self._info(
            f'Web server starting on http://{self.config.host}:{self.config.port}'
        )

    def shutdown_plugin(self) -> None:
        self._info('Shutting down web server...')

        self._shutdown_event.set()

        self.registry_manager.shutdown()

        self._info('Web server shut down complete.')

    def requires_main_thread(self) -> bool:
        # TODO: enable setting config and holding until set
        return False

    def run_main_thread(self) -> None:
        pass

    def _runtime_assets_exist(self, static_folder: Path) -> bool:
        return static_folder.exists() and any(static_folder.iterdir())

    def _run_registry_updates_thread(self) -> None:
        """Pops changes from the registry manager and puts them in the send queue."""
        while not self._shutdown_event.is_set():
            update = self.registry_manager.pop(0.5)
            if update is None:
                continue
            self.socket.emit('chunkUpdate', update.model_dump())

    def _run_server_thread(self) -> None:
        """Run the Flask-SocketIO server in a background thread."""
        try:
            self.socket.run(
                self.app,
                host=self.config.host,
                port=self.config.port,
                debug=False,
                allow_unsafe_werkzeug=True,
                use_reloader=False,
            )
        except KeyboardInterrupt:
            return
        except Exception as e:  # noqa: BLE001
            self._error(f'Server thread error: {e}')

    def _route_app(self) -> None:
        @self.app.route('/')
        def serve_index() -> Response:
            if self.app.static_folder is None:
                return Response('No static folder')
            return send_from_directory(self.app.static_folder, 'index.html')

        @self.app.route('/<path:path>')
        def serve_static_or_index(path: str) -> Response:
            if self.app.static_folder is None:
                return Response('No static folder')
            try:
                return send_from_directory(self.app.static_folder, path)
            except (FileNotFoundError, NotFound):
                return send_from_directory(self.app.static_folder, 'index.html')

        @self.app.post('/upload')
        def upload() -> (
            tuple[Response, Literal[400]]
            | tuple[Response, Literal[200]]
            | tuple[Response, Literal[500]]
        ):
            try:
                if 'file' not in request.files:
                    return jsonify(error='No file provided'), 400

                file = request.files['file']
                if not file or not file.filename:
                    return jsonify(error='Invalid file'), 400

                uploads_dir = Path(self.static_folder) / 'uploads'
                uploads_dir.mkdir(parents=True, exist_ok=True)

                filename = secure_filename(file.filename)
                save_path = uploads_dir / filename

                with save_path.open('wb') as buffer:
                    shutil.copyfileobj(file.stream, buffer)

                relative_path = f'uploads/{filename}'
                self._info(f'Uploaded: {save_path}')

                return jsonify(path=relative_path), 200
            except Exception as e:  # noqa: BLE001
                self._error(f'Upload error: {e}')
                return jsonify(error=f'Upload failed: {e!s}'), 500

    def _route_socket(self) -> None:
        """Set up WebSocket event handlers."""

        @self.socket.on('connect')  # type: ignore[misc]
        def handle_connect(connection: None) -> None:
            emit('snapshot', self.registry_manager.snapshot().model_dump())

        @self.socket.event  # type: ignore[misc]
        def subscribe(subscription_json: Unpack[Subscription]) -> None:  # type: ignore[valid-type]
            subscription = Subscription.model_validate(subscription_json)
            self.registry_manager.subscribe(subscription)
            initial_value = self.registry_manager.get_current_value(
                subscription.group, subscription.key
            )
            if initial_value is not None:
                emit(
                    'chunkUpdate',
                    ChunkUpdate(
                        ordered_updates=[],
                        unordered_updates={subscription.group: initial_value},
                    ).model_dump(),
                )

        @self.socket.event  # type: ignore[misc]
        def unsubscribe(subscription_json: Unpack[Subscription]) -> None:  # type: ignore[valid-type]
            subscription = Subscription.model_validate(subscription_json)
            self.registry_manager.unsubscribe(subscription)

        @self.socket.event  # type: ignore[misc]
        def write(write_request_dict: Unpack[Write]) -> None:  # type: ignore[valid-type]
            write_request = Write.model_validate(write_request_dict)
            for write in self.write_buffer.add(write_request):
                self.registry_manager.write(write)

        @self.socket.event  # type: ignore[misc]
        def snapshot() -> Snapshot:
            return self.registry_manager.snapshot()

    def _info(self, message: str) -> None:
        """Log info message."""
        self.mediator.log_message(LoggingLevel.INFO, message)

    def _warn(self, message: str) -> None:
        """Log warning message."""
        self.mediator.log_message(LoggingLevel.WARN, message)

    def _debug(self, message: str) -> None:
        """Log debug message."""
        self.mediator.log_message(LoggingLevel.DEBUG, message)

    def _error(self, message: str) -> None:
        """Log error message."""
        self.mediator.log_message(LoggingLevel.ERROR, message)
