import os
import time
from pathlib import Path
from signal import SIGINT
from subprocess import PIPE, Popen
from threading import Thread
from typing import IO, Any


def monitor_app_output(
    pipe: IO[Any],
    validate: bool = False,
    wait_for_msg: str = '',
    separate_thread: bool = False,
) -> None:
    if separate_thread:
        t = Thread(target=monitor_app_output, args=(pipe, validate, wait_for_msg))
        t.daemon = True
        t.start()
        return

    for line in pipe:
        print(line, end='')
        if validate:
            # ensure there are no warnings or errors
            assert 'WARN' not in line
            assert 'ERROR' not in line
        if wait_for_msg and wait_for_msg in line:
            break


def wait_until_file_stable(
    file: Path, stable_secs: int = 3, check_interval: int = 1
) -> None:
    """Wait until file stops growing for `stable_secs` seconds.

    Will also return if file does not exist for `stable_secs` seconds.
    """
    last_size = -1
    size = -1
    stable_time = 0.0

    while True:
        if file.exists():
            size = file.stat().st_size

        if size == last_size:
            stable_time += check_interval
            if stable_time >= stable_secs:
                return
        else:
            stable_time = 0.0
            last_size = size

        time.sleep(check_interval)


def run_app(
    app: Path,
    args: list[str] | None = None,
    monitor: bool = False,
    validate: bool = False,
) -> Popen[str]:
    cmd = ['python3', '-u', app.as_posix()]
    if args is not None:
        cmd.extend(args)

    # Set unbuffered flag so the subprocess standard output can be read in real time
    app_process = Popen(cmd, stdout=PIPE, text=True, bufsize=1, start_new_session=True)
    if monitor:
        assert app_process.stdout is not None
        monitor_app_output(app_process.stdout, validate=validate, separate_thread=True)

    return app_process


def kill(process: Popen[Any]) -> None:
    try:
        os.killpg(os.getpgid(process.pid), SIGINT)
    except OSError:
        return
    else:
        process.wait()
