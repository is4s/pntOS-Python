from math import atan2, cos, sin, sqrt

import numpy as np
from numpy.typing import NDArray


def skew(angles):
    return np.array(
        [
            [0, -angles[2], angles[1]],
            [angles[2], 0, -angles[0]],
            [-angles[1], angles[0], 0],
        ]
    )


def meridian_radius(lat):
    sin_lat = sin(lat)
    return RAD_E * (1 - ECC_SQUARE) / pow(1 - ECC_SQUARE * sin_lat * sin_lat, 1.5)


def transverse_radius(lat):
    sin_lat = sin(lat)
    return RAD_E / pow(1 - ECC_SQUARE * sin_lat * sin_lat, 0.5)


def calc_lat_factor(lat, alt):
    return meridian_radius(lat) + alt


def calc_lon_factor(lat, alt):
    return (transverse_radius(lat) + alt) * cos(lat)


def quat_to_dcm(quat: NDArray):
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


def llh_to_ecef(llh: NDArray) -> NDArray:
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


def ecef_to_llh(ecef: NDArray) -> NDArray:
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

    while (abs(dp0) > 7e-6 or abs(dp1) > 1e-6) and count <= max_iterations:
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


def llh_to_cen(llh: NDArray) -> NDArray:
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


RAD_E = 6378137.0
OMEGA_E = 7.2921151467e-5
F = 1 / 298.257223563
ECC_SQUARE = F * (2 - F)


class EarthModel:
    A1 = 9.7803267715
    A2 = 0.0052790414
    A3 = 0.0000232718
    A4 = -3.0876910891e-6
    A5 = 4.3977311e-9
    A6 = 7.211e-13

    def __init__(self, pos: NDArray, vel: NDArray):
        lat, lon, alt_msl = pos
        vn, ve, vd = vel

        self.sin_l = sin(lat)
        self.cos_l = cos(lat)
        self.tan_l = self.sin_l / self.cos_l
        self.sec_l = 1 / self.cos_l
        self.sin_2l = sin(2 * lat)

        self.r_n = meridian_radius(lat)
        self.r_e = transverse_radius(lat)
        self.r_zero = sqrt(self.r_n * self.r_e)

        self.lat_factor = calc_lat_factor(lat, alt_msl)
        self.lon_factor = calc_lon_factor(lat, alt_msl)

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

    def calculate_gravity(self, alt_msl):
        # Calculate gravity using Schwartz model
        sin2_l = pow(self.sin_l, 2)
        sin4_l = pow(sin2_l, 2)

        return (
            self.A1 * (1.0 + self.A2 * sin2_l + self.A3 * sin4_l)
            + (self.A4 + self.A5 * sin2_l) * alt_msl
            + self.A6 * pow(alt_msl, 2)
        )


# Explicitly define exports so that we can exclude symbosl imported by this file when doing `from navutils import *`.
__all__ = [
    'skew',
    'meridian_radius',
    'transverse_radius',
    'calc_lat_factor',
    'calc_lon_factor',
    'EarthModel',
    'quat_to_dcm',
    'llh_to_ecef',
    'ecef_to_llh',
    'llh_to_cen',
    'RAD_E',
    'OMEGA_E',
    'F',
    'ECC_SQUARE',
]
