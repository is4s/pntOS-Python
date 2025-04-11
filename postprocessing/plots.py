#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['figure.figsize'] = (10, 6)

import os
import pickle
import sys

import numpy as np
from navtk.navutils import (
    dcm_to_rpy,
    delta_lat_to_north,
    delta_lon_to_east,
    east_to_delta_lon,
    north_to_delta_lat,
    quat_to_rpy,
    rpy_to_dcm,
)
from numpy import (
    array,
    diagonal,
    diff,
    dot,
    rad2deg,
    sqrt,
    transpose,
    zeros,
)
from pylab import (
    figure,
    gca,
    legend,
    plot,
    savefig,
    show,
    subplot,
    subplots_adjust,
    suptitle,
    xlabel,
    ylabel,
)
from scipy.interpolate import interp1d


def get_statistics(arr: np.ndarray):
    """
    Generate the following statistics from a given array of values:
    1) Mean
    2) Standard Deviation
    3) Root Mean Square
    4) Absolute Max

    Args:
        - arr (np.ndarray): Array for which to generate statistics.

    Returns:
        - String containing the generated statistics.
    """
    m = np.nanmean(arr)
    std = np.nanstd(arr)
    rms = np.sqrt(np.nansum(np.square(arr)) / arr.size)
    abs_max = np.nanmax(np.abs(arr))

    statistics_str = (
        f'Mean: {m:.2f}\n'
        + f'Standard Deviation: {std:.2f}\n'
        + f'Root Mean Square: {rms:.2f}\n'
        + f'Absolute Max: {abs_max:.2f}'
    )

    return statistics_str


def show_stats(fig, y):
    subplots_adjust(right=0.7)
    ax_pos = gca().get_position()
    x_pos = ax_pos.xmax + 0.01
    y_pos = ax_pos.ymin + 0.01
    stats = get_statistics(y)
    fig.text(x_pos, y_pos, stats)


def timestamps_to_double_list(data):
    t = []
    for d in data:
        t.append(d.time_of_validity.elapsed_nsec * 1e-9)
    return t


def arrival_timestamps_to_double_list(data):
    t = []
    for d in data:
        t.append(d.time_of_validity.elapsed_nsec * 1e-9)
    return t


class TimeData:
    def __init__(self, data):
        self.raw_time = array(timestamps_to_double_list(data))
        self.raw_arrival_time = array(arrival_timestamps_to_double_list(data))
        self.t0 = self.raw_time[0]
        self.dt = diff(self.raw_time)


def extract_lla(data):
    lla = zeros([len(data), 3])
    for k in range(0, len(data)):
        lla[k, :] = [
            data[k].p1,
            data[k].p2,
            data[k].p3,
        ]
    return lla


def lla_to_ned_vector(d, lat0, lon0, alt0):
    out = zeros(d.shape)
    for k in range(0, d.shape[0]):
        out[k, 0] = delta_lat_to_north(d[k, 0] - lat0, lat0, alt0)
        out[k, 1] = delta_lon_to_east(d[k, 1] - lon0, lat0, alt0)
        out[k, 2] = alt0 - d[k, 2]
    return out


def vel_from_llh(llh, t):
    # nx3 input
    ned_vec = lla_to_ned_vector(llh, llh[0, 0], llh[0, 1], llh[0, 2])
    ned_diff = diff(ned_vec, axis=0)
    t_diff = diff(t)
    ned_diff[:, 0] = ned_diff[:, 0] / t_diff
    ned_diff[:, 1] = ned_diff[:, 1] / t_diff
    ned_diff[:, 2] = ned_diff[:, 2] / t_diff
    # Vel at midpoints, need to interpolate back to original time
    t_vel = t[0:-1] + 0.5 * t_diff
    return transpose(
        interp1d(
            t_vel,
            transpose(ned_diff),
            bounds_error=False,
            fill_value='extrapolate',
        )(t)
    )


def extract_pos_sigma(data):
    sigma = zeros([len(data), 3])
    for k in range(0, len(data)):
        sigma[k, :] = sqrt(diagonal(data[k].covariance)[0:3])
    return sigma


def extract_rpy(data, convert_rpy_to_prh: bool = False):
    rpy = zeros([len(data), 3])
    for k in range(0, len(data)):
        rpy[k, :] = quat_to_rpy(data[k].quaternion)
    if convert_rpy_to_prh:
        rpy = np.transpose(np.stack((rpy[:, 1], rpy[:, 0], -rpy[:, 2])))

    return rpy


def extract_tilt_sigma(data):
    sigma = zeros([len(data), 3])
    for k in range(0, len(data)):
        sigma[k, :] = sqrt(diagonal(data[k].covariance)[6:9])
    return sigma


def extract_vel(data_struct):
    if data_struct.decode_class_name == 'geodeticposition3d':
        llh = extract_lla(data_struct.data)
        t = TimeData(data_struct.data)
        return vel_from_llh(llh, t.raw_time)
    elif data_struct.decode_class_name == 'positionvelocityattitude':
        vel = zeros([len(data_struct.data), 3])
        for k in range(0, len(data_struct.data)):
            vel[k, :] = [
                data_struct.data[k].v1,
                data_struct.data[k].v2,
                data_struct.data[k].v3,
            ]
        return vel
    elif data_struct.decode_class_name == 'velocity3d':
        vel = zeros([len(data_struct.data), 3])
        for k in range(0, len(data_struct.data)):
            vel[k, :] = [
                data_struct.data[k].x,
                data_struct.data[k].y,
                data_struct.data[k].z,
            ]
        return vel
    else:
        raise ValueError(
            "Data struct is of wrong type ({}), can't extract velocity".format(
                data_struct.decode_class_name
            )
        )


def extract_vel_sigma(data_struct):
    if data_struct.decode_class_name == 'geodeticposition3d':
        cov = zeros([len(data_struct.data), 3])
        for k in range(0, len(data_struct.data)):
            cov[k, :] = diagonal(data_struct.data[k].covariance)[0:3]
        sig_sm = sqrt(cov[:-1, :] + cov[1:, :])
        t = TimeData(data_struct.data)
        sig_sm[:, 0] /= t.dt
        sig_sm[:, 1] /= t.dt
        sig_sm[:, 2] /= t.dt
        # Sigmas are at midpoints, need to interpolate back to original times
        t_mid = t.raw_time[0:-1] + 0.5 * t.dt
        return transpose(
            interp1d(
                t_mid,
                transpose(sig_sm),
                bounds_error=False,
                fill_value='extrapolate',
            )(t.raw_time)
        )
    elif data_struct.decode_class_name == 'positionvelocityattitude':
        sigma = zeros([len(data_struct.data), 3])
        for k in range(0, len(data_struct.data)):
            sigma[k, :] = sqrt(diagonal(data_struct.data[k].covariance)[3:6])
        return sigma
    elif data_struct.decode_class_name == 'velocity3d':
        sigma = zeros([len(data_struct.data), 3])
        for k in range(0, len(data_struct.data)):
            sigma[k, :] = sqrt(diagonal(data_struct.data[k].covariance))
        return sigma
    else:
        raise ValueError(
            "Data struct is of wrong type ({}), can't extract velocity sigma".format(
                data_struct.decode_class_name
            )
        )


def convert_ned_sigma_to_lla_sigma(ned_sigma, lla):
    """
    Requires nx3 matrices
    """
    out_sigma = zeros(ned_sigma.shape)
    for k in range(0, ned_sigma.shape[0]):
        out_sigma[k, 0] = north_to_delta_lat(ned_sigma[k, 0], lla[k, 0], lla[k, 2])
        out_sigma[k, 1] = east_to_delta_lon(ned_sigma[k, 1], lla[k, 0], lla[k, 2])
    return out_sigma


def calc_tilts(rpy1, rpy2):
    """
    Both sources nx3
    """
    tilts = zeros(rpy1.shape)
    for k in range(0, rpy1.shape[0]):
        if np.isnan(rpy1[k]).any() or np.isnan(rpy2[k]).any():
            tilts[k, :] = np.array([np.nan, np.nan, np.nan])
        else:
            tilts[k, :] = dcm_to_rpy(
                dot(transpose(rpy_to_dcm(rpy1[k, :])), rpy_to_dcm(rpy2[k, :]))
            )
    return tilts


def sort_solution(solution):
    # Order PVAs by timestamp
    solution[1].data.sort(key=lambda x: x.time_of_validity.elapsed_nsec)


def trim_identical_points(solution):
    # Crop off first few points, since we have duplicate solutions at
    # alignment. This is because we align at the IMU time, and don't get more
    # solutions until filter time catches up.
    start_time = solution[1].data[0].time_of_validity.elapsed_nsec
    time = start_time
    idx = 0
    while time == start_time:
        idx += 1
        time = solution[1].data[idx].time_of_validity.elapsed_nsec

    solution[1].data = solution[1].data[idx - 1 :]


def plot_biases(data):
    for d in data.items():
        if d[0] == 'accel_biases':
            t = TimeData(d[1].data)
            tt = t.raw_time - t.t0
            accel_bias = extract_lla(d[1].data)
            accel_bias_sigma = extract_pos_sigma(d[1].data)
            figure()
            subplot(3, 1, 1)
            plot(tt, accel_bias[:, 0], 'k')
            plot(tt, accel_bias[:, 0] + accel_bias_sigma[:, 0], 'r')
            plot(tt, accel_bias[:, 0] - accel_bias_sigma[:, 0], 'r')
            subplot(3, 1, 2)
            plot(tt, accel_bias[:, 1], 'k')
            plot(tt, accel_bias[:, 1] + accel_bias_sigma[:, 1], 'r')
            plot(tt, accel_bias[:, 1] - accel_bias_sigma[:, 1], 'r')
            subplot(3, 1, 3)
            plot(tt, accel_bias[:, 2], 'k')
            plot(tt, accel_bias[:, 2] + accel_bias_sigma[:, 2], 'r')
            plot(tt, accel_bias[:, 2] - accel_bias_sigma[:, 2], 'r')
            suptitle('Estimated Accel Biases')
        if d[0] == 'gyro_biases':
            t = TimeData(d[1].data)
            tt = t.raw_time - t.t0
            gyro_bias = extract_lla(d[1].data)
            gyro_bias_sigma = extract_pos_sigma(d[1].data)
            figure()
            subplot(3, 1, 1)
            plot(tt, gyro_bias[:, 0])
            plot(tt, gyro_bias[:, 0] + gyro_bias_sigma[:, 0], 'r')
            plot(tt, gyro_bias[:, 0] - gyro_bias_sigma[:, 0], 'r')
            subplot(3, 1, 2)
            plot(tt, gyro_bias[:, 1])
            plot(tt, gyro_bias[:, 1] + gyro_bias_sigma[:, 1], 'r')
            plot(tt, gyro_bias[:, 1] - gyro_bias_sigma[:, 1], 'r')
            subplot(3, 1, 3)
            plot(tt, gyro_bias[:, 2])
            plot(tt, gyro_bias[:, 2] + gyro_bias_sigma[:, 2], 'r')
            plot(tt, gyro_bias[:, 2] - gyro_bias_sigma[:, 2], 'r')
            suptitle('Estimated Gyro Biases')


def trim_extra_points(solution, truth):
    # Remove any points that would require us to extrapolate more than 1 second
    # when interpolating solution onto truth
    sol_start = solution[1].data[0].time_of_validity.elapsed_nsec
    truth_start = truth[1].data[0].time_of_validity.elapsed_nsec
    sol_end = solution[1].data[-1].time_of_validity.elapsed_nsec
    truth_end = truth[1].data[-1].time_of_validity.elapsed_nsec

    start_idx = 0
    while (sol_start - truth_start) > 1_000_000_000:
        start_idx += 1
        truth_start = truth[1].data[start_idx].time_of_validity.elapsed_nsec

    end_idx = -1
    while (truth_end - sol_end) > 1_000_000_000:
        end_idx -= 1
        truth_end = truth[1].data[end_idx].time_of_validity.elapsed_nsec

    truth[1].data = truth[1].data[start_idx:end_idx]


def plot_solution(solution, truth, plot_dir, show_plots):
    title = os.path.basename(plot_dir)
    sort_solution(solution)
    trim_identical_points(solution)
    trim_extra_points(solution, truth)

    leg = [solution[0], truth[0]]
    leg_w_sigma = [solution[0], truth[0], '+/- 1 sigma']

    # Extract truth solution
    tlla = extract_lla(truth[1].data)
    lat0 = tlla[0, 0]
    lon0 = tlla[0, 1]
    alt0 = tlla[0, 2]
    tvel = extract_vel(truth[1])
    tvel[:, 2] = -tvel[:, 2]
    trpy = None
    if truth[1].decode_class_name == 'positionvelocityattitude':
        trpy = extract_rpy(truth[1].data, True)
    tt = TimeData(truth[1].data)
    tned = lla_to_ned_vector(tlla, lat0, lon0, alt0)

    # Extract (most likely the filter) solution
    t = TimeData(solution[1].data)
    lla = extract_lla(solution[1].data)
    pos_sig = extract_pos_sigma(solution[1].data)
    sig = convert_ned_sigma_to_lla_sigma(pos_sig, lla)
    ned = lla_to_ned_vector(lla, lat0, lon0, alt0)
    vel = extract_vel(solution[1])
    vel_sig = extract_vel_sigma(solution[1])
    rpy = None
    rpy_sig = None
    if solution[1].decode_class_name == 'positionvelocityattitude':
        rpy = extract_rpy(solution[1].data)
        rpy_sig = extract_tilt_sigma(solution[1].data)

    t0 = min(t.t0, tt.t0)
    rel_time = t.raw_time - t0
    truth_rel_time = tt.raw_time - t0

    # Northing vs .Easting
    fig = figure(f'Trajectory {title}')
    suptitle('Northing vs. Easting')
    plot(ned[:, 1], ned[:, 0], 'o', tned[:, 1], tned[:, 0], 'o')
    ylabel('Northing (m)')
    xlabel('Easting (s)')
    legend(leg)
    filename = os.path.join(plot_dir, 'ne_trajectory')
    pickle.dump(fig, open(f'{filename}.pickle', 'wb'))
    savefig(f'{filename}.png', dpi=300)

    # LLA Postion vs. Time
    fig = figure(f'LLA Pos {title}')
    suptitle('LLA Position and Uncertainty vs. Time')
    subplot(3, 1, 1)
    plot(rel_time, lla[:, 0])
    plot(truth_rel_time, tlla[:, 0], 'g')
    plot(rel_time, lla[:, 0] + sig[:, 0], 'black')
    plot(rel_time, lla[:, 0] - sig[:, 0], 'black')
    ylabel('Latitude (rad)')
    subplot(3, 1, 2)
    plot(rel_time, lla[:, 1])
    plot(truth_rel_time, tlla[:, 1], 'g')
    plot(rel_time, lla[:, 1] + sig[:, 1], 'black')
    plot(rel_time, lla[:, 1] - sig[:, 1], 'black')
    ylabel('Longitude (rad)')
    subplot(3, 1, 3)
    plot(rel_time, lla[:, 2])
    plot(truth_rel_time, tlla[:, 2], 'g')
    # TODO: is alt sigma 0?
    plot(rel_time, lla[:, 2] + sig[:, 2], 'black')
    plot(rel_time, lla[:, 2] - sig[:, 2], 'black')
    ylabel('Altitude (m)')
    xlabel(f'Relative time (sec), t0 = {t0}')
    legend(leg_w_sigma)
    filename = os.path.join(plot_dir, 'lla_position')
    pickle.dump(fig, open(f'{filename}.pickle', 'wb'))
    savefig(f'{filename}.png', dpi=300)

    # NED Position vs. Time
    fig = figure(f'NED Pos {title}')
    suptitle('NED Position vs. Time')
    subplot(3, 1, 1)
    plot(rel_time, ned[:, 0])
    plot(truth_rel_time, tned[:, 0])
    ylabel('Northing (m)')
    subplot(3, 1, 2)
    plot(rel_time, ned[:, 1])
    plot(truth_rel_time, tned[:, 1])
    ylabel('Easting (m)')
    subplot(3, 1, 3)
    plot(rel_time, ned[:, 2])
    plot(truth_rel_time, tned[:, 2])
    ylabel('Down (m)')
    xlabel(f'Relative time (sec), t0 = {t0}')
    legend(leg)
    filename = os.path.join(plot_dir, 'ned_position')
    pickle.dump(fig, open(f'{filename}.pickle', 'wb'))
    savefig(f'{filename}.png', dpi=300)

    pos_sig = transpose(
        interp1d(
            t.raw_time,
            transpose(pos_sig),
            bounds_error=False,
            fill_value='extrapolate',
        )(tt.raw_time)
    )
    ned = transpose(
        interp1d(
            t.raw_time,
            transpose(ned),
            bounds_error=False,
            fill_value='extrapolate',
        )(tt.raw_time)
    )

    fig = figure(f'NED Pos Error {title}')
    north_pos_err = tned[:, 0] - ned[:, 0]
    east_pos_err = tned[:, 1] - ned[:, 1]
    down_pos_error = tned[:, 2] - ned[:, 2]
    suptitle(f'{solution[0]} NED Position Error vs. Time')
    subplot(3, 1, 1)
    plot(truth_rel_time, north_pos_err)
    plot(truth_rel_time, pos_sig[:, 0], 'black')
    plot(truth_rel_time, -pos_sig[:, 0], 'black')
    show_stats(fig, north_pos_err)
    ylabel('North Error (m)')
    subplot(3, 1, 2)
    plot(truth_rel_time, east_pos_err)
    plot(truth_rel_time, pos_sig[:, 1], 'black')
    plot(truth_rel_time, -pos_sig[:, 1], 'black')
    show_stats(fig, east_pos_err)
    ylabel('East Error (m)')
    subplot(3, 1, 3)
    plot(truth_rel_time, down_pos_error)
    plot(truth_rel_time, pos_sig[:, 2], 'black')
    plot(truth_rel_time, -pos_sig[:, 2], 'black')
    show_stats(fig, down_pos_error)
    ylabel('Down Error (m)')
    xlabel(f'Relative time (sec), t0 = {t0}')
    filename = os.path.join(plot_dir, 'ned_position_error')
    pickle.dump(fig, open(f'{filename}.pickle', 'wb'))
    savefig(f'{filename}.png', dpi=300)

    # NED Velocity vs. Time
    fig = figure(f'Vel {title}')
    suptitle('Velocity and Uncertainty vs. Time')
    subplot(3, 1, 1)
    plot(rel_time, vel[:, 0])
    plot(truth_rel_time, tvel[:, 0], 'g')
    plot(rel_time, vel[:, 0] + vel_sig[:, 0], 'black')
    plot(rel_time, vel[:, 0] - vel_sig[:, 0], 'black')
    ylabel('North vel (m/s)')
    subplot(3, 1, 2)
    plot(rel_time, vel[:, 1])
    plot(truth_rel_time, tvel[:, 1], 'g')
    plot(rel_time, vel[:, 1] + vel_sig[:, 1], 'black')
    plot(rel_time, vel[:, 1] - vel_sig[:, 1], 'black')
    ylabel('East vel (m/s)')
    subplot(3, 1, 3)
    plot(rel_time, vel[:, 2])
    plot(truth_rel_time, tvel[:, 2], 'g')
    plot(rel_time, vel[:, 2] + vel_sig[:, 2], 'black')
    plot(rel_time, vel[:, 2] - vel_sig[:, 2], 'black')
    ylabel('Down vel (m/s)')
    xlabel(f'Relative time (sec), t0 = {t0}')
    legend(leg_w_sigma)
    filename = os.path.join(plot_dir, 'ned_velocity')
    pickle.dump(fig, open(f'{filename}.pickle', 'wb'))
    savefig(f'{filename}.png', dpi=300)

    vel_sig = transpose(
        interp1d(
            t.raw_time,
            transpose(vel_sig),
            bounds_error=False,
            fill_value='extrapolate',
        )(tt.raw_time)
    )
    vel = transpose(
        interp1d(
            t.raw_time,
            transpose(vel),
            bounds_error=False,
            fill_value='extrapolate',
        )(tt.raw_time)
    )

    fig = figure(f'NED Vel Error {title}')
    north_vel_error = tvel[:, 0] - vel[:, 0]
    east_vel_error = tvel[:, 1] - vel[:, 1]
    down_vel_error = tvel[:, 2] - vel[:, 2]
    suptitle(f'{solution[0]} NED Velocity Error vs. Time')
    subplot(3, 1, 1)
    plot(truth_rel_time, north_vel_error)
    plot(truth_rel_time, vel_sig[:, 0], 'black')
    plot(truth_rel_time, -vel_sig[:, 0], 'black')
    show_stats(fig, north_vel_error)
    ylabel('North Error (m/s)')
    subplot(3, 1, 2)
    plot(truth_rel_time, east_vel_error)
    plot(truth_rel_time, vel_sig[:, 1], 'black')
    plot(truth_rel_time, -vel_sig[:, 1], 'black')
    show_stats(fig, east_vel_error)
    ylabel('East Error (m/s)')
    subplot(3, 1, 3)
    plot(truth_rel_time, down_vel_error)
    plot(truth_rel_time, vel_sig[:, 2], 'black')
    plot(truth_rel_time, -vel_sig[:, 2], 'black')
    show_stats(fig, down_vel_error)
    ylabel('Down Error (m/s)')
    xlabel(f'Relative time (sec), t0 = {t0}')
    filename = os.path.join(plot_dir, 'ned_velocity_error')
    pickle.dump(fig, open(f'{filename}.pickle', 'wb'))
    savefig(f'{filename}.png', dpi=300)

    if rpy is not None and trpy is not None:
        rpy_deg = rad2deg(rpy)
        rpy_sig_deg = rad2deg(rpy_sig)
        trpy_deg = rad2deg(trpy)

        fig = figure(f'RPY {title}')
        suptitle('RPY and (tilt) Uncertainty vs. Time')
        subplot(3, 1, 1)
        plot(rel_time, rpy_deg[:, 0])
        plot(truth_rel_time, trpy_deg[:, 0], 'g')
        plot(rel_time, (rpy_deg[:, 0] + rpy_sig_deg[:, 0]), 'black')
        plot(rel_time, (rpy_deg[:, 0] - rpy_sig_deg[:, 0]), 'black')
        ylabel('Roll (deg)')
        subplot(3, 1, 2)
        plot(rel_time, rpy_deg[:, 1])
        plot(truth_rel_time, trpy_deg[:, 1], 'g')
        plot(rel_time, rpy_deg[:, 1] + (rpy_sig_deg[:, 1]), 'black')
        plot(rel_time, rpy_deg[:, 1] - (rpy_sig_deg[:, 1]), 'black')
        ylabel('Pitch (deg)')
        subplot(3, 1, 3)
        plot(rel_time, rpy_deg[:, 2])
        plot(truth_rel_time, trpy_deg[:, 2], 'g')
        plot(rel_time, rpy_deg[:, 2] + (rpy_sig_deg[:, 2]), 'black')
        plot(rel_time, rpy_deg[:, 2] - (rpy_sig_deg[:, 2]), 'black')
        ylabel('Yaw (deg)')
        xlabel(f'Relative time (sec), t0 = {t0}')
        legend(leg_w_sigma)
        filename = os.path.join(plot_dir, 'rpy')
        pickle.dump(fig, open(f'{filename}.pickle', 'wb'))
        savefig(f'{filename}.png', dpi=300)

        rpy_sig_deg = transpose(
            interp1d(
                t.raw_time,
                transpose(rpy_sig_deg),
                bounds_error=False,
                fill_value='extrapolate',
            )(tt.raw_time)
        )
        rpy = np.unwrap(rpy, axis=0)
        trpy = np.unwrap(trpy, axis=0)
        rpy = transpose(
            interp1d(
                t.raw_time,
                transpose(rpy),
                bounds_error=False,
                fill_value='extrapolate',
            )(tt.raw_time)
        )
        tilts = rad2deg(calc_tilts(trpy, rpy))

        fig = figure(f'NED Tilt Error {title}')
        suptitle(f'{solution[0]} NED Tilt Error vs. Time')
        subplot(3, 1, 1)
        plot(truth_rel_time, tilts[:, 0])
        plot(truth_rel_time, rpy_sig_deg[:, 0], 'black')
        plot(truth_rel_time, -rpy_sig_deg[:, 0], 'black')
        show_stats(fig, tilts[:, 0])
        ylabel('North tilt (deg)')
        subplot(3, 1, 2)
        plot(truth_rel_time, tilts[:, 1])
        plot(truth_rel_time, rpy_sig_deg[:, 1], 'black')
        plot(truth_rel_time, -rpy_sig_deg[:, 1], 'black')
        show_stats(fig, tilts[:, 1])
        ylabel('East tilt (deg)')
        subplot(3, 1, 3)
        plot(truth_rel_time, tilts[:, 2])
        plot(truth_rel_time, rpy_sig_deg[:, 2], 'black')
        plot(truth_rel_time, -rpy_sig_deg[:, 2], 'black')
        show_stats(fig, tilts[:, 2])
        ylabel('Down tilt (deg)')
        xlabel(f'Relative time (sec), t0 = {t0}')
        filename = os.path.join(plot_dir, 'ned_tilt_error')
        pickle.dump(fig, open(f'{filename}.pickle', 'wb'))
        savefig(f'{filename}.png', dpi=300)

    if show_plots:
        show()


def main(plot_dir):
    # show all previously-saved plots under plot_dir
    for subdir, _, files in os.walk(plot_dir):
        for file in files:
            if os.path.splitext(file)[1] == '.pickle':
                pickle.load(open(os.path.join(subdir, file), 'rb'))

    show()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python plots.py [plot_dir]')
        exit(1)

    lcmlog = sys.argv[1]
    main(lcmlog)
