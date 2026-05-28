import re
from collections.abc import Callable
from pathlib import Path
from site import getsitepackages
from subprocess import PIPE, Popen

import aspn23
from aspn23_lcm import (
    AspnMsg as Aspn23Msg,
    LcmMsg as Aspn23LcmMsg,
    from_lcm_map as marshaler_from_aspn23_lcm,
    to_lcm_map as marshaler_to_aspn23_lcm,
)

from pntos.api import LoggingLevel, Mediator, Message

from .apps import kill, monitor_app_output, run_app

Aspn23MeasurementExtended = (
    Aspn23Msg
    | list[aspn23.MeasurementDeltaRangeToPoint]
    | list[aspn23.MeasurementRangeRateToPoint]
    | list[aspn23.MeasurementRangeToPoint]
    | list[aspn23.MeasurementTdoa1Tx2Rx]
)

# dictionary mapping LCM message fingerprint to message decode function
decoder: dict[bytes, Callable[[bytes], Aspn23LcmMsg]] = {}
for aspn_type in marshaler_from_aspn23_lcm:
    decoder[aspn_type._get_packed_fingerprint()] = aspn_type.decode


def decode_aspn_lcm_msg(
    data: bytes,
) -> Aspn23LcmMsg | None:
    """
    Decodes a set of bytes into an ASPN-LCM message. Uses the first 8 bytes to determine the type of message,
    if the type cannot be determined this function will return ``None``.

    Args:
        data (bytes): The set of bytes to decode.

    Returns:
        Aspn23LcmMsg | None
    """
    fingerprint = data[:8]

    if fingerprint not in decoder:
        return None

    decode_func = decoder[fingerprint]
    return decode_func(data)


def marshal_from_lcm(
    msg: Aspn23LcmMsg,
) -> Aspn23MeasurementExtended | None:
    """
    Converts from ASPN-LCM message to ASPN23 message. If the input message cannot be converted,
    this function will return ``None``.

    Args:
        msg (``Aspn23LcmMsg``): The message to convert.

    Returns:
        Aspn23Msg | None
    """
    msg_type = type(msg)

    if msg_type not in marshaler_from_aspn23_lcm:
        return None

    marshal_func = marshaler_from_aspn23_lcm[msg_type]
    return marshal_func(msg)  # type: ignore[no-any-return]


def marshal_to_aspn23_lcm(msg: aspn23.AspnBase) -> Aspn23LcmMsg | None:
    """
    Convert from ASPN23 message to ASPN23-LCM message. If the input message cannot be converted,
    this function will return ``None``.

    Args:
        msg (AspnBase): The message to convert.

    Returns:
        Aspn23LcmMsg | None
    """
    msg_type = type(msg)

    if msg_type not in marshaler_to_aspn23_lcm:
        return None

    marshal_func = marshaler_to_aspn23_lcm[msg_type]  # type: ignore[index]
    return marshal_func(msg)  # type: ignore[no-any-return]


def process_lcm_message(
    mediator: Mediator, channel: str, data: bytes, channels: set[str]
) -> None:
    """
    Marshal LCM message to ASPN-Python and send to the mediator for processing.

    Args:
        mediator (Mediator): Mediator instance used for logging and processing message.
        channel (str): The channel name the data originates from.
        data (bytes): A message represented in binary.
        channels (set[str]): Set of channels found so far.
    """
    # Do not process messages sent from pntos.
    if 'pntos' in channel:
        mediator.log_message(
            LoggingLevel.DEBUG,
            'pntOS channel message, not processing in ASPN handler.',
        )
        return

    try:
        lcm_aspn_msg = decode_aspn_lcm_msg(data)
    except ValueError as e:
        mediator.log_message(LoggingLevel.WARN, f'Failed to decode lcm message: {e}')

    if lcm_aspn_msg is None:
        mediator.log_message(
            LoggingLevel.WARN,
            f'Cannot decode message on channel {channel}. Ignoring message.',
        )
        return

    try:
        aspn_msg = marshal_from_lcm(lcm_aspn_msg)
    except ValueError as e:
        mediator.log_message(LoggingLevel.WARN, f'Failed to marshal lcm message: {e}')

    if aspn_msg is None:
        mediator.log_message(
            LoggingLevel.WARN,
            f'Cannot marshal message on channel {channel} of type {type(aspn_msg)}. Ignoring message.',
        )
        return
    if channel not in channels:
        # It is possible for conversions to return a list of Measurements to cover the case
        # where ASPN23 dropped support for multiple obs in 1 message
        ts = (
            aspn_msg[0].time_of_validity.elapsed_nsec / 1e9
            if isinstance(aspn_msg, list)
            else aspn_msg.time_of_validity.elapsed_nsec / 1e9
        )
        mediator.log_message(
            LoggingLevel.INFO,
            f'Found new channel {channel}\t with a timestamp of {ts:.9f}s',
        )
        channels.add(channel)
    if isinstance(aspn_msg, list):
        for am in aspn_msg:
            message = Message(am, channel)
            mediator.process_pntos_message(message)
    else:
        message = Message(aspn_msg, channel)
        mediator.process_pntos_message(message)


def run_tcp_relay() -> Popen[str]:  # pragma: no cover
    sitepackages_dir = Path(getsitepackages()[0])
    print('Starting LCM relay...', flush=True)
    process = Popen(
        [
            'java',
            '-classpath',
            sitepackages_dir / 'share' / 'java' / 'lcm.jar',
            'lcm.lcm.TCPService',
        ],
        text=True,
        stdout=PIPE,
        start_new_session=True,
    )
    # wait until we start seeing output from relay
    process.stdout.readline()  # type: ignore[union-attr]
    return process


def run_logger(output_file: Path) -> Popen[str]:  # pragma: no cover
    # Remove any pre-existing output
    if output_file.exists():
        output_file.unlink()
    current_dir = Path(__file__).parent
    logger_path = current_dir / 'logger.py'
    print('Starting logger...', flush=True)
    return run_app(
        logger_path,
        [output_file.as_posix(), '2584', '/solution/pntos/pva'],
        monitor=True,
    )


def run_lcm_logplayer(logfile: Path) -> Popen[bytes]:  # pragma: no cover
    print('Starting Logplayer...', flush=True)
    return Popen(
        ['lcm-logplayer', '--lcm-url=tcpq://', '--speed=1000', logfile.as_posix()],
        start_new_session=True,
    )


def run_pntos_with_log_transport(
    app: Path,
    args: list[str] | None = None,
    validate: bool = False,
) -> int:  # pragma: no cover
    """Spin up app, process log, then shut down.

    Args:
        app (pathlib.Path): Path to app to run.
        args (list[str] | None): Optional command-line arguments to pass to app (e.g. output log).
        validate (bool): Whether to validate the app's output, ensuring there are no
            warnings or errors. Defaults to False.

    Returns:
        Return code of app. Will be 0 if app ran and terminated successfully.
    """
    # initialize process variables to avoid possibly unbound errors
    app_process = None

    try:
        app_process = run_app(app, args, validate=validate)

        # Wait until pntOS is done processing the LCM log
        done_msg = 'Done processing LCM log. Press Ctrl + C to shut down pntOS.'
        assert app_process.stdout is not None
        monitor_app_output(app_process.stdout, validate=validate, wait_for_msg=done_msg)

        # Continue to forward app output to stdout
        monitor_app_output(app_process.stdout, separate_thread=True)

    finally:
        if app_process is not None:
            kill(app_process)

    return app_process.returncode if app_process else -1


def run_pntos_with_network_transport(
    app: Path,
    input_log: Path,
    output_log: Path,
    args: list[str] | None = None,
    validate: bool = False,
) -> int:  # pragma: no cover
    """Spin up app and network tools necessary to run it, process log, then shut down.

    Args:
        app (pathlib.Path): Path to app to run.
        input_log (pathlib.Path): LCM log containing the measurements to be processed.
        output_log (pathlib.Path): LCM log to which output should be recorded.
        args (list[str] | None): Optional command-line arguments to pass to app.
        validate (bool): Whether to validate the app's output, ensuring there are no
            warnings or errors. Defaults to False.

    Returns:
        Return code of app. Will be 0 if app ran and terminated successfully.
    """

    # initialize process variables to avoid possibly unbound errors
    relay_process = None
    logger_process = None
    logplayer_process = None
    app_process = None
    max_relay_wait_iterations = 10

    try:
        relay_process = run_tcp_relay()
        logger_process = run_logger(output_log)
        print('Starting app...', flush=True)
        app_process = run_app(app, args, monitor=True, validate=validate)

        # wait for cobra to connect to TCP relay
        for i, line in enumerate(relay_process.stdout):  # type: ignore[arg-type]
            # wait for at least 2 clients to be connected (cobra and LCM logger)
            if i > max_relay_wait_iterations:
                print(
                    'Timed out waiting for clients to connect to the TCP relay.',
                    flush=True,
                )
                raise TimeoutError
            if re.search(r'[2-9] clients', line):
                break

        # play log. note that logplayer process automatically terminates at end of log
        logplayer_process = run_lcm_logplayer(input_log)

    finally:
        if logger_process is not None:
            logger_process.wait()
        if app_process is not None:
            kill(app_process)
        if logplayer_process is not None:
            kill(logplayer_process)
        if relay_process is not None:
            kill(relay_process)

    return app_process.returncode if app_process else -1
