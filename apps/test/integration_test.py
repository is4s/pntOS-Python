#!/usr/bin/env python3

import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from analysis.lcm.data import PvaData
from analysis.lcm.error import calc_tilts
from analysis.lcm.interpolation import interpolate_pva
from analysis.lcm.log_readers import read_pva
from numpy.typing import NDArray
from pntos.cobra.utils import (
    run_pntos_with_log_transport,
    run_pntos_with_network_transport,
    run_pntos_with_ros_transport,
)
from pntos_python_datasets import EXAMPLE_LCM_LOG, EXAMPLE_ROS_LOG

OUTPUT_LOG = Path('pntos_output.log')
OUTPUT_BAG = OUTPUT_LOG.parent / OUTPUT_LOG.stem
SOLUTION_CHANNEL = '/solution/pntos/pva'
TRUTH_CHANNEL = '/sensor/ins-d/pva'

# Use non-GUI backend for any plots that apps generate, since we just want to
# programmatically validate the filter solution
os.environ['MPLBACKEND'] = 'Agg'


@dataclass
class ErrorLimits:
    std_thresh: float
    max_thresh: float
    pct_below_1sigma: float = 68.0
    pct_below_2sigma: float = 95.0
    pct_below_3sigma: float = 99.0


def validate_error(
    error: NDArray[np.float64], sigma: NDArray[np.float64], limits: ErrorLimits
) -> None:
    abs_error = np.abs(error)

    # ensure specific percentage of error below 1-sigma, 2-sigma, and 3-sigma
    pct_below_1sigma = np.mean(abs_error <= sigma, axis=0) * 100
    assert np.all(pct_below_1sigma >= limits.pct_below_1sigma)
    pct_below_2sigma = np.mean(abs_error <= sigma * 2, axis=0) * 100
    assert np.all(pct_below_2sigma >= limits.pct_below_2sigma)
    pct_below_3sigma = np.mean(abs_error <= sigma * 3, axis=0) * 100
    assert np.all(pct_below_3sigma >= limits.pct_below_3sigma)

    # ensure error is below expected standard deviation and max err limits
    assert np.all(np.abs(np.std(error, axis=0)) < limits.std_thresh)
    assert np.all(np.max(abs_error, axis=0) < limits.max_thresh)


def validate_results(
    pva: PvaData,
    truth: PvaData,
    num_points: float,
    pos_err_limits: ErrorLimits,
    vel_err_limits: ErrorLimits,
    tilt_err_limits: ErrorLimits,
    expected_start_time_offset: float = 0.0,
) -> None:
    filter_time: NDArray[np.float64] = pva.time
    truth_time: NDArray[np.float64] = truth.time

    # ensure solution has enough points
    assert filter_time.size == num_points

    # ensure solution has no NANs
    assert not np.isnan(pva.ned).any()
    assert not np.isnan(pva.vel).any()
    assert not np.isnan(pva.rpy).any()
    assert not np.isnan(pva.ned_sig).any()
    assert not np.isnan(pva.vel_sig).any()
    assert not np.isnan(pva.tilt_sig).any()

    # ensure solution starts and ends within 3 seconds of truth start and end
    assert abs(filter_time[0] - expected_start_time_offset - truth_time[0]) < 3.0  # noqa: PLR2004
    assert abs(filter_time[-1] - truth_time[-1]) < 3  # noqa: PLR2004

    # Interpolate truth onto solution times so that we can calculate the solution error
    interp_truth_pva = interpolate_pva(pva, truth)
    ned_err = pva.ned - interp_truth_pva.ned
    vel_err = pva.vel - interp_truth_pva.vel
    rpy_rad = np.deg2rad(pva.rpy)
    truth_rpy_rad = np.deg2rad(interp_truth_pva.rpy)
    tilt_err = np.rad2deg(calc_tilts(truth_rpy_rad, rpy_rad))

    # ensure PVA errors are within expected limits
    validate_error(ned_err, pva.ned_sig, limits=pos_err_limits)
    validate_error(vel_err, pva.vel_sig, limits=vel_err_limits)
    validate_error(tilt_err, pva.tilt_sig, limits=tilt_err_limits)


def test_tutorial_gps_ins_app() -> None:
    run_pntos_with_log_transport(
        Path('apps/tutorial/gps_ins.py'), OUTPUT_LOG, validate=True
    )
    log_data = read_pva(OUTPUT_LOG.as_posix(), read_all=True)
    validate_results(
        log_data.data[SOLUTION_CHANNEL],
        log_data.data[TRUTH_CHANNEL],
        num_points=2593,
        pos_err_limits=ErrorLimits(std_thresh=2.0, max_thresh=4.0, pct_below_1sigma=60),
        vel_err_limits=ErrorLimits(std_thresh=0.11, max_thresh=1.0),
        tilt_err_limits=ErrorLimits(
            std_thresh=0.85, max_thresh=3.5, pct_below_1sigma=48, pct_below_2sigma=91
        ),
    )


def test_standard_gps_ins_app() -> None:
    run_pntos_with_log_transport(
        Path('apps/standard/gps_ins.py'), OUTPUT_LOG, validate=True
    )
    log_data = read_pva(OUTPUT_LOG, read_all=True)
    validate_results(
        log_data.data[SOLUTION_CHANNEL],
        log_data.data[TRUTH_CHANNEL],
        num_points=2584,
        pos_err_limits=ErrorLimits(std_thresh=2.0, max_thresh=4.0, pct_below_1sigma=60),
        vel_err_limits=ErrorLimits(std_thresh=0.11, max_thresh=1.0),
        tilt_err_limits=ErrorLimits(
            std_thresh=0.85, max_thresh=3.5, pct_below_1sigma=48, pct_below_2sigma=91
        ),
        expected_start_time_offset=10.0,
    )


def test_standard_gps_ins_network_app() -> None:
    run_pntos_with_network_transport(
        Path('apps/standard/lcm_relay.py'),
        Path(EXAMPLE_LCM_LOG),
        OUTPUT_LOG,
        validate=True,
    )
    log_data = read_pva(OUTPUT_LOG.as_posix(), read_all=True)
    validate_results(
        log_data.data[SOLUTION_CHANNEL],
        log_data.data[TRUTH_CHANNEL],
        num_points=2584,
        pos_err_limits=ErrorLimits(std_thresh=2.0, max_thresh=4.0, pct_below_1sigma=60),
        vel_err_limits=ErrorLimits(std_thresh=0.11, max_thresh=1.0),
        tilt_err_limits=ErrorLimits(
            std_thresh=0.85, max_thresh=3.5, pct_below_1sigma=48, pct_below_2sigma=91
        ),
        expected_start_time_offset=10.0,
    )


def test_tutorial_gps_ins_vel_app() -> None:
    run_pntos_with_log_transport(
        Path('apps/tutorial/gps_vel_ins.py'), OUTPUT_LOG, validate=True
    )
    log_data = read_pva(OUTPUT_LOG, read_all=True)
    validate_results(
        log_data.data[SOLUTION_CHANNEL],
        log_data.data[TRUTH_CHANNEL],
        num_points=2593,
        # TODO: these limits are very high
        pos_err_limits=ErrorLimits(
            std_thresh=2.0,
            max_thresh=4.5,
            pct_below_1sigma=40,
            pct_below_2sigma=70,
            pct_below_3sigma=95,
        ),
        vel_err_limits=ErrorLimits(
            std_thresh=0.2,
            max_thresh=1.5,
            pct_below_1sigma=55,
            pct_below_2sigma=75,
            pct_below_3sigma=85,
        ),
        tilt_err_limits=ErrorLimits(
            std_thresh=2.0,
            max_thresh=6.0,
            pct_below_1sigma=20,
            pct_below_2sigma=50,
            pct_below_3sigma=60,
        ),
    )


def test_standard_gps_ins_leverarm_app() -> None:
    run_pntos_with_log_transport(
        Path('apps/standard/gps_ins_leverarm.py'), OUTPUT_LOG, validate=True
    )
    log_data = read_pva(OUTPUT_LOG, read_all=True)
    validate_results(
        log_data.data[SOLUTION_CHANNEL],
        log_data.data[TRUTH_CHANNEL],
        num_points=2584,
        pos_err_limits=ErrorLimits(std_thresh=2.0, max_thresh=4.1, pct_below_1sigma=60),
        vel_err_limits=ErrorLimits(std_thresh=0.11, max_thresh=1.0),
        tilt_err_limits=ErrorLimits(
            std_thresh=0.81, max_thresh=2.5, pct_below_1sigma=53, pct_below_2sigma=91
        ),
        expected_start_time_offset=10.0,
    )


def test_standard_gps_bodyvel_ins_app() -> None:
    run_pntos_with_log_transport(
        Path('apps/standard/gps_ins_bodyvel.py'), OUTPUT_LOG, validate=True
    )
    log_data = read_pva(OUTPUT_LOG, read_all=True)
    validate_results(
        log_data.data[SOLUTION_CHANNEL],
        log_data.data[TRUTH_CHANNEL],
        num_points=2584,
        pos_err_limits=ErrorLimits(std_thresh=1.4, max_thresh=4.0, pct_below_1sigma=64),
        vel_err_limits=ErrorLimits(std_thresh=0.11, max_thresh=1.0),
        tilt_err_limits=ErrorLimits(std_thresh=0.8, max_thresh=3.5),
        expected_start_time_offset=10.0,
    )


def test_standard_gps_ins_vel_app() -> None:
    run_pntos_with_log_transport(
        Path('apps/standard/gps_vel_ins.py'), OUTPUT_LOG, validate=True
    )
    log_data = read_pva(OUTPUT_LOG, read_all=True)
    validate_results(
        log_data.data[SOLUTION_CHANNEL],
        log_data.data[TRUTH_CHANNEL],
        num_points=2584,
        # TODO: these limits are very high
        pos_err_limits=ErrorLimits(
            std_thresh=1.4,
            max_thresh=4.7,
            pct_below_1sigma=5,
            pct_below_2sigma=12,
            pct_below_3sigma=24,
        ),
        vel_err_limits=ErrorLimits(
            std_thresh=0.14,
            max_thresh=1.1,
            pct_below_1sigma=48,
            pct_below_2sigma=77,
            pct_below_3sigma=87,
        ),
        tilt_err_limits=ErrorLimits(
            std_thresh=1.6,
            max_thresh=5.1,
            pct_below_1sigma=30,
            pct_below_2sigma=52,
            pct_below_3sigma=68,
        ),
        expected_start_time_offset=10.0,
    )


def test_standard_posvel_ins_app() -> None:
    run_pntos_with_log_transport(
        Path('apps/standard/posvel_ins.py'), OUTPUT_LOG, validate=True
    )
    log_data = read_pva(OUTPUT_LOG, read_all=True)

    validate_results(
        log_data.data[SOLUTION_CHANNEL],
        log_data.data[TRUTH_CHANNEL],
        num_points=2584,
        # TODO: these limits are very high
        pos_err_limits=ErrorLimits(
            std_thresh=1.4,
            max_thresh=4.7,
            pct_below_1sigma=5,
            pct_below_2sigma=12,
            pct_below_3sigma=24,
        ),
        vel_err_limits=ErrorLimits(
            std_thresh=0.14,
            max_thresh=1.1,
            pct_below_1sigma=48,
            pct_below_2sigma=77,
            pct_below_3sigma=87,
        ),
        tilt_err_limits=ErrorLimits(
            std_thresh=1.6,
            max_thresh=5.1,
            pct_below_1sigma=30,
            pct_below_2sigma=52,
            pct_below_3sigma=68,
        ),
        expected_start_time_offset=10.0,
    )


def test_advanced_gps_ins_ros_app() -> None:
    import pytest  # noqa: PLC0415

    # Only run this test if ros is installed
    pytest.importorskip('rosbag2_py')

    # Just run the app and ensure it doesn't crash. Don't validate the results, as the
    # ROS transport is not consistent enough.
    run_pntos_with_ros_transport(
        Path('apps/advanced/gps_ins_ros.py'),
        Path(EXAMPLE_ROS_LOG),
        OUTPUT_BAG,
        validate=True,
    )
