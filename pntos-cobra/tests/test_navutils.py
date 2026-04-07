import numpy as np
import pytest
from navtk.navutils import skew as navtk_skew
from pntos.cobra.utils import (
    delta_lat_to_north,
    delta_lon_to_east,
    east_to_delta_lon,
    north_to_delta_lat,
    skew,
)

APPROX_LAT = np.rad2deg(39.0)
APPROX_ALT = 1000
NORTH_DISTANCES = np.array([0.1, 2, 30, 400, 5000, 60000])
EAST_DISTANCES = np.array([0.1, 2, 30, 400, 5000, 60000])
DELTA_LATS = np.array(
    [
        1.56903478e-08,
        3.13806956e-07,
        4.70710434e-06,
        6.27613911e-05,
        7.84517389e-04,
        9.41420867e-03,
    ]
)
DELTA_LONS = np.array(
    [
        -2.40651610e-08,
        -4.81303219e-07,
        -7.21954829e-06,
        -9.62606439e-05,
        -1.20325805e-03,
        -1.44390966e-02,
    ]
)


def test_north_to_delta_lat() -> None:
    # Single point
    delta_lat = north_to_delta_lat(NORTH_DISTANCES[0], APPROX_LAT, APPROX_ALT)
    assert isinstance(delta_lat, float)
    assert delta_lat == pytest.approx(DELTA_LATS[0])

    # Batch of points
    delta_lats = north_to_delta_lat(NORTH_DISTANCES, APPROX_LAT, APPROX_ALT)
    assert np.allclose(delta_lats, DELTA_LATS)


def test_east_to_delta_lon() -> None:
    # Single point
    delta_lon = east_to_delta_lon(EAST_DISTANCES[0], APPROX_LAT, APPROX_ALT)
    assert isinstance(delta_lon, float)
    assert delta_lon == pytest.approx(DELTA_LONS[0])

    # Batch of points
    delta_lons = east_to_delta_lon(EAST_DISTANCES, APPROX_LAT, APPROX_ALT)
    assert np.allclose(delta_lons, DELTA_LONS)


def test_delta_lat_to_north() -> None:
    # Single point
    north_distance = delta_lat_to_north(DELTA_LATS[0], APPROX_LAT, APPROX_ALT)
    assert isinstance(north_distance, float)
    assert north_distance == pytest.approx(NORTH_DISTANCES[0])

    # Batch of points
    north_distances = delta_lat_to_north(DELTA_LATS, APPROX_LAT, APPROX_ALT)
    assert np.allclose(north_distances, NORTH_DISTANCES)


def test_delta_lon_to_east() -> None:
    # Single point
    east_distance = delta_lon_to_east(DELTA_LONS[0], APPROX_LAT, APPROX_ALT)
    assert isinstance(east_distance, float)
    assert east_distance == pytest.approx(EAST_DISTANCES[0])

    # Batch of points
    east_distances = delta_lon_to_east(DELTA_LONS, APPROX_LAT, APPROX_ALT)
    assert np.allclose(east_distances, EAST_DISTANCES)


def test_skew() -> None:
    vec = np.random.random(3)
    skew_mat = skew(vec)
    navtk_skew_mat = navtk_skew(vec)
    assert np.allclose(skew_mat, navtk_skew_mat)

    vecs = np.random.random((10, 3))
    skew_mats = skew(vecs)
    for idx in range(vecs.shape[0]):
        navtk_skew_mat = navtk_skew(vecs[idx])
        assert np.allclose(skew_mats[idx], navtk_skew_mat)
