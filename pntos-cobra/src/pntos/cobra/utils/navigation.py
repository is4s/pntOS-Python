from math import atan2, cos, sin, sqrt

import numpy as np
from aspn23 import MeasurementPositionVelocityAttitude as MeasurementPVA
from numpy import float64
from numpy.typing import NDArray


def skew(angles: NDArray[float64]) -> NDArray[float64]:
    return np.array(
        [
            [0, -angles[2], angles[1]],
            [angles[2], 0, -angles[0]],
            [-angles[1], angles[0], 0],
        ]
    )


def meridian_radius(lat: float) -> float:
    sin_lat = sin(lat)
    return float(
        RAD_E * (1 - ECC_SQUARE) / pow(1 - ECC_SQUARE * sin_lat * sin_lat, 1.5)
    )


def transverse_radius(lat: float) -> float:
    sin_lat = sin(lat)
    return float(RAD_E / pow(1 - ECC_SQUARE * sin_lat * sin_lat, 0.5))


def delta_lat_to_north(delta_lat: float, approx_lat: float, altitude: float) -> float:
    return (meridian_radius(approx_lat) + altitude) * delta_lat


def delta_lon_to_east(delta_lon: float, approx_lat: float, altitude: float) -> float:
    return (transverse_radius(approx_lat) + altitude) * delta_lon * cos(approx_lat)


def east_to_delta_lon(
    east_distance: float, approx_lat: float, altitude: float
) -> float:
    return east_distance / (
        (transverse_radius(approx_lat) + altitude) * cos(approx_lat)
    )


def north_to_delta_lat(
    north_distance: float, approx_lat: float, altitude: float
) -> float:
    return north_distance / (meridian_radius(approx_lat) + altitude)


def quat_to_dcm(quat: NDArray[float64]) -> NDArray[float64]:
    q0, q1, q2, q3 = quat
    a2 = pow(q0, 2)
    b2 = pow(q1, 2)
    c2 = pow(q2, 2)
    d2 = pow(q3, 2)
    ab = q0 * q1
    ac = q0 * q2
    ad = q0 * q3
    bc = q1 * q2
    bd = q1 * q3
    cd = q2 * q3
    return np.array(
        [
            [a2 + b2 - c2 - d2, 2 * (bc - ad), 2 * (bd + ac)],
            [2 * (bc + ad), a2 - b2 + c2 - d2, 2 * (cd - ab)],
            [2 * (bd - ac), 2 * (cd + ab), a2 - b2 - c2 + d2],
        ]
    )


def dcm_to_quat(dcm: NDArray[float64]) -> NDArray[float64]:
    d0 = dcm[0, 0]
    d1 = dcm[1, 1]
    d2 = dcm[2, 2]

    pa = abs(1 + d0 + d1 + d2)
    pb = abs(1 + d0 - d1 - d2)
    pc = abs(1 - d0 + d1 - d2)
    pd = abs(1 - d0 - d1 + d2)
    q0 = 0.0
    q1 = 0.0
    q2 = 0.0
    q3 = 0.0

    if pa >= pb and pa >= pc and pa >= pd:
        q0 = 0.5 * sqrt(pa)
        q0t4 = 4 * q0
        q1 = (dcm[2, 1] - dcm[1, 2]) / (q0t4)
        q2 = (dcm[0, 2] - dcm[2, 0]) / (q0t4)
        q3 = (dcm[1, 0] - dcm[0, 1]) / (q0t4)
    elif pb >= pa and pb >= pc and pb >= pd:
        q1 = 0.5 * sqrt(pb)
        q1t4 = 4 * q1
        q0 = (dcm[2, 1] - dcm[1, 2]) / (q1t4)
        q2 = (dcm[1, 0] + dcm[0, 1]) / (q1t4)
        q3 = (dcm[0, 2] + dcm[2, 0]) / (q1t4)
    elif pc >= pa and pc >= pb and pc >= pd:
        q2 = 0.5 * sqrt(pc)
        q2t4 = 4 * q2
        q0 = (dcm[0, 2] - dcm[2, 0]) / (q2t4)
        q1 = (dcm[1, 0] + dcm[0, 1]) / (q2t4)
        q3 = (dcm[2, 1] + dcm[1, 2]) / (q2t4)
    else:
        q3 = 0.5 * sqrt(pd)
        q3t4 = 4 * q3
        q0 = (dcm[1, 0] - dcm[0, 1]) / (q3t4)
        q1 = (dcm[0, 2] + dcm[2, 0]) / (q3t4)
        q2 = (dcm[2, 1] + dcm[1, 2]) / (q3t4)

    if q0 <= 0:
        return np.array([-q0, -q1, -q2, -q3])

    return np.array([q0, q1, q2, q3])


def llh_to_ecef(llh: NDArray[float64]) -> NDArray[float64]:
    a = RAD_E
    e2 = ECC_SQUARE
    phi, lam, h = llh
    cosphi = cos(phi)
    sinphi = sin(phi)

    N = a / sqrt(1 - e2 * pow(sinphi, 2))

    return np.array(
        [
            (N + h) * cosphi * cos(lam),
            (N + h) * cosphi * sin(lam),
            (N * (1 - e2) + h) * sinphi,
        ]
    )


def ecef_to_llh(ecef: NDArray[float64]) -> NDArray[float64]:
    """Converts from ECEF to LLH.

    Args:
        ecef (NDArray[float64]): A vector in the ECEF frame.

    Returns:
        NDArray[float64]: The equivalent vector in the LLH frame.
    """
    a = RAD_E
    e2 = ECC_SQUARE
    pm0 = sqrt(pow(ecef[0], 2) + pow(ecef[1], 2))
    pm1 = ecef[2]
    phi0 = atan2(pm1, pm0)
    h0: float = 0
    dp0 = a
    dp1 = a
    count = 0
    max_iterations = 5

    while (abs(dp0) > 7e-6 or abs(dp1) > 1e-6) and count <= max_iterations:  # noqa: PLR2004
        slat = sin(phi0)
        clat = cos(phi0)
        s2lat = slat * slat
        Nden = 1 - e2 * s2lat
        N = a / sqrt(Nden)

        dp0 = pm0 - (N + h0) * clat
        dp1 = pm1 - (N * (1 - e2) + h0) * slat
        k1 = 1 - e2 * s2lat
        k2 = sqrt(k1)

        A11 = slat * (e2 * a * clat * clat / k1 / k2 - a / k2 - h0)
        A12 = clat
        A21 = clat * (a * (1 - e2) / k2 + h0 + a * e2 * (1 - e2) * s2lat / k1 / k2)
        A22 = slat
        Adet = A11 * A22 - A21 * A12
        dHa = (A22 * dp0 - A12 * dp1) / Adet
        dHb = (-A21 * dp0 + A11 * dp1) / Adet

        phi0 += dHa
        h0 += dHb

        count += 1

    lam = atan2(ecef[1], ecef[0])
    return np.array([phi0, lam, h0])


def llh_to_cen(llh: NDArray[float64]) -> NDArray[float64]:
    clat = cos(llh[0])
    slat = sin(llh[0])
    clon = cos(llh[1])
    slon = sin(llh[1])
    return np.array(
        [
            [-slat * clon, -slon, -clat * clon],
            [-slat * slon, clon, -clat * slon],
            [clat, 0, -slat],
        ]
    )


def correct_dcm_with_tilt(
    dcm: NDArray[float64], tilt: NDArray[float64]
) -> NDArray[float64]:
    sum_squares = np.sum(np.square(tilt))
    if sum_squares > 0:
        m = sqrt(sum_squares)
        I = np.eye(3)  # noqa: E741
        s = skew(tilt)
        # Below is equivalent to I - sin(m) * s / m + dot((1 - cos(m)) * s, s) / pow(m, 2)
        # B is an approximation of rpy_to_dcm(-tilt) and/or I - skew(tilt)
        B: NDArray[float64] = (1 - cos(m)) / sum_squares * np.linalg.matrix_power(
            s, 2
        ) + (-sin(m) / m * s + I)
        return B @ dcm
    return dcm


def dcm_to_rpy(dcm: NDArray[float64]) -> NDArray[float64]:
    asin_arg = min(1.0, max(dcm[2, 0], -1.0))
    r = np.arctan2(dcm[2, 1], dcm[2, 2])
    p = -np.arcsin(asin_arg)
    y = np.arctan2(dcm[1, 0], dcm[0, 0])

    if asin_arg <= -0.999:  # noqa: PLR2004
        y_min_r = np.arctan2(dcm[1, 2] - dcm[0, 1], dcm[0, 2] + dcm[1, 1])
        y = y_min_r + r

    if asin_arg >= 0.999:  # noqa: PLR2004
        y_pls_r = np.arctan2(dcm[1, 2] + dcm[0, 1], dcm[0, 2] - dcm[1, 1]) + np.pi
        y = np.remainder((y_pls_r - r), 2.0 * np.pi)

    return np.array([r, p, y])


def extract_pos_and_vel(
    pva: MeasurementPVA,
) -> tuple[tuple[float, float, float], tuple[float, float, float]] | None:
    if (
        pva.p1 is None
        or pva.p2 is None
        or pva.p3 is None
        or pva.v1 is None
        or pva.v2 is None
        or pva.v3 is None
    ):
        return None
    return ((pva.p1, pva.p2, pva.p3), (pva.v1, pva.v2, pva.v3))


def calculate_gravity_schwartz(sin_l: float, alt_msl: float) -> float:
    A1 = 9.7803267715
    A2 = 0.0052790414
    A3 = 0.0000232718
    A4 = -3.0876910891e-6
    A5 = 4.3977311e-9
    A6 = 7.211e-13

    sin2_l = pow(sin_l, 2)
    sin4_l = pow(sin2_l, 2)

    return (
        A1 * (1.0 + A2 * sin2_l + A3 * sin4_l)
        + (A4 + A5 * sin2_l) * alt_msl
        + A6 * pow(alt_msl, 2)
    )


RAD_E = 6378137.0
OMEGA_E = 7.2921151467e-5
F = 1 / 298.257223563
ECC_SQUARE = F * (2 - F)


class EarthModel:
    def __init__(self, pos: NDArray[float64], vel: NDArray[float64]) -> None:
        lat, _lon, alt_msl = pos
        vn, ve, _vd = vel

        self.sin_l = sin(lat)
        self.cos_l = cos(lat)
        self.tan_l = self.sin_l / self.cos_l
        self.sec_l = 1 / self.cos_l
        self.sin_2l = sin(2 * lat)

        self.r_n = meridian_radius(lat)
        self.r_e = transverse_radius(lat)
        self.r_zero = sqrt(self.r_n * self.r_e)

        self.lat_factor = delta_lat_to_north(1, lat, alt_msl)
        self.lon_factor = delta_lon_to_east(1, lat, alt_msl)

        omega_en_n = np.array(
            [
                ve / (self.r_e + alt_msl),
                -vn / (self.r_n + alt_msl),
                -ve * self.tan_l / (self.r_e + alt_msl),
            ]
        )

        omega_ie_n = np.array([OMEGA_E * self.cos_l, 0.0, -OMEGA_E * self.sin_l])

        self.omega_in_n = omega_ie_n + omega_en_n

        self.g_n = np.array([0.0, 0.0, self.calculate_gravity(alt_msl)])

    def calculate_gravity(self, alt_msl: float) -> float:
        return calculate_gravity_schwartz(self.sin_l, alt_msl)


# Explicitly define exports so that we can exclude symbols imported by this file when doing `from navutils import *`.
__all__ = [
    'ECC_SQUARE',
    'OMEGA_E',
    'RAD_E',
    'EarthModel',
    'F',
    'calculate_gravity_schwartz',
    'correct_dcm_with_tilt',
    'dcm_to_quat',
    'dcm_to_rpy',
    'delta_lat_to_north',
    'delta_lon_to_east',
    'east_to_delta_lon',
    'ecef_to_llh',
    'extract_pos_and_vel',
    'llh_to_cen',
    'llh_to_ecef',
    'meridian_radius',
    'north_to_delta_lat',
    'quat_to_dcm',
    'skew',
    'transverse_radius',
]
