import os
import shutil
from subprocess import Popen

from .apps import kill, monitor_app_output, run_app, wait_until_file_stable


def get_ros_bag_file(specified_file: str) -> str:  # pragma: no cover
    actual_file = os.path.join(specified_file, f'{specified_file}_0.db3')
    if not os.path.exists(actual_file):
        actual_file = os.path.join(specified_file, f'{specified_file}_0.mcap')

    return actual_file


def run_ros_logger(output_file: str) -> Popen[bytes]:  # pragma: no cover
    # Remove any pre-existing output
    if os.path.exists(output_file):
        shutil.rmtree(output_file)
    return Popen(
        ['ros2', 'bag', 'record', '-a', '-s', 'mcap', '-o', output_file],
        start_new_session=True,
    )


def run_ros_bag_player(logfile: str) -> Popen[bytes]:  # pragma: no cover
    return Popen(
        # Rate must be slow enough for fastest topics to be published
        # at full speed in the CI. See "Using ROS" docs.
        ['ros2', 'bag', 'play', '-r', '10', '--log-level', 'warn', logfile],
        start_new_session=True,
    )


def run_pntos_with_ros_transport(
    app: str,
    input_log: str,
    output_log: str,
    validate: bool = False,
) -> None:  # pragma: no cover
    """Spin up app and network tools necessary to run it, process log, then shut down.

    Args:
        app (str): Path to app to run.
        input_log (str): ROS log containing the measurements to be processed.
        output_log (str): ROS log to which output should be recorded.
        validate (bool): Whether to validate the app's output, ensuring there are no
            warnings or errors. Defaults to False.
    """
    try:
        logger_process = run_ros_logger(output_log)
        app_process = run_app(app, validate=validate)

        # Wait for all plugins to start up
        done_msg = 'Ctrl + C'
        assert app_process.stdout is not None
        monitor_app_output(app_process.stdout, validate=validate, wait_for_msg=done_msg)

        # Now just monitor app output asynchronously
        monitor_app_output(app_process.stdout, validate=validate, separate_thread=True)

        # play log
        logplayer_process = run_ros_bag_player(input_log)

        actual_output_log = get_ros_bag_file(output_log)
        wait_until_file_stable(actual_output_log)

    finally:
        kill(logplayer_process)
        kill(logger_process)
        kill(app_process)
