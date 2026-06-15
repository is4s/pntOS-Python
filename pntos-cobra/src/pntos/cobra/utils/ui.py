import pickle
from threading import Lock, Thread, Timer
from time import time
from typing import Protocol, TypeGuard, runtime_checkable

import numpy as np
from aspn23 import (
    AspnBase,
    TypeTimestamp,
)

from pntos.api import Message, Registry

from .registry import GroupsView, MutableValueView, ValueView

# Channels each have their own group of format: `UI_CHANNEL_GROUP_PREFIX/{channel}`
UI_GROUP_CHANNEL_PREFIX = 'ui/channel/'
# Keys in `UI_CHANNEL_GROUP_PREFIX/{channel}` group:
UI_GROUP_CHANNEL_KEY_ENABLED_MEDIATOR_BOOL = 'enabled_mediator'
UI_GROUP_CHANNEL_KEY_ENABLED_SOURCE_BOOL = 'enabled_source'
UI_GROUP_CHANNEL_KEY_MESSAGE_COUNT_INT = 'message_count'
UI_GROUP_CHANNEL_KEY_RATE_FLOAT = 'rate'
UI_GROUP_CHANNEL_KEY_TYPE_STR = 'type'
UI_GROUP_CHANNEL_KEY_JITTER_FLOAT = 'jitter'
UI_GROUP_CHANNEL_KEY_BANDWIDTH_FLOAT = 'bandwidth'
UI_GROUP_CHANNEL_KEY_TOV_LAST_MESSAGE_INT = 'tov_last_message'


# Solutions each have their own group of format: `UI_GROUP_SOLUTION_PREFIX/{filter_description}`
UI_GROUP_SOLUTION_PREFIX = 'ui/solution/'
# numpy array of [t, x, y, z, vx, vy, vz, r, p, y]
UI_GROUP_SOLUTION_KEY_SOLUTION = 'solution'
UI_GROUP_SOLUTION_KEY_SOLUTION_COVARIANCE = (
    'solution_covariance'  # 9x9 numpy covariance matrix
)
UI_GROUP_SOLUTION_KEY_REQUESTED_TIME = 'solution_requested_time'

# A group for ui metadata (e.g. a list of all groups)
UI_GROUP_METADATA = 'ui/metadata'
# Keys in `UI_GROUP_METADATA` group:
UI_GROUP_METADATA_KEY_GROUPS_LIST = 'groups'


class UiMetadataInterface(GroupsView):
    """Utility object to populate the keys in the ``UI_GROUP_METADATA`` group."""

    def __init__(self, registry: Registry) -> None:
        self._groups_view = MutableValueView(
            registry, UI_GROUP_METADATA, UI_GROUP_METADATA_KEY_GROUPS_LIST, list
        )
        super().__init__(registry)
        if self._groups is not None:
            self._groups_view.set_value(self._groups)

    def _callback(self, new_group: str) -> None:
        super()._callback(new_group)
        if self._groups is None:
            return
        Thread(
            target=self._groups_view.set_value, args=(list(self._groups),), daemon=True
        ).start()


@runtime_checkable
class AspnBaseWithTOV(AspnBase, Protocol):
    time_of_validity: TypeTimestamp


def has_tov(measurement: AspnBase) -> TypeGuard[AspnBaseWithTOV]:
    return hasattr(measurement, 'time_of_validity')


class ChannelView:
    """
    Utility object to track all registry <-> UI interactions for a single channel.
    """

    def __init__(
        self, registry: Registry, channel: str, update_interval: float
    ) -> None:
        self._registry: Registry = registry
        self._channel: str = channel
        self._group: str = UI_GROUP_CHANNEL_PREFIX + channel
        self._update_interval: float = update_interval

        # Default values
        with self._registry.batch_start(self._group) as kv:
            if UI_GROUP_CHANNEL_KEY_ENABLED_MEDIATOR_BOOL not in kv:
                kv[UI_GROUP_CHANNEL_KEY_ENABLED_MEDIATOR_BOOL] = True
            if UI_GROUP_CHANNEL_KEY_MESSAGE_COUNT_INT not in kv:
                kv[UI_GROUP_CHANNEL_KEY_MESSAGE_COUNT_INT] = 0
            if UI_GROUP_CHANNEL_KEY_RATE_FLOAT not in kv:
                kv[UI_GROUP_CHANNEL_KEY_RATE_FLOAT] = 0.0
            if UI_GROUP_CHANNEL_KEY_TYPE_STR not in kv:
                kv[UI_GROUP_CHANNEL_KEY_TYPE_STR] = 'Unknown'
            if UI_GROUP_CHANNEL_KEY_JITTER_FLOAT not in kv:
                kv[UI_GROUP_CHANNEL_KEY_JITTER_FLOAT] = 0.0
            if UI_GROUP_CHANNEL_KEY_BANDWIDTH_FLOAT not in kv:
                kv[UI_GROUP_CHANNEL_KEY_BANDWIDTH_FLOAT] = 0.0
            if UI_GROUP_CHANNEL_KEY_TOV_LAST_MESSAGE_INT not in kv:
                kv[UI_GROUP_CHANNEL_KEY_TOV_LAST_MESSAGE_INT] = 0

        # Value views
        self._mediator_enabled: ValueView[bool] = ValueView(
            self._registry,
            self._group,
            UI_GROUP_CHANNEL_KEY_ENABLED_MEDIATOR_BOOL,
            bool,
        )
        self._source_enabled: ValueView[bool] = ValueView(
            self._registry,
            self._group,
            UI_GROUP_CHANNEL_KEY_ENABLED_SOURCE_BOOL,
            bool,
        )
        self._message_count: MutableValueView[int] = MutableValueView(
            self._registry, self._group, UI_GROUP_CHANNEL_KEY_MESSAGE_COUNT_INT, int
        )
        self._rate: MutableValueView[float] = MutableValueView(
            self._registry, self._group, UI_GROUP_CHANNEL_KEY_RATE_FLOAT, float
        )
        self._type: MutableValueView[str] = MutableValueView(
            self._registry, self._group, UI_GROUP_CHANNEL_KEY_TYPE_STR, str
        )
        self._jitter: MutableValueView[float] = MutableValueView(
            self._registry, self._group, UI_GROUP_CHANNEL_KEY_JITTER_FLOAT, float
        )
        self._tov_last_message: MutableValueView[int] = MutableValueView(
            self._registry, self._group, UI_GROUP_CHANNEL_KEY_TOV_LAST_MESSAGE_INT, int
        )
        self._bandwidth: MutableValueView[float] = MutableValueView(
            self._registry, self._group, UI_GROUP_CHANNEL_KEY_BANDWIDTH_FLOAT, float
        )
        self._message: MutableValueView[Message] = MutableValueView(
            self._registry, self._group, 'message', Message
        )

        # Buffer/update variables
        self._update_timer: Timer | None = None
        self._messages_since: int = 0
        self._t_last_update: float = time()
        self._last_message: Message | None = None
        self._times: list[float] = []
        self._update_lock: Lock = Lock()

    def update_channel_info(self, message: Message) -> None:
        """Thread-safe function for the mediator to update this channel."""
        with self._update_lock:
            # Update local values between updates
            self._messages_since += 1
            self._last_message = message
            if has_tov(message.wrapped_message):
                self._times.append(
                    message.wrapped_message.time_of_validity.elapsed_nsec / 1e9
                )

        # Handle timer
        if self._update_timer is not None and self._update_timer.is_alive():
            # We have previously updated and are waiting for the next update
            return
        if (
            self._update_timer is None  # First message on this channel, or...
            or (time() - self._t_last_update) > self._update_interval  # Been awhile
        ):
            self._update_channel_info()
        self._update_timer = Timer(
            interval=self._update_interval, function=self._update_channel_info
        )
        self._update_timer.daemon = True
        self._update_timer.start()

    def _update_channel_info(self) -> None:
        """Performs actual channel info registry update."""
        # Grab and reset the current buffer values
        with self._update_lock:
            last_message = self._last_message
            # Check if previous timer already fired for this message - don't want to
            # double-write messages.
            if last_message is None:
                return
            self._last_message = None
            n_new_messages = self._messages_since
            self._messages_since = 0
            t_last = self._t_last_update
            t_now = time()
            self._t_last_update = t_now
            times = np.array(self._times, dtype=np.float64)
            self._times = []

        # Calculations
        dt = t_now - t_last
        # Bandwidth: assume all messages are the same pickled size
        size = len(pickle.dumps(last_message))
        bandwidth = n_new_messages * size / dt
        rate = n_new_messages / dt
        tov_last_message = int(times[-1]) if times.size > 0 else 0
        type_str = type(last_message.wrapped_message).__name__
        jitter: float = round(times.std(), 9) if times.size > 0 else 0.0

        # Update registry
        with self._registry.batch_start(self._group) as kv:
            self._message_count.set_value(
                (self._message_count.value or 0) + n_new_messages, kv
            )
            self._bandwidth.set_value(bandwidth, kv)
            self._rate.set_value(rate, kv)
            self._tov_last_message.set_value(tov_last_message, kv)
            self._type.set_value(type_str, kv)
            self._jitter.set_value(jitter, kv)
            self._message.set_value(last_message, kv)

    @property
    def channel(self) -> str:
        """The channel for which this object is a view."""
        return self._channel

    @property
    def group(self) -> str:
        """The group in the registry that contains the metadata for this channel."""
        return self._group

    @property
    def mediator_enabled(self) -> bool:
        """False if UI requests that mediator block this channel, else True."""
        val = self._mediator_enabled.value
        return val if val is not None else True

    @property
    def source_enabled(self) -> bool:
        """False if UI requests that sources block this channel, else True."""
        val = self._source_enabled.value
        return val if val is not None else True

    @property
    def message_count(self) -> int:
        """The most recent message count on this channel."""
        return self._message_count.value or 0

    @property
    def rate(self) -> float:
        """The most recent measured messages/second on this channel."""
        return self._rate.value or 0.0

    @property
    def type(self) -> str:
        """The most recent measurement type as a string on this channel."""
        return self._type.value or 'Unknown'

    @property
    def jitter(self) -> float:
        """The most recent measured timestamp jitter in seconds on this channel."""
        return self._jitter.value or 0.0

    @property
    def tov_last_message(self) -> int:
        """The most recent time of validity in elapsed nano-seconds on this channel."""
        return self._tov_last_message.value or 0

    @property
    def bandwidth(self) -> float:
        """The most recent bandwidth value in bytes per second on this channel."""
        return self._bandwidth.value or 0.0


class UiMediatorInterface:
    """
    Interface between a ``pntos.api.Mediator`` and the UI via the registry.
    """

    _channels: dict[str, ChannelView]

    def __init__(self, registry: Registry, update_interval: float = 0.5) -> None:
        """
        Args:
            registry (Registry): Registry reference for UI communications.
            update_interval (float): Minimum time in seconds between UI updates
                per-channel. Small intervals could incur performance degradation.
                Default is 0.1 seconds.
        """
        self._registry: Registry = registry
        self._update_interval = update_interval
        self._channels = {}

    def _ensure_channel_view(self, channel: str) -> ChannelView:
        """Gets the ``ChannelView`` for a given channel, creating one if necessary."""
        if channel not in self._channels:
            self._channels[channel] = ChannelView(
                self._registry, channel, self._update_interval
            )
        return self._channels[channel]

    def new_mediator_message(self, message: Message) -> bool:
        """
        Update the UI with a new message from the mediator.

        It is up to the controller/mediator implementation to decide what a "new"
        message means as pertains to buffering messages. It could be that "new" refers
        to messages from ``process_pntos_message()`` calls, or it could be post-buffer
        messages, or some combination.

        Args:
            message (Message): The message from the Mediator.

        Returns:
            bool: False if UI user requests that the mediator block this source ID, else
                True.
        """
        cv = self._ensure_channel_view(message.source_identifier)
        cv.update_channel_info(message)
        return cv.mediator_enabled


class SourceChannelView:
    """
    A Utility object to track registry <-> UI interactions for a source channel.
    """

    def __init__(self, registry: Registry, channel: str) -> None:
        self._registry: Registry = registry
        self._channel: str = channel
        self._group: str = UI_GROUP_CHANNEL_PREFIX + channel
        with self._registry.batch_start(self._group) as kv:
            if UI_GROUP_CHANNEL_KEY_ENABLED_SOURCE_BOOL not in kv:
                kv[UI_GROUP_CHANNEL_KEY_ENABLED_SOURCE_BOOL] = True

        self._source_enabled: ValueView[bool] = ValueView(
            self._registry,
            self._group,
            UI_GROUP_CHANNEL_KEY_ENABLED_SOURCE_BOOL,
            bool,
        )

    @property
    def channel(self) -> str:
        """The channel for which this object is a view."""
        return self._channel

    @property
    def group(self) -> str:
        """The group in the registry that contains the metadata for this channel."""
        return self._group

    @property
    def source_enabled(self) -> bool:
        """False if UI requests that sources block this channel, else True."""
        val = self._source_enabled.value
        return val if val is not None else True


class UiSourceInterface:
    """
    Interface between a source (e.g. ``pntos.api.TransportPlugin``) and the UI via the
    registry.
    """

    _channels: dict[str, SourceChannelView]

    def __init__(self, registry: Registry) -> None:
        """
        Args:
            registry (Registry): Registry reference for UI communications.
        """
        self._registry: Registry = registry
        self._channels = {}

    def _ensure_channel_view(self, channel: str) -> SourceChannelView:
        """Gets the ``SourceChannelView`` for a given channel, creating one if necessary."""
        if channel not in self._channels:
            self._channels[channel] = SourceChannelView(self._registry, channel)
        return self._channels[channel]

    def new_message(self, source_identifier: str) -> bool:
        """
        Update the UI with a new message from this source.

        A source (e.g. TransportPlugin) should call this method on it's
        ``UiSourceInterface`` as soon as it has a ``source_identifier``. Note that
        the source is not required to provide a whole ``pntos.api.Message``. This
        provides for some potential performance gains - when the user wishes to block
        this source ID, the source does not need to allocate and populate a whole
        ``pntos.api.Message``.

        Args:
            source_identifier (str): The source ID of the new message.

        Returns:
            bool: False if UI user requests that the source block this source ID, else
                True.
        """
        return self._ensure_channel_view(source_identifier).source_enabled
