import pytest
import numpy as np
from accwidgets.graph import TimeSpan


def test_time_span_default_params():
    t = TimeSpan()
    assert np.isinf(t.left_boundary_offset)
    assert t.right_boundary_offset == 0.0
    assert not t.finite
    assert np.isinf(t.size)


def test_time_span_only_left():
    t = TimeSpan(32.0)
    assert t.left_boundary_offset == 32.0
    assert t.right_boundary_offset == 0.0
    assert t.finite
    assert t.size == 32.0


def test_time_span_only_left_none():
    t = TimeSpan(None)
    assert np.isinf(t.left_boundary_offset)
    assert t.right_boundary_offset == 0.0
    assert not t.finite
    assert np.isinf(t.size)


def test_time_span_only_left_inf():
    t = TimeSpan(np.inf)
    assert np.isinf(t.left_boundary_offset)
    assert t.right_boundary_offset == 0.0
    assert not t.finite
    assert np.isinf(t.size)


def test_time_span_only_left_nan():
    t = TimeSpan(np.nan)
    assert np.isinf(t.left_boundary_offset)
    assert t.right_boundary_offset == 0.0
    assert not t.finite
    assert np.isinf(t.size)


def test_time_span_both():
    t = TimeSpan(32.0, 2.0)
    assert t.left_boundary_offset == 32.0
    assert t.right_boundary_offset == 2.0
    assert t.finite
    assert t.size == 30.0


def test_time_span_both_invalid():
    with pytest.raises(ValueError):
        TimeSpan(3.0, 33.0)


def test_time_span_both_right_none():
    t = TimeSpan(32.0, None)
    assert t.left_boundary_offset == 32.0
    assert t.right_boundary_offset == 0.0
    assert t.finite
    assert t.size == 32.0


def test_time_span_both_right_nan():
    t = TimeSpan(32.0, np.nan)
    assert t.left_boundary_offset == 32.0
    assert t.right_boundary_offset == 0.0
    assert t.finite
    assert t.size == 32.0


def test_time_span_both_right_inf():
    t = TimeSpan(32.0, np.inf)
    assert t.left_boundary_offset == 32.0
    assert t.right_boundary_offset == 0.0
    assert t.finite
    assert t.size == 32.0


def test_time_span_both_right_negative():
    t = TimeSpan(32.0, -2.0)
    assert t.left_boundary_offset == 32.0
    assert t.right_boundary_offset == -2.0
    assert t.finite
    assert t.size == 34.0
