import pytest
from accwidgets._deprecations import deprecated_param_alias


@pytest.fixture
def deprecated_fn():
    @deprecated_param_alias(a2="b2", a3="b3")
    def fn(a1, b2, b3, a4):
        return a1, b2, b3, a4
    return fn


@pytest.mark.parametrize(
    "args,"
    "kwargs,"
    "expected_warnings", [
        ([], {"a1": 1, "b2": 2, "b3": 3, "a4": 4}, []),
        ([], {"a1": 1, "a2": 2, "a3": 3, "a4": 4}, ["Keyword-argument 'a2' in function 'fn' is deprecated, use 'b2'.",
                                                    "Keyword-argument 'a3' in function 'fn' is deprecated, use 'b3'."]),
        ([], {"a1": 1, "a2": 2, "b3": 3, "a4": 4}, ["Keyword-argument 'a2' in function 'fn' is deprecated, use 'b2'."]),
        ([], {"a1": 1, "b2": 2, "a3": 3, "a4": 4}, ["Keyword-argument 'a3' in function 'fn' is deprecated, use 'b3'."]),
        ([1], {"b2": 2, "b3": 3, "a4": 4}, []),
        ([1], {"a2": 2, "a3": 3, "a4": 4}, ["Keyword-argument 'a2' in function 'fn' is deprecated, use 'b2'.",
                                            "Keyword-argument 'a3' in function 'fn' is deprecated, use 'b3'."]),
        ([1], {"a2": 2, "b3": 3, "a4": 4}, ["Keyword-argument 'a2' in function 'fn' is deprecated, use 'b2'."]),
        ([1], {"b2": 2, "a3": 3, "a4": 4}, ["Keyword-argument 'a3' in function 'fn' is deprecated, use 'b3'."]),
        ([1, 2], {"b3": 3, "a4": 4}, []),
        ([1, 2], {"a3": 3, "a4": 4}, ["Keyword-argument 'a3' in function 'fn' is deprecated, use 'b3'."]),
        ([1, 2, 3], {"a4": 4}, []),
        ((1, 2, 3, 4), {}, []),
    ])
def test_fn_arg_deprecations(recwarn, args, kwargs, expected_warnings, deprecated_fn):
    res1, res2, res3, res4 = deprecated_fn(*args, **kwargs)
    assert res1 == 1
    assert res2 == 2
    assert res3 == 3
    assert res4 == 4
    actual_warnings = [recorded.message.args[0] for recorded in recwarn]
    assert actual_warnings == expected_warnings


def test_fn_arg_deprecation_exc(deprecated_fn):
    with pytest.raises(TypeError, match="'fn' received both 'a2' and 'b2'"):
        deprecated_fn(a1=1, a2=2, b2=2, a3=3)
