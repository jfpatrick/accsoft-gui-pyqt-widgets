import pytest
from accwidgets._api import mark_public_api


@pytest.fixture
def custom_class():
    class TestClass:

        class InnerTestClass:
            pass

        pass

    return TestClass


@pytest.mark.parametrize("input", [
    1,
    "string",
    object(),
])
def test_mark_public_api_ignores_not_classes(input):
    assert not hasattr(input, "__module__")
    mark_public_api(input, public_mod_name="test.mod")
    assert not hasattr(input, "__module__")


def test_mark_public_api_ignores_repeated_api(custom_class):
    assert custom_class.__module__ != "test.mod1"
    mark_public_api(custom_class, public_mod_name="test.mod1")
    assert custom_class.__module__ == "test.mod1"
    mark_public_api(custom_class, public_mod_name="test.mod2")
    assert custom_class.__module__ == "test.mod1"


def test_mark_public_api_modifies_modules(custom_class):
    orig_module = custom_class.__module__
    assert orig_module != "test.mod"
    mark_public_api(custom_class, public_mod_name="test.mod")
    assert custom_class.__module__ != orig_module
    assert custom_class.__module__ == "test.mod"
    assert custom_class.__accwidgets_real_module__ == orig_module


def test_mark_public_api_modifies_inner_classes_from_same_hierarchy(custom_class):
    custom_class.InnerTestClass.__module__ = "test.mod.subpackage"
    mark_public_api(custom_class, public_mod_name="test.mod")
    assert custom_class.InnerTestClass.__module__ != "test.mod.subpackage"
    assert custom_class.InnerTestClass.__module__ == "test.mod"
    assert custom_class.InnerTestClass.__accwidgets_real_module__ == "test.mod.subpackage"


def test_mark_public_api_ingores_inner_classes_from_different_hierarchy(custom_class):
    custom_class.InnerTestClass.__module__ = "different.mod.hierarchy"
    mark_public_api(custom_class, public_mod_name="test.mod")
    assert custom_class.InnerTestClass.__module__ == "different.mod.hierarchy"
    assert not hasattr(custom_class.InnerTestClass, "__accwidgets_real_module__")
