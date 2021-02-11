import pytest
import sys
from unittest import mock
from typing import Optional, Any
from accwidgets._api import mark_public_api, assert_dependencies, assert_requirement

try:
    # Python >=3.8
    from importlib.metadata import PackageNotFoundError  # type: ignore  # mypy fails this in Python 3.7
except ImportError:
    # Python <3.8
    from importlib_metadata import PackageNotFoundError


@pytest.fixture(scope="function", autouse=True)
def test_fn_wrapper():
    import accwidgets._api
    accwidgets._api._ASSERT_CACHE.clear()
    yield
    accwidgets._api._ASSERT_CACHE.clear()
    try:
        del sys.modules["accwidgets.test_widget.__deps__"]
    except KeyError:
        pass


@pytest.fixture
def custom_class():
    class TestClass:

        class InnerTestClass:
            pass

        pass

    return TestClass


@pytest.fixture
def environ_get_side_effect():

    def _wrapper(override_deps_defined: bool, override_deps_value: bool):

        def get_environ(key: str, default_value: Optional[Any] = None):
            if override_deps_defined and key == "ACCWIDGETS_OVERRIDE_DEPENDENCIES":
                return override_deps_value
            return default_value

        return get_environ

    return _wrapper


@pytest.fixture
def inject_mod_side_effect():

    def _wrapper(mock_obj: mock.Mock):

        def side_effect(pkg_name: str):
            sys.modules[pkg_name] = mock_obj

        return side_effect

    return _wrapper


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


@pytest.mark.parametrize("marker_exists,marker_evaluates,should_create_distribution", [
    (True, True, True),
    (True, False, False),
    (False, False, True),
])
@mock.patch("accwidgets._api.distribution")
def test_assert_requirement_ignored_with_irrelevant_marker(distribution, marker_exists, marker_evaluates, should_create_distribution):
    # should_create_distribution checks whether function returns early or not
    req = mock.MagicMock()
    if marker_exists:
        req.marker.evaluate.return_value = marker_evaluates
    else:
        req.marker = None
    assert_requirement(req=req, widget_name="test_widget")
    if should_create_distribution:
        distribution.assert_called_once()
    else:
        distribution.assert_not_called()


@pytest.mark.parametrize("override_deps_defined,override_deps_value", [
    (True, True),
    (True, False),
    (False, False),
])
@mock.patch("os.environ")
@mock.patch("accwidgets._api.distribution")
def test_assert_requirement_throws_on_package_not_found(distribution, environ, override_deps_defined, override_deps_value, environ_get_side_effect):
    environ.get.side_effect = environ_get_side_effect(override_deps_defined, override_deps_value)
    distribution.side_effect = PackageNotFoundError("test_req")
    req = mock.MagicMock()
    req.name = "test_req"
    req.marker = None

    with pytest.raises(ImportError, match='accwidgets.test_widget is intended to be used with "test_req" package. '
                                          "Please specify this widget as an extra of your accwidgets dependency, "
                                          r"e.g. accwidgets\[test_widget\] in order to keep using the widget. To "
                                          "quickly install it in the environment, use: 'pip install "
                                          r"accwidgets\[test_widget\]'.\n\nNo package metadata was found for test_req"):
        assert_requirement(req=req, widget_name="test_widget")


@pytest.mark.parametrize("override_deps_defined,override_deps_value,requirement_correct,should_throw", [
    (True, True, False, False),
    (True, False, False, True),
    (False, False, False, True),
    (True, True, True, False),
    (True, False, True, False),
    (False, False, True, False),
])
@mock.patch("os.environ")
@mock.patch("accwidgets._api.distribution")
def test_assert_requirement_throws_on_wrong_version(_, environ, override_deps_defined, override_deps_value, requirement_correct, should_throw, environ_get_side_effect):
    environ.get.side_effect = environ_get_side_effect(override_deps_defined, override_deps_value)
    req = mock.MagicMock()
    req.name = "test_req"
    req.marker = None
    req.specifier.__str__.return_value = "==test_version"
    req.specifier.contains.return_value = requirement_correct

    if should_throw:
        with pytest.raises(ImportError, match="accwidgets.test_widget cannot reliably work with test_req versions "
                                              "other than test_req==test_version. Please specify this widget as an "
                                              r"extra of your accwidgets dependency, e\.g\. accwidgets\[test_widget\] in "
                                              "order to keep using the widget. To quickly install it in the "
                                              r"environment, use: 'pip install accwidgets\[test_widget\]'\.\nYou can "
                                              "override this limitation by setting an environment variable "
                                              "ACCWIDGETS_OVERRIDE_DEPENDENCIES=1."):
            assert_requirement(req=req, widget_name="test_widget")
    else:
        assert_requirement(req=req, widget_name="test_widget")


@pytest.mark.parametrize("base_path,widget_name,expected_pkg_name", [
    ("/path/to/test_widget", "test_widget", "accwidgets.test_widget.__deps__"),
    ("/path/to/test_widget/__init__.py", "test_widget", "accwidgets.test_widget.__deps__"),
    ("/path/to/another_widget/__init__.py", "another_widget", "accwidgets.another_widget.__deps__"),
])
@mock.patch("importlib.import_module", side_effect=ImportError)  # To exit early, as we don't need to test later code
def test_assert_dependencies_works_with_both_init_and_parent_dir(import_module, base_path, widget_name, expected_pkg_name):
    assert_dependencies(base_path=base_path)
    import_module.assert_called_once_with(expected_pkg_name)
    import accwidgets._api
    assert accwidgets._api._ASSERT_CACHE == {widget_name}


@mock.patch("importlib.import_module", side_effect=ImportError)  # To exit early, as we don't need to test later code
def test_assert_dependencies_evaluates_once_per_widget(import_module):
    import_module.assert_not_called()
    assert_dependencies(base_path="/path/to/test_widget")
    import_module.assert_called_once()
    import_module.reset_mock()
    import_module.assert_not_called()
    assert_dependencies(base_path="/path/to/test_widget")
    import_module.assert_not_called()


@mock.patch("importlib.import_module", side_effect=ImportError)
@mock.patch("packaging.requirements.Requirement")
def test_assert_dependencies_ignored_when_deps_not_defined(Requirement, _):
    assert_dependencies(base_path="/path/to/test_widget")
    Requirement.assert_not_called()  # Verify that method exited early


@mock.patch("importlib.import_module")
@mock.patch("packaging.requirements.Requirement")
def test_assert_dependencies_ignored_when_deps_badly_formatted(Requirement, import_module, inject_mod_side_effect):
    mock_obj = mock.MagicMock(spec=object)  # spec to remove autostubs and cause AttributeError on 'core' attribute access
    import_module.side_effect = inject_mod_side_effect(mock_obj)
    assert_dependencies(base_path="/path/to/test_widget")
    Requirement.assert_not_called()  # Verify that method exited early


@pytest.mark.parametrize("raise_error", [True, False])
@pytest.mark.parametrize("requirements,warning", [
    (["pyjapc", "==1.0"], r"Failed to parse dependency ==1\.0\. This constraint will be ignored\.*"),
    (["pkg>=0.1,2"], r"Failed to parse dependency pkg>=0\.1,2\. This constraint will be ignored\.*"),
    (["pkg==0.1;unknown_specifier='something'"], r"Failed to parse dependency pkg==0\.1;unknown_specifier='something'\. This constraint will be ignored\.*"),
])
@mock.patch("importlib.import_module")
@mock.patch("accwidgets._api.assert_requirement")
def test_assert_dependencies_warns_on_invalid_requirement(_, import_module, inject_mod_side_effect, requirements, raise_error, warning):
    mock_obj = mock.MagicMock()
    mock_obj.core = requirements
    import_module.side_effect = inject_mod_side_effect(mock_obj)
    with pytest.warns(UserWarning, match=warning):
        assert_dependencies(base_path="/path/to/test_widget", raise_error=raise_error)


@pytest.mark.parametrize("raise_error", [True, False])
@pytest.mark.parametrize("actual_version,requirement", [
    ("1.1", "test_package>1.1"),
    ("1.1", "test_package<1.1a0"),
    ("1.1", "test_package!=1.1"),
    ("1.1", "test_package<=2,>1.5"),
    ("1.1", "test_package==1.1.post0"),
    ("1.1", "test_package==1.1a0"),
    ("1.1", "test_package~=1.0.0"),
    ("2", "test_package~=1.0"),
])
@mock.patch("importlib.import_module")
@mock.patch("accwidgets._api.distribution")
def test_assert_dependencies_throws_with_unmet_requirement(distribution, import_module, inject_mod_side_effect, actual_version, requirement, raise_error):
    mock_obj = mock.MagicMock()
    mock_obj.core = [requirement]
    import_module.side_effect = inject_mod_side_effect(mock_obj)
    distribution.return_value.version = actual_version
    expected_message = "accwidgets.test_widget cannot reliably work with test_package versions other than " \
                       f"{requirement}. Please specify this widget as an extra of your accwidgets dependency, e.g." \
                       r" accwidgets\[test_widget\] in order to keep using the widget\. To quickly install it " \
                       r"in the environment, use: 'pip install accwidgets\[test_widget\]'\.\n" \
                       "You can override this limitation by setting an environment variable " \
                       "ACCWIDGETS_OVERRIDE_DEPENDENCIES=1."

    if raise_error:
        with pytest.raises(ImportError, match=expected_message):
            assert_dependencies(base_path="/path/to/test_widget", raise_error=raise_error)
    else:
        with pytest.warns(UserWarning, match=expected_message):
            assert_dependencies(base_path="/path/to/test_widget", raise_error=raise_error)


@pytest.mark.parametrize("raise_error", [True, False])
@pytest.mark.parametrize("actual_version,requirement", [
    ("1.1", "test_package>=0.9,<2"),
    ("1.1", "test_package>=0.9"),
    ("1.1", "test_package>0.9"),
    ("1.1", "test_package<=2"),
    ("1.1", "test_package<2"),
    ("1.1", "test_package>1.1b1"),
    ("1.1", "test_package==1.1"),
    ("1.1", "test_package!=1.0"),
    ("1.1", "test_package"),
    ("1.1", "test_package@git+https://example.com#egg=test_package"),
    ("1.1.2", "test_package~=1.1.0"),
    ("1.2", "test_package~=1.1"),
    ("1.1", "test_package<0.1;python_version<'3.2'"),
])
@mock.patch("importlib.import_module")
@mock.patch("accwidgets._api.distribution")
def test_assert_dependencies_succeeds(distribution, import_module, inject_mod_side_effect, raise_error, actual_version, requirement):
    mock_obj = mock.MagicMock()
    mock_obj.core = [requirement]
    import_module.side_effect = inject_mod_side_effect(mock_obj)
    distribution.return_value.version = actual_version
    assert_dependencies(base_path="/path/to/test_widget", raise_error=raise_error)
