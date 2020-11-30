import pytest
import re
from freezegun import freeze_time
from pytestqt.qtbot import QtBot
from datetime import datetime
from dateutil.tz import UTC
from unittest import mock
from qtpy.QtGui import QIcon
from accwidgets.app_frame._about_dialog import AboutDialog


# We have to make the freeze time utc, otherwise freeze-gun seems to
# take the current timezone which lets tests fail
STATIC_TIME = datetime(year=2020, day=1, month=1, hour=4, minute=43, second=5, microsecond=214923, tzinfo=UTC)


@mock.patch("accwidgets.app_frame._about_dialog.QDialog.setWindowIcon")
def test_about_dialog_sets_window_icon(setWindowIcon, qtbot: QtBot):
    icon = QIcon("custom_file.png")
    setWindowIcon.assert_not_called()
    dialog = AboutDialog(app_name="Test app", version="version", icon=icon)
    qtbot.add_widget(dialog)
    setWindowIcon.assert_called_with(icon)


@pytest.mark.parametrize("app_name,version,expected_text", [
    ("Test app", "0.0.1", "<p>Test app</p><p>Version: 0.0.1</p><p>CERN © 2020</p>"),
    ("Test app", "1.2", "<p>Test app</p><p>Version: 1.2</p><p>CERN © 2020</p>"),
    ("Test app", "3.5-beta4", "<p>Test app</p><p>Version: 3.5-beta4</p><p>CERN © 2020</p>"),
    ("my_other_app", "4.0a0.post0+43ebdc", "<p>my_other_app</p><p>Version: 4.0a0.post0+43ebdc</p><p>CERN © 2020</p>"),
])
@freeze_time(STATIC_TIME)
def test_about_dialog_sets_info_label(qtbot: QtBot, app_name, version, expected_text):
    dialog = AboutDialog(app_name=app_name, version=version, icon=QIcon())
    qtbot.add_widget(dialog)
    match = re.search(r"<body.*?>(?P<contents>.*)<\/body>", dialog.contents.text())
    assert match is not None
    assert match.group("contents") == expected_text
