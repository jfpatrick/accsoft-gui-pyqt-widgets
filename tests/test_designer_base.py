import pytest
from unittest import mock
import accwidgets._api
from accwidgets._designer_base import designer_user_error, DesignerUserError


@pytest.mark.parametrize("is_designer_value,gui_available,thrown_error,captured_error,captured_msg,expected_final_error,expect_gui_error", [
    (True, True, ImportError, ImportError, None, DesignerUserError, True),
    (True, True, ImportError, ValueError, None, ImportError, False),
    (True, True, TypeError, ValueError, None, TypeError, False),
    (True, True, TypeError, ImportError, None, TypeError, False),
    (True, True, TypeError, TypeError, None, DesignerUserError, True),
    (False, True, ImportError, ImportError, None, ImportError, False),
    (False, True, ImportError, ValueError, None, ImportError, False),
    (False, True, TypeError, ValueError, None, TypeError, False),
    (False, True, TypeError, ImportError, None, TypeError, False),
    (False, True, TypeError, TypeError, None, TypeError, False),
    (True, True, ImportError, ImportError, "Not_matching", ImportError, False),
    (True, True, ImportError, ValueError, "Not_matching", ImportError, False),
    (True, True, TypeError, ValueError, "Not_matching", TypeError, False),
    (True, True, TypeError, ImportError, "Not_matching", TypeError, False),
    (True, True, TypeError, TypeError, "Not_matching", TypeError, False),
    (False, True, ImportError, ImportError, "Not_matching", ImportError, False),
    (False, True, ImportError, ValueError, "Not_matching", ImportError, False),
    (False, True, TypeError, ValueError, "Not_matching", TypeError, False),
    (False, True, TypeError, ImportError, "Not_matching", TypeError, False),
    (False, True, TypeError, TypeError, "Not_matching", TypeError, False),
    (True, True, ImportError("Test"), ImportError, None, DesignerUserError, True),
    (True, True, ImportError("Test"), ValueError, None, ImportError, False),
    (True, True, TypeError("Test"), ValueError, None, TypeError, False),
    (True, True, TypeError("Test"), ImportError, None, TypeError, False),
    (True, True, TypeError("Test"), TypeError, None, DesignerUserError, True),
    (False, True, ImportError("Test"), ImportError, None, ImportError, False),
    (False, True, ImportError("Test"), ValueError, None, ImportError, False),
    (False, True, TypeError("Test"), ValueError, None, TypeError, False),
    (False, True, TypeError("Test"), ImportError, None, TypeError, False),
    (False, True, TypeError("Test"), TypeError, None, TypeError, False),
    (True, True, ImportError("Test"), ImportError, "Not_matching", ImportError, False),
    (True, True, ImportError("Test"), ValueError, "Not_matching", ImportError, False),
    (True, True, TypeError("Test"), ValueError, "Not_matching", TypeError, False),
    (True, True, TypeError("Test"), ImportError, "Not_matching", TypeError, False),
    (False, True, ImportError("Test"), ImportError, "Not_matching", ImportError, False),
    (False, True, ImportError("Test"), ValueError, "Not_matching", ImportError, False),
    (False, True, TypeError("Test"), ValueError, "Not_matching", TypeError, False),
    (False, True, TypeError("Test"), ImportError, "Not_matching", TypeError, False),
    (False, True, TypeError("Test"), TypeError, "Not_matching", TypeError, False),
    (True, True, ImportError("Test"), ImportError, "Test", DesignerUserError, True),
    (True, True, ImportError("Test"), ValueError, "Test", ImportError, False),
    (True, True, TypeError("Test"), ValueError, "Test", TypeError, False),
    (True, True, TypeError("Test"), ImportError, "Test", TypeError, False),
    (True, True, TypeError("Test"), TypeError, "Test", DesignerUserError, True),
    (False, True, ImportError("Test"), ImportError, "Test", ImportError, False),
    (False, True, ImportError("Test"), ValueError, "Test", ImportError, False),
    (False, True, TypeError("Test"), ValueError, "Test", TypeError, False),
    (False, True, TypeError("Test"), ImportError, "Test", TypeError, False),
    (False, True, TypeError("Test"), TypeError, "Test", TypeError, False),
    (True, False, ImportError, ImportError, None, ImportError, False),
    (True, False, ImportError, ValueError, None, ImportError, False),
    (True, False, TypeError, ValueError, None, TypeError, False),
    (True, False, TypeError, ImportError, None, TypeError, False),
    (True, False, TypeError, TypeError, None, TypeError, False),
    (False, False, ImportError, ImportError, None, ImportError, False),
    (False, False, ImportError, ValueError, None, ImportError, False),
    (False, False, TypeError, ValueError, None, TypeError, False),
    (False, False, TypeError, ImportError, None, TypeError, False),
    (False, False, TypeError, TypeError, None, TypeError, False),
    (True, False, ImportError, ImportError, "Not_matching", ImportError, False),
    (True, False, ImportError, ValueError, "Not_matching", ImportError, False),
    (True, False, TypeError, ValueError, "Not_matching", TypeError, False),
    (True, False, TypeError, ImportError, "Not_matching", TypeError, False),
    (True, False, TypeError, TypeError, "Not_matching", TypeError, False),
    (False, False, ImportError, ImportError, "Not_matching", ImportError, False),
    (False, False, ImportError, ValueError, "Not_matching", ImportError, False),
    (False, False, TypeError, ValueError, "Not_matching", TypeError, False),
    (False, False, TypeError, ImportError, "Not_matching", TypeError, False),
    (False, False, TypeError, TypeError, "Not_matching", TypeError, False),
    (True, False, ImportError("Test"), ImportError, None, ImportError, False),
    (True, False, ImportError("Test"), ValueError, None, ImportError, False),
    (True, False, TypeError("Test"), ValueError, None, TypeError, False),
    (True, False, TypeError("Test"), ImportError, None, TypeError, False),
    (True, False, TypeError("Test"), TypeError, None, TypeError, False),
    (False, False, ImportError("Test"), ImportError, None, ImportError, False),
    (False, False, ImportError("Test"), ValueError, None, ImportError, False),
    (False, False, TypeError("Test"), ValueError, None, TypeError, False),
    (False, False, TypeError("Test"), ImportError, None, TypeError, False),
    (False, False, TypeError("Test"), TypeError, None, TypeError, False),
    (True, False, ImportError("Test"), ImportError, "Not_matching", ImportError, False),
    (True, False, ImportError("Test"), ValueError, "Not_matching", ImportError, False),
    (True, False, TypeError("Test"), ValueError, "Not_matching", TypeError, False),
    (True, False, TypeError("Test"), ImportError, "Not_matching", TypeError, False),
    (False, False, ImportError("Test"), ImportError, "Not_matching", ImportError, False),
    (False, False, ImportError("Test"), ValueError, "Not_matching", ImportError, False),
    (False, False, TypeError("Test"), ValueError, "Not_matching", TypeError, False),
    (False, False, TypeError("Test"), ImportError, "Not_matching", TypeError, False),
    (False, False, TypeError("Test"), TypeError, "Not_matching", TypeError, False),
    (True, False, ImportError("Test"), ImportError, "Test", ImportError, False),
    (True, False, ImportError("Test"), ValueError, "Test", ImportError, False),
    (True, False, TypeError("Test"), ValueError, "Test", TypeError, False),
    (True, False, TypeError("Test"), ImportError, "Test", TypeError, False),
    (True, False, TypeError("Test"), TypeError, "Test", TypeError, False),
    (False, False, ImportError("Test"), ImportError, "Test", ImportError, False),
    (False, False, ImportError("Test"), ValueError, "Test", ImportError, False),
    (False, False, TypeError("Test"), ValueError, "Test", TypeError, False),
    (False, False, TypeError("Test"), ImportError, "Test", TypeError, False),
    (False, False, TypeError("Test"), TypeError, "Test", TypeError, False),
])
@mock.patch("qtpy.QtWidgets.QApplication.instance")
@mock.patch("accwidgets._designer_base.QMessageBox.warning")
@mock.patch("accwidgets._designer_base.is_designer")
def test_designer_user_error_shows_gui_error(is_designer, warning, app, qtbot, captured_msg, gui_available,
                                             is_designer_value, thrown_error, expect_gui_error,
                                             captured_error, expected_final_error):
    _ = qtbot
    widget = mock.MagicMock()
    widget.isVisible.return_value = gui_available
    app.return_value.topLevelWidgets.return_value = [widget]
    is_designer.return_value = is_designer_value
    with pytest.raises(expected_final_error):
        with designer_user_error(captured_error, match=captured_msg):
            raise thrown_error
    if expect_gui_error:
        warning.assert_called_once_with(mock.ANY, "Error occurred", mock.ANY)
    else:
        warning.assert_not_called()


@pytest.mark.parametrize("is_designer_value,should_disable_cache", [
    (True, True),
    (False, False),
])
@mock.patch("accwidgets._designer_base.is_designer")
def test_designer_user_error_does_not_use_assert_cache_in_designer(is_designer, qtbot, is_designer_value, should_disable_cache):
    _ = qtbot
    is_designer.return_value = is_designer_value
    assert accwidgets._api._ASSERT_CACHE_ENABLED
    with designer_user_error(ImportError):
        assert accwidgets._api._ASSERT_CACHE_ENABLED != should_disable_cache
    assert accwidgets._api._ASSERT_CACHE_ENABLED