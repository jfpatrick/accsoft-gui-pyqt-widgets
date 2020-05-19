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
    t = TimeSpan(left=32.0)
    assert t.left_boundary_offset == 32.0
    assert t.right_boundary_offset == 0.0
    assert t.finite
    assert t.size == 32.0


def test_time_span_only_left_inf():
    t = TimeSpan(left=np.inf)
    assert np.isinf(t.left_boundary_offset)
    assert t.right_boundary_offset == 0.0
    assert not t.finite
    assert np.isinf(t.size)


def test_time_span_only_left_nan():
    t = TimeSpan(left=np.nan)
    assert np.isinf(t.left_boundary_offset)
    assert t.right_boundary_offset == 0.0
    assert not t.finite
    assert np.isinf(t.size)


def test_time_span_both():
    t = TimeSpan(left=32.0, right=2.0)
    assert t.left_boundary_offset == 32.0
    assert t.right_boundary_offset == 2.0
    assert t.finite
    assert t.size == 30.0


def test_time_span_both_invalid():
    with pytest.raises(ValueError):
        TimeSpan(left=3.0, right=33.0)


def test_time_span_both_right_nan():
    t = TimeSpan(left=32.0, right=np.nan)
    assert t.left_boundary_offset == 32.0
    assert t.right_boundary_offset == 0.0
    assert t.finite
    assert t.size == 32.0


def test_time_span_both_right_inf():
    t = TimeSpan(left=32.0, right=np.inf)
    assert t.left_boundary_offset == 32.0
    assert t.right_boundary_offset == 0.0
    assert t.finite
    assert t.size == 32.0


def test_time_span_both_right_negative():
    t = TimeSpan(left=32.0, right=-2.0)
    assert t.left_boundary_offset == 32.0
    assert t.right_boundary_offset == -2.0
    assert t.finite
    assert t.size == 34.0
