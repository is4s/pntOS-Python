import time
from pathlib import Path
from threading import Event, Lock, Thread

from lcm import LCM, EventLog
from pntos.api import KeyValueStore, LoggingLevel, Mediator, UtilityPlugin
from pntos.cobra.utils import MutableValueView

DISPLAY_UPDATE_INTERVAL_MS = 100
FILE_KEY_DEFAULT_VALUE = 'Choose a file.'


class CobraUiLogPlayerPlugin(UtilityPlugin):
    _mediator: Mediator
    _lcm_url: str
    _group: str
    _file: Path | None
    _file_found: Event
    _log_thread: Thread | None
    _upload_dir: Path
    _play: Event
    _step: Event

    def __init__(
        self,
        identifier: str,
        lcm_url: str = 'tcpq://localhost:7700',
        upload_dir: str = '_static/dist/',
        group: str = 'ui/logplayer',
    ) -> None:
        self.identifier = identifier
        self._lcm_url = lcm_url
        self._group = group
        self._requested_seek_fraction: float | None = None
        self._seek_lock: Lock = Lock()
        self._local_offset: float = 0.0
        self._log_offset: float = 0.0
        self._last_display_time: float = 0.0
        self._last_system_time: float = 0.0
        self._channels_seen: set[str] = set()
        self._log_thread = None
        script_dir = Path(__file__).parent.resolve()
        self._upload_dir = script_dir / upload_dir

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        assert mediator is not None
        self._mediator = mediator
        self._shutdown_thread_event = Event()
        self._play = Event()
        self._step = Event()
        self._file_found = Event()
        self._lcm = LCM(self._lcm_url)
        self._initialize_keys()
        self._request_notify_new_file()
        self._request_notify_run_thread()
        self._speed: MutableValueView[float] = MutableValueView(
            self._mediator.registry, self._group, 'requested_speed', float
        )
        self._speed.set_value(1.0)

    def _run(self) -> None:  # noqa: PLR0915
        self._info('Started logplayer thread')
        assert self._event_log is not None

        last_speed = None
        last_position_fraction = 0.0
        last_event_time = 0.0

        try:
            while not self._shutdown_thread_event.is_set():
                self._play.wait(0.5)
                if not self._play.is_set():
                    continue

                with self._seek_lock:
                    if self._requested_seek_fraction is not None:
                        seek_pos = int(
                            self._requested_seek_fraction * self._event_log.size()
                        )
                        self._event_log.seek(seek_pos)
                        self._requested_seek_fraction = None
                        self._log_offset = 0.0
                        self._local_offset = 0.0

                last_position_fraction = self._event_log.tell() / self._event_log.size()

                try:
                    event = self._event_log.next()
                except StopIteration:
                    self._info(f'EOF for {self._file}')
                    break

                current_speed = self._speed.value or 0.0
                if current_speed != last_speed:
                    self._log_offset = event.timestamp
                    self._local_offset = time.perf_counter() * 1_000_000
                    last_speed = current_speed

                log_relative_time = event.timestamp - self._log_offset
                clock_relative_time = (
                    time.perf_counter() * 1_000_000 - self._local_offset
                )

                speed_scale = max(1, current_speed * 1024.0)
                wait_time_us = (
                    1024 * log_relative_time / speed_scale
                ) - clock_relative_time
                wait_time_ms = max(0, wait_time_us / 1000)

                while wait_time_ms > 0:
                    if self._shutdown_thread_event.is_set():
                        return

                    if self._step.is_set():
                        kv = self._mediator.registry.batch_start(self._group)
                        kv['step'] = False
                        kv.batch_end()
                        self._step.clear()
                        self._play.clear()
                        should_continue = False
                    elif not self._play.is_set():
                        should_continue = False
                    else:
                        should_continue = True

                    if not should_continue:
                        seek_pos = int(last_position_fraction * self._event_log.size())
                        self._event_log.seek(seek_pos)
                        break

                    chunk = min(wait_time_ms, 50)
                    time.sleep(chunk / 1000)
                    wait_time_ms -= chunk

                if self._shutdown_thread_event.is_set():
                    return

                if not (self._play.is_set() or self._step.is_set()):
                    seek_pos = int(last_position_fraction * self._event_log.size())
                    self._event_log.seek(seek_pos)
                    continue

                self._lcm.publish(event.channel, event.data)

                if event.channel not in self._channels_seen:
                    self._channels_seen.add(event.channel)
                    kv = self._mediator.registry.batch_start(self._group)
                    kv['channels'] = list(self._channels_seen)
                    kv.batch_end()
                current_time_ms = time.perf_counter() * 1000
                dt = current_time_ms - self._last_display_time
                if dt > DISPLAY_UPDATE_INTERVAL_MS:
                    position_fraction = self._event_log.tell() / self._event_log.size()
                    self._last_display_time = current_time_ms
                    kv = self._mediator.registry.batch_start(self._group)
                    kv['n_messages'] = event.eventnum
                    kv['fraction_through_file'] = position_fraction
                    kv['time'] = event.timestamp
                    kv['actual_speed'] = (
                        (log_relative_time - last_event_time) / 1_000_000 / (dt / 1000)
                    )
                    last_event_time = log_relative_time
                    kv.batch_end()

                if self._step.is_set():
                    kv = self._mediator.registry.batch_start(self._group)
                    kv['step'] = False
                    kv.batch_end()
                    self._step.clear()
                    self._play.clear()

        except Exception as e:  # noqa: BLE001
            self._warn(str(e))

    def _request_notify_new_file(self) -> None:
        kv = self._mediator.registry.batch_start(self._group)
        kv.request_notify('file', self._load_callback)
        kv.batch_end()

    def _remove_notify_new_file(self) -> None:
        kv = self._mediator.registry.batch_start(self._group)
        kv.remove_notify('file', self._load_callback)
        kv.batch_end()

    def _initialize_keys(self) -> None:
        kv = self._mediator.registry.batch_start(self._group)
        kv['playing'] = False
        kv['step'] = False
        kv['file'] = FILE_KEY_DEFAULT_VALUE
        kv.batch_end()

    def _request_notify_run_thread(self) -> None:
        kv = self._mediator.registry.batch_start(self._group)
        kv.request_notify('playing', self._play_pause_callback)
        kv.request_notify('step', self._step_callback)
        kv.batch_end()

    def _remove_notify_run_thread(self) -> None:
        kv = self._mediator.registry.batch_start(self._group)
        kv.remove_notify('playing', self._play_pause_callback)
        kv.remove_notify('step', self._step_callback)
        kv.batch_end()

    def _play_pause_callback(
        self, group: str, keys: list[str], kv: KeyValueStore
    ) -> None:
        self._info(f'Playing: {kv["playing"]}')
        if kv['playing']:
            self._play.set()
            return
        self._play.clear()

    def _load_callback(self, group: str, keys: list[str], kv: KeyValueStore) -> None:
        self._info('Loading file...')
        file = kv.get_value('file', str)
        if not file:
            self._mediator.log_message(
                LoggingLevel.WARN, f'No file at (group, key): ({group}, file)...'
            )
            return
        if file == FILE_KEY_DEFAULT_VALUE:
            return
        self._shutdown_current_thread()
        path = self._upload_dir / file
        if not path.exists():
            self._mediator.log_message(
                LoggingLevel.WARN, f'Unable to find file {file} - cannot open.'
            )
            return
        self._file = path
        try:
            self._event_log = EventLog(self._file)
        except FileNotFoundError:
            self._mediator.log_message(LoggingLevel.WARN, f'Could not open "{path}"')
        self._log_thread = Thread(
            target=self._run,
        )
        self._log_thread.start()

    def _step_callback(self, group: str, keys: list[str], kv: KeyValueStore) -> None:
        if self._step.is_set():
            return
        self._step.set()
        self._play.set()

    def _shutdown_current_thread(self) -> None:
        if self._log_thread is not None:
            self._shutdown_thread_event.set()
            try:
                self._log_thread.join(timeout=1)
            except TimeoutError:
                self._mediator.log_message(
                    LoggingLevel.WARN, 'Having trouble shuting down'
                )

    def shutdown_plugin(self) -> None:
        self._remove_notify_new_file()
        self._remove_notify_run_thread()
        self._shutdown_current_thread()

    def _info(self, message: str) -> None:
        """Log info message."""
        self._mediator.log_message(LoggingLevel.INFO, message)

    def _warn(self, message: str) -> None:
        """Log warning message."""
        self._mediator.log_message(LoggingLevel.WARN, message)

    def _debug(self, message: str) -> None:
        """Log debug message."""
        self._mediator.log_message(LoggingLevel.DEBUG, message)

    def _error(self, message: str) -> None:
        """Log error message."""
        self._mediator.log_message(LoggingLevel.ERROR, message)
