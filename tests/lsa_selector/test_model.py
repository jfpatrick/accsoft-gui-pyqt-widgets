import sys
import pytest
import operator
from typing import cast, Set, Iterable, List, Tuple, Optional
from datetime import datetime
from pytestqt.qtbot import QtBot
from unittest import mock
from qtpy.QtGui import QColor, QFont
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QTableView
from accwidgets.lsa_selector import (LsaSelectorNonMultiplexedResidentContext, LsaSelectorMultiplexedResidentContext,
                                     AbstractLsaSelectorContext, LsaSelectorModel, LsaSelectorAccelerator,
                                     LsaSelectorColorRole, LsaSelectorNonResidentContext)
from accwidgets.lsa_selector._model import (LsaSelectorRowViewModel, LsaSelectorFilterModel, LsaSelectorTableModel,
                                            LsaSelectorTooltipInfo, contexts_for_accelerator)


@pytest.fixture(autouse=True, scope="function")
def mock_java_imports():
    sys.modules["java"] = mock.MagicMock()
    sys.modules["java.util"] = mock.MagicMock()
    sys.modules["cern"] = mock.MagicMock()
    sys.modules["cern.accsoft"] = mock.MagicMock()
    sys.modules["cern.accsoft.commons"] = mock.MagicMock()
    sys.modules["cern.accsoft.commons.domain"] = mock.MagicMock()
    sys.modules["cern.lsa"] = mock.MagicMock()
    sys.modules["cern.lsa.client"] = mock.MagicMock()
    sys.modules["cern.lsa.domain"] = mock.MagicMock()
    sys.modules["cern.lsa.domain.settings"] = mock.MagicMock()
    yield
    del sys.modules["java"]
    del sys.modules["java.util"]
    del sys.modules["cern"]
    del sys.modules["cern.accsoft"]
    del sys.modules["cern.accsoft.commons"]
    del sys.modules["cern.accsoft.commons.domain"]
    del sys.modules["cern.lsa"]
    del sys.modules["cern.lsa.client"]
    del sys.modules["cern.lsa.domain"]
    del sys.modules["cern.lsa.domain.settings"]


@pytest.mark.parametrize("ctx_type,extra_args,allows_user", [
    (LsaSelectorMultiplexedResidentContext, {"user_type": LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL}, True),
    (LsaSelectorNonMultiplexedResidentContext, {}, False),
])
def test_non_multiplexed_resident_context_cannot_receive_user(ctx_type, extra_args, allows_user):
    all_args = {
        "name": "test_name",
        "user": "TEST.USER.ALL",
        "category": AbstractLsaSelectorContext.Category.OPERATIONAL,
        **extra_args,
    }
    if allows_user:
        ctx_type(**all_args)
    else:
        with pytest.raises(TypeError):
            ctx_type(**all_args)


def test_non_multiplexed_resident_context_always_empty_user():
    ctx = LsaSelectorNonMultiplexedResidentContext(name="test_name",
                                                   category=AbstractLsaSelectorContext.Category.OPERATIONAL)
    assert ctx.user == ""


@pytest.mark.parametrize("is_designer_value,provided_client_id,expected_client_id", [
    (True, "given", "given"),
    (False, "given", "given"),
    (True, None, None),
    (False, None, "default"),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator", return_value=[])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
@mock.patch("accwidgets.lsa_selector._model.is_designer")
def test_model_creates_default_lsa_client(is_designer, LSAClient, _, is_designer_value, provided_client_id, expected_client_id):
    is_designer.return_value = is_designer_value

    LSAClient.return_value.client_id = "default"

    if provided_client_id is None:
        provided_client = None
    else:
        provided_client = mock.MagicMock()
        provided_client.client_id = "given"

    model = LsaSelectorModel(lsa=provided_client)
    if expected_client_id is None:
        assert model._lsa is None
    else:
        assert model._lsa.client_id == expected_client_id


@pytest.mark.parametrize("is_designer_value,expect_call_lsa", [
    (True, False),
    (False, True),
])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
@mock.patch("accwidgets.lsa_selector._model.is_designer")
def test_model_calls_lsa_on_init(is_designer, LSAClient, is_designer_value, expect_call_lsa):
    is_designer.return_value = is_designer_value
    LSAClient.return_value.java_api.assert_not_called()
    LsaSelectorModel()
    if expect_call_lsa:
        LSAClient.return_value.java_api.assert_called_once()
    else:
        LSAClient.return_value.java_api.assert_not_called()


@pytest.mark.parametrize("initial_acc,expected_initial_acc", [
    (LsaSelectorAccelerator.AD, LsaSelectorAccelerator.AD),
    (LsaSelectorAccelerator.CTF, LsaSelectorAccelerator.CTF),
    (LsaSelectorAccelerator.ISOLDE, LsaSelectorAccelerator.ISOLDE),
    (LsaSelectorAccelerator.LEIR, LsaSelectorAccelerator.LEIR),
    (LsaSelectorAccelerator.LHC, LsaSelectorAccelerator.LHC),
    (LsaSelectorAccelerator.PS, LsaSelectorAccelerator.PS),
    (LsaSelectorAccelerator.PSB, LsaSelectorAccelerator.PSB),
    (LsaSelectorAccelerator.SPS, LsaSelectorAccelerator.SPS),
    (LsaSelectorAccelerator.NORTH, LsaSelectorAccelerator.NORTH),
    (LsaSelectorAccelerator.AWAKE, LsaSelectorAccelerator.AWAKE),
    (LsaSelectorAccelerator.ELENA, LsaSelectorAccelerator.ELENA),
])
@pytest.mark.parametrize("new_acc,expected_new_acc", [
    (LsaSelectorAccelerator.AD, LsaSelectorAccelerator.AD),
    (LsaSelectorAccelerator.CTF, LsaSelectorAccelerator.CTF),
    (LsaSelectorAccelerator.ISOLDE, LsaSelectorAccelerator.ISOLDE),
    (LsaSelectorAccelerator.LEIR, LsaSelectorAccelerator.LEIR),
    (LsaSelectorAccelerator.LHC, LsaSelectorAccelerator.LHC),
    (LsaSelectorAccelerator.PS, LsaSelectorAccelerator.PS),
    (LsaSelectorAccelerator.PSB, LsaSelectorAccelerator.PSB),
    (LsaSelectorAccelerator.SPS, LsaSelectorAccelerator.SPS),
    (LsaSelectorAccelerator.NORTH, LsaSelectorAccelerator.NORTH),
    (LsaSelectorAccelerator.AWAKE, LsaSelectorAccelerator.AWAKE),
    (LsaSelectorAccelerator.ELENA, LsaSelectorAccelerator.ELENA),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator", return_value=[])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
def test_model_accelerator_prop(_, __, initial_acc, expected_initial_acc, new_acc, expected_new_acc):
    model = LsaSelectorModel(accelerator=initial_acc)
    assert model.accelerator == expected_initial_acc
    model.accelerator = new_acc
    assert model.accelerator == expected_new_acc


@pytest.mark.parametrize("initial_acc,new_acc,expect_refetch", [
    (LsaSelectorAccelerator.LHC, LsaSelectorAccelerator.LHC, False),
    (LsaSelectorAccelerator.LHC, LsaSelectorAccelerator.PSB, True),
    (LsaSelectorAccelerator.PSB, LsaSelectorAccelerator.LHC, True),
    (LsaSelectorAccelerator.PSB, LsaSelectorAccelerator.PSB, False),
    (LsaSelectorAccelerator.PSB, LsaSelectorAccelerator.LEIR, True),
    (LsaSelectorAccelerator.ELENA, LsaSelectorAccelerator.LEIR, True),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator", return_value=[])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
def test_model_set_accelerator_refetches_data(_, __, initial_acc, new_acc, expect_refetch):
    model = LsaSelectorModel(accelerator=initial_acc)
    with mock.patch.object(model, "refetch") as refetch:
        model.accelerator = new_acc
        if expect_refetch:
            refetch.assert_called_once()
        else:
            refetch.assert_not_called()


@pytest.mark.parametrize("initial_val,expected_initial_val", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("new_val,expected_new_val", [
    (True, True),
    (False, False),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator", return_value=[])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
def test_model_resident_only_prop(_, __, initial_val, expected_initial_val, new_val, expected_new_val):
    model = LsaSelectorModel(resident_only=initial_val)
    assert model.resident_only == expected_initial_val
    model.resident_only = new_val
    assert model.resident_only == expected_new_val


@pytest.mark.parametrize("initial_val,new_val,expect_refetch", [
    (True, True, False),
    (True, False, True),
    (False, True, True),
    (False, False, False),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator", return_value=[])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
def test_model_set_resident_only_refetches_data(_, __, initial_val, new_val, expect_refetch):
    model = LsaSelectorModel(resident_only=initial_val)
    with mock.patch.object(model, "refetch") as refetch:
        model.resident_only = new_val
        if expect_refetch:
            refetch.assert_called_once()
        else:
            refetch.assert_not_called()


@pytest.mark.parametrize("initial_val,expected_initial_val", [
    (None, {AbstractLsaSelectorContext.Category.OPERATIONAL}),
    (set(), {AbstractLsaSelectorContext.Category.OPERATIONAL}),
    ({AbstractLsaSelectorContext.Category.OPERATIONAL}, {AbstractLsaSelectorContext.Category.OPERATIONAL}),
    ({AbstractLsaSelectorContext.Category.MD}, {AbstractLsaSelectorContext.Category.MD}),
    ({AbstractLsaSelectorContext.Category.ARCHIVED}, {AbstractLsaSelectorContext.Category.ARCHIVED}),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE}, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE}),
    ({AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE},
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE}),
])
@pytest.mark.parametrize("new_val,expected_new_val", [
    ({AbstractLsaSelectorContext.Category.OPERATIONAL}, {AbstractLsaSelectorContext.Category.OPERATIONAL}),
    (set(), set()),
    ({AbstractLsaSelectorContext.Category.MD}, {AbstractLsaSelectorContext.Category.MD}),
    ({AbstractLsaSelectorContext.Category.ARCHIVED}, {AbstractLsaSelectorContext.Category.ARCHIVED}),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE}, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE}),
    ({AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE},
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE}),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator", return_value=[])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
def test_model_categories_prop(_, __, initial_val, expected_initial_val, new_val, expected_new_val):
    model = LsaSelectorModel(categories=initial_val)
    assert model.categories == expected_initial_val
    model.categories = new_val
    assert model.categories == expected_new_val


@pytest.mark.parametrize("initial_val,new_val,expect_refetch", [
    (None, {AbstractLsaSelectorContext.Category.OPERATIONAL}, False),
    (set(), {AbstractLsaSelectorContext.Category.OPERATIONAL}, False),
    ({AbstractLsaSelectorContext.Category.OPERATIONAL}, {AbstractLsaSelectorContext.Category.OPERATIONAL}, False),
    (None, {AbstractLsaSelectorContext.Category.MD}, True),
    (set(), {AbstractLsaSelectorContext.Category.MD}, True),
    ({AbstractLsaSelectorContext.Category.OPERATIONAL}, {AbstractLsaSelectorContext.Category.MD}, True),
    ({AbstractLsaSelectorContext.Category.MD}, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, True),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, {AbstractLsaSelectorContext.Category.MD}, True),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, False),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OBSOLETE}, True),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator", return_value=[])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
def test_model_set_categories_refetches_data(_, __, initial_val, new_val, expect_refetch):
    model = LsaSelectorModel(categories=initial_val)
    with mock.patch.object(model, "refetch") as refetch:
        model.categories = new_val
        if expect_refetch:
            refetch.assert_called_once()
        else:
            refetch.assert_not_called()


@pytest.mark.parametrize("role,expected_initial_val", [
    (LsaSelectorColorRole.FG_CTX_RESIDENT_NON_PPM, "#ffa500"),
    (LsaSelectorColorRole.FG_CTX_RESIDENT_ACTIVE, "#00ff00"),
    (LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL, "#ffff00"),
    (LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE, "#00ffff"),
    (LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NORMAL, "#000000"),
    (LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM, "#c66600"),
    (LsaSelectorColorRole.BG_CTX_RESIDENT, "#000000"),
    (LsaSelectorColorRole.BG_CTX_NON_RESIDENT, "#ffffff"),
    (LsaSelectorColorRole.BG_CTX_CAN_BE_RESIDENT, "#c8c8c8"),
    (LsaSelectorColorRole.FG_USER, "#ffffff"),
])
@pytest.mark.parametrize("new_val,expected_new_val", [
    (Qt.black, "#000000"),
    (Qt.red, "#ff0000"),
    (Qt.blue, "#0000ff"),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator", return_value=[])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
def test_model_get_set_color(_, __, role, expected_initial_val, new_val, expected_new_val):
    model = LsaSelectorModel()
    assert model.color(role).name() == expected_initial_val
    model.set_color(role, QColor(new_val))
    assert model.color(role).name() == expected_new_val


@pytest.mark.parametrize("role,new_color,expect_signal", [
    (LsaSelectorColorRole.FG_CTX_RESIDENT_NON_PPM, "#ffa500", False),
    (LsaSelectorColorRole.FG_CTX_RESIDENT_ACTIVE, "#00ff00", False),
    (LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL, "#ffff00", False),
    (LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE, "#00ffff", False),
    (LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NORMAL, "#000000", False),
    (LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM, "#c66600", False),
    (LsaSelectorColorRole.BG_CTX_RESIDENT, "#000000", False),
    (LsaSelectorColorRole.BG_CTX_NON_RESIDENT, "#ffffff", False),
    (LsaSelectorColorRole.BG_CTX_CAN_BE_RESIDENT, "#c8c8c8", False),
    (LsaSelectorColorRole.FG_USER, "#ffffff", False),
    (LsaSelectorColorRole.FG_CTX_RESIDENT_NON_PPM, "#f0f0f0", False),
    (LsaSelectorColorRole.FG_CTX_RESIDENT_ACTIVE, "#f0f0f0", False),
    (LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL, "#f0f0f0", False),
    (LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE, "#f0f0f0", False),
    (LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NORMAL, "#f0f0f0", False),
    (LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM, "#f0f0f0", False),
    (LsaSelectorColorRole.BG_CTX_RESIDENT, "#f0f0f0", True),
    (LsaSelectorColorRole.BG_CTX_NON_RESIDENT, "#f0f0f0", False),
    (LsaSelectorColorRole.BG_CTX_CAN_BE_RESIDENT, "#f0f0f0", False),
    (LsaSelectorColorRole.FG_USER, "#f0f0f0", False),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator", return_value=[])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
def test_model_set_color_emits_signal_for_bkg(_, __, qtbot: QtBot, role, new_color, expect_signal):
    model = LsaSelectorModel()
    with qtbot.wait_signal(model.background_color_changed, raising=False, timeout=100) as blocker:
        model.set_color(role, QColor(new_color))
    assert blocker.signal_triggered == expect_signal


@pytest.mark.parametrize("new_val,expected_new_val", [
    (QFont("Arial"), QFont("Arial")),
    (QFont("Arial", 12), QFont("Arial", 12)),
    (QFont("Arial", 12, QFont.Bold), QFont("Arial", 12, QFont.Bold)),
    (QFont("Arial", 12, QFont.Medium), QFont("Arial", 12, QFont.Medium)),
    (QFont("Arial", 12, QFont.Medium, True), QFont("Arial", 12, QFont.Medium, True)),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator", return_value=[])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
def test_model_resident_font_prop(_, __, new_val, expected_new_val):
    model = LsaSelectorModel()
    assert model.resident_font == QFont("Helvetica", 8, QFont.Bold)
    model.resident_font = new_val
    assert model.resident_font == expected_new_val


@pytest.mark.parametrize("new_val,expected_new_val", [
    (QFont("Arial"), QFont("Arial")),
    (QFont("Arial", 12), QFont("Arial", 12)),
    (QFont("Arial", 12, QFont.Bold), QFont("Arial", 12, QFont.Bold)),
    (QFont("Arial", 12, QFont.Medium), QFont("Arial", 12, QFont.Medium)),
    (QFont("Arial", 12, QFont.Medium, True), QFont("Arial", 12, QFont.Medium, True)),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator", return_value=[])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
def test_model_non_resident_font_prop(_, __, new_val, expected_new_val):
    model = LsaSelectorModel()
    assert model.non_resident_font == QFont("Helvetica", 8)
    model.non_resident_font = new_val
    assert model.non_resident_font == expected_new_val


@pytest.mark.parametrize("new_val,expected_new_val", [
    (None, ""),
    ("", ""),
    ("abc", "abc"),
    ("9", "9"),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator", return_value=[])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
def test_model_filter_title_prop(_, __, new_val, expected_new_val):
    model = LsaSelectorModel()
    assert model.filter_title == ""
    model.filter_title = new_val
    assert model.filter_title == expected_new_val


@pytest.mark.parametrize("initial_val,new_val,expect_signal", [
    (None, None, False),
    (None, "", True),
    (None, "abc", True),
    (None, "9", True),
    ("", None, True),
    ("", "", False),
    ("", "abc", True),
    ("", "9", True),
    ("abc", None, True),
    ("abc", "", True),
    ("abc", "abc", False),
    ("abc", "9", True),
    ("9", None, True),
    ("9", "", True),
    ("9", "abc", True),
    ("9", "9", False),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator", return_value=[])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
def test_model_set_filter_title_emits_signal(_, __, qtbot: QtBot, initial_val, new_val, expect_signal):
    model = LsaSelectorModel()
    model.filter_title = initial_val
    with qtbot.wait_signal(model.title_filter_changed, raising=False, timeout=100) as blocker:
        model.filter_title = new_val
    assert blocker.signal_triggered == expect_signal


@pytest.mark.parametrize("new_val,expected_new_val", [
    (None, set()),
    (set(), set()),
    ({AbstractLsaSelectorContext.Category.MD}, {AbstractLsaSelectorContext.Category.MD}),
    ({AbstractLsaSelectorContext.Category.OPERATIONAL}, {AbstractLsaSelectorContext.Category.OPERATIONAL}),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.OPERATIONAL},
     {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.OPERATIONAL}),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator", return_value=[])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
def test_model_filter_categories_prop(_, __, new_val, expected_new_val):
    model = LsaSelectorModel()
    assert model.filter_categories == set()
    model.filter_categories = new_val
    assert model.filter_categories == expected_new_val


@pytest.mark.parametrize("initial_val,new_val,expect_signal", [
    (None, None, False),
    (None, set(), True),
    (None, {AbstractLsaSelectorContext.Category.MD}, True),
    (None, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, True),
    (None, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.OPERATIONAL}, True),
    (set(), None, True),
    (set(), set(), False),
    (set(), {AbstractLsaSelectorContext.Category.MD}, True),
    (set(), {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, True),
    (set(), {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.OPERATIONAL}, True),
    ({AbstractLsaSelectorContext.Category.MD}, None, True),
    ({AbstractLsaSelectorContext.Category.MD}, set(), True),
    ({AbstractLsaSelectorContext.Category.MD}, {AbstractLsaSelectorContext.Category.MD}, False),
    ({AbstractLsaSelectorContext.Category.MD}, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, True),
    ({AbstractLsaSelectorContext.Category.MD}, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.OPERATIONAL}, True),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, None, True),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, set(), True),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, {AbstractLsaSelectorContext.Category.MD}, True),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, False),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.OPERATIONAL}, True),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.OPERATIONAL}, None, True),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.OPERATIONAL}, set(), True),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.OPERATIONAL}, {AbstractLsaSelectorContext.Category.MD}, True),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.OPERATIONAL}, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, True),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.OPERATIONAL},
     {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.OPERATIONAL}, False),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator", return_value=[])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
def test_model_set_filter_categories_emits_signal(_, __, qtbot: QtBot, initial_val, new_val, expect_signal):
    model = LsaSelectorModel()
    model.filter_categories = initial_val
    with qtbot.wait_signal(model.category_filter_changed, raising=False, timeout=100) as blocker:
        model.filter_categories = new_val
    assert blocker.signal_triggered == expect_signal


@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator", return_value=[])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
def test_model_refetch(_, contexts_for_accelerator):
    model = LsaSelectorModel()
    contexts_for_accelerator.assert_called_once()
    contexts_for_accelerator.reset_mock()
    model.refetch()
    contexts_for_accelerator.assert_called_once()


@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator", return_value=[])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
def test_model_connect_table(_, __, qtbot: QtBot):
    table = QTableView()
    qtbot.add_widget(table)
    model = LsaSelectorModel()
    assert table.model() is None
    model.connect_table(table)
    assert table.model() is not None


@pytest.mark.parametrize("ctx_categories,expected_stored_categories", [
    ([], set()),
    (
        [
            AbstractLsaSelectorContext.Category.OPERATIONAL,
        ],
        {
            AbstractLsaSelectorContext.Category.OPERATIONAL,
        },
    ),
    (
        [
            AbstractLsaSelectorContext.Category.OPERATIONAL,
            AbstractLsaSelectorContext.Category.OPERATIONAL,
        ],
        {
            AbstractLsaSelectorContext.Category.OPERATIONAL,
        },
    ),
    (
        [
            AbstractLsaSelectorContext.Category.OPERATIONAL,
            AbstractLsaSelectorContext.Category.MD,
        ],
        {
            AbstractLsaSelectorContext.Category.OPERATIONAL,
            AbstractLsaSelectorContext.Category.MD,
        },
    ),
    (
        [
            AbstractLsaSelectorContext.Category.ARCHIVED,
            AbstractLsaSelectorContext.Category.OPERATIONAL,
            AbstractLsaSelectorContext.Category.MD,
            AbstractLsaSelectorContext.Category.ARCHIVED,
        ],
        {
            AbstractLsaSelectorContext.Category.OPERATIONAL,
            AbstractLsaSelectorContext.Category.MD,
            AbstractLsaSelectorContext.Category.ARCHIVED,
        },
    ),
    (
        [
            AbstractLsaSelectorContext.Category.ARCHIVED,
            AbstractLsaSelectorContext.Category.OPERATIONAL,
            AbstractLsaSelectorContext.Category.ARCHIVED,
            AbstractLsaSelectorContext.Category.ARCHIVED,
        ],
        {
            AbstractLsaSelectorContext.Category.OPERATIONAL,
            AbstractLsaSelectorContext.Category.ARCHIVED,
        },
    ),
])
@pytest.mark.parametrize("ctx_types,extra_ctx_args", [
    ([LsaSelectorNonMultiplexedResidentContext], [{}]),
    ([LsaSelectorNonResidentContext], [{"multiplexed": True}]),
    ([LsaSelectorMultiplexedResidentContext], [{"user": "TEST.USER.ALL", "user_type": LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL}]),
    (
        [
            LsaSelectorNonMultiplexedResidentContext,
            LsaSelectorNonResidentContext,
            LsaSelectorMultiplexedResidentContext,
        ],
        [
            {},
            {"multiplexed": True},
            {"user": "TEST.USER.ALL", "user_type": LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL},
        ],
    ),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator")
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
def test_model_find_stored_categories(_, contexts_for_accelerator, ctx_categories, expected_stored_categories,
                                      ctx_types, extra_ctx_args):
    def make_row(category: AbstractLsaSelectorContext.Category, idx: int):
        i = idx % min(len(ctx_types), len(extra_ctx_args))
        ctx_type = ctx_types[i]
        extra_args = extra_ctx_args[i]
        ctx = ctx_type(name="test_ctx", category=category, **extra_args)
        return LsaSelectorRowViewModel(ctx=ctx)

    rows = [make_row(category, idx) for idx, category in enumerate(ctx_categories)]
    contexts_for_accelerator.return_value = rows
    model = LsaSelectorModel()
    assert model.find_stored_categories() == expected_stored_categories


@pytest.mark.parametrize("real_contexts,expected_rows", [
    ([], []),
    (
        [
            LsaSelectorMultiplexedResidentContext(
                name="_ZERO_",
                user="LEI.USER.ZERO",
                category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
            ),
            LsaSelectorMultiplexedResidentContext(
                name="LIN3MEASv1",
                user="LEI.USER.LIN3MEAS",
                category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
            ),
            LsaSelectorNonMultiplexedResidentContext(
                name="_NON_MULTIPLEXED_LHC",
                category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
            ),
            LsaSelectorMultiplexedResidentContext(
                name="LIN3MEASv1_spare",
                user="LEI.USER.LIN3MEAS",
                category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
            ),
        ],
        [
            LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
                name="LIN3MEASv1",
                user="LEI.USER.LIN3MEAS",
                category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
            )),
            LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
                name="LIN3MEASv1_spare",
                user="LEI.USER.LIN3MEAS",
                category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
            )),
            LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
                name="_ZERO_",
                user="LEI.USER.ZERO",
                category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
            )),
            LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(
                name="_NON_MULTIPLEXED_LHC",
                category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
            )),
        ],
    ),
    (
        [
            LsaSelectorMultiplexedResidentContext(
                name="LIN3MEASv1_spare",
                user="LEI.USER.LIN3MEAS",
                category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
            ),
            LsaSelectorMultiplexedResidentContext(
                name="LIN3MEASv1",
                user="LEI.USER.LIN3MEAS",
                category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
            ),
            LsaSelectorNonMultiplexedResidentContext(
                name="_NON_MULTIPLEXED_LHC",
                category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
            ),
            LsaSelectorMultiplexedResidentContext(
                name="_ZERO_",
                user="LEI.USER.ZERO",
                category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
            ),
            LsaSelectorNonResidentContext(
                name="BP_CAN_BE_RESIDENT_OP",
                multiplexed=True,
                can_become_resident=True,
                category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
            ),
            LsaSelectorNonResidentContext(
                name="STANDALONE_NON_RESIDENT_OP",
                multiplexed=True,
                category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
            ),
            LsaSelectorNonResidentContext(
                name="_NON_PPM_NON_RESIDENT_OP",
                multiplexed=False,
                category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
            ),
            LsaSelectorNonResidentContext(
                name="_NON_PPM_CAN_BE_RESIDENT_OP",
                multiplexed=False,
                can_become_resident=True,
                category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
            ),
        ],
        [
            LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
                name="LIN3MEASv1",
                user="LEI.USER.LIN3MEAS",
                category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
            )),
            LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
                name="LIN3MEASv1_spare",
                user="LEI.USER.LIN3MEAS",
                category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
            )),
            LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
                name="_ZERO_",
                user="LEI.USER.ZERO",
                category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
            )),
            LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(
                name="_NON_MULTIPLEXED_LHC",
                category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
            )),
            LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
                name="BP_CAN_BE_RESIDENT_OP",
                multiplexed=True,
                can_become_resident=True,
                category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
            )),
            LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
                name="_NON_PPM_CAN_BE_RESIDENT_OP",
                multiplexed=False,
                can_become_resident=True,
                category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
            )),
            LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
                name="STANDALONE_NON_RESIDENT_OP",
                multiplexed=True,
                category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
            )),
            LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
                name="_NON_PPM_NON_RESIDENT_OP",
                multiplexed=False,
                category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
            )),
        ],
    ),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator")
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
@mock.patch("accwidgets.lsa_selector._model.is_designer", return_value=False)
def test_model_rows_on_success_real(_, __, contexts_for_accelerator, real_contexts, expected_rows):
    contexts_for_accelerator.return_value = [LsaSelectorRowViewModel(ctx) for ctx in real_contexts]
    model = LsaSelectorModel()
    assert model._row_models == expected_rows


@pytest.mark.parametrize("accelerator,resident_only,categories,expected_rows", [
    (LsaSelectorAccelerator.LHC, True, {}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1_spare",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="_ZERO_",
            user="LEI.USER.ZERO",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(
            name="_NON_MULTIPLEXED_LHC",
            category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
        )),
    ]),
    (LsaSelectorAccelerator.SPS, True, {}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1_spare",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="_ZERO_",
            user="LEI.USER.ZERO",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(
            name="_NON_MULTIPLEXED_SPS",
            category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
        )),
    ]),
    (LsaSelectorAccelerator.LHC, True, {AbstractLsaSelectorContext.Category.OPERATIONAL}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1_spare",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="_ZERO_",
            user="LEI.USER.ZERO",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(
            name="_NON_MULTIPLEXED_LHC",
            category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
        )),
    ]),
    (LsaSelectorAccelerator.SPS, True, {AbstractLsaSelectorContext.Category.OPERATIONAL}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1_spare",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="_ZERO_",
            user="LEI.USER.ZERO",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(
            name="_NON_MULTIPLEXED_SPS",
            category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
        )),
    ]),
    (LsaSelectorAccelerator.LHC, True, {AbstractLsaSelectorContext.Category.MD}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="MD4003_Pb54_3BP_B_Train",
            user="LEI.USER.AMD",
            category=LsaSelectorMultiplexedResidentContext.Category.MD,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
    ]),
    (LsaSelectorAccelerator.SPS, True, {AbstractLsaSelectorContext.Category.MD}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="MD4003_Pb54_3BP_B_Train",
            user="LEI.USER.AMD",
            category=LsaSelectorMultiplexedResidentContext.Category.MD,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
    ]),
    (LsaSelectorAccelerator.LHC, True, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OPERATIONAL}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1_spare",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="MD4003_Pb54_3BP_B_Train",
            user="LEI.USER.AMD",
            category=LsaSelectorMultiplexedResidentContext.Category.MD,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="_ZERO_",
            user="LEI.USER.ZERO",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(
            name="_NON_MULTIPLEXED_LHC",
            category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
        )),
    ]),
    (LsaSelectorAccelerator.SPS, True, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OPERATIONAL}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1_spare",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="MD4003_Pb54_3BP_B_Train",
            user="LEI.USER.AMD",
            category=LsaSelectorMultiplexedResidentContext.Category.MD,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="_ZERO_",
            user="LEI.USER.ZERO",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(
            name="_NON_MULTIPLEXED_SPS",
            category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
        )),
    ]),
    (LsaSelectorAccelerator.LHC, True, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="MD4003_Pb54_3BP_B_Train",
            user="LEI.USER.AMD",
            category=LsaSelectorMultiplexedResidentContext.Category.MD,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
    ]),
    (LsaSelectorAccelerator.SPS, True, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="MD4003_Pb54_3BP_B_Train",
            user="LEI.USER.AMD",
            category=LsaSelectorMultiplexedResidentContext.Category.MD,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
    ]),
    (LsaSelectorAccelerator.LHC, True, {AbstractLsaSelectorContext.Category.OBSOLETE}, []),
    (LsaSelectorAccelerator.SPS, True, {AbstractLsaSelectorContext.Category.OBSOLETE}, []),
    (LsaSelectorAccelerator.LHC, False, {}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1_spare",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="_ZERO_",
            user="LEI.USER.ZERO",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(
            name="_NON_MULTIPLEXED_LHC",
            category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="BP_CAN_BE_RESIDENT_OP",
            multiplexed=True,
            can_become_resident=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="_NON_PPM_CAN_BE_RESIDENT_OP",
            multiplexed=False,
            can_become_resident=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="STANDALONE_NON_RESIDENT_OP",
            multiplexed=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="_NON_PPM_NON_RESIDENT_OP",
            multiplexed=False,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        )),
    ]),
    (LsaSelectorAccelerator.SPS, False, {}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1_spare",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="_ZERO_",
            user="LEI.USER.ZERO",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(
            name="_NON_MULTIPLEXED_SPS",
            category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
        )),

        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="BP_CAN_BE_RESIDENT_OP",
            multiplexed=True,
            can_become_resident=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="_NON_PPM_CAN_BE_RESIDENT_OP",
            multiplexed=False,
            can_become_resident=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="STANDALONE_NON_RESIDENT_OP",
            multiplexed=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="_NON_PPM_NON_RESIDENT_OP",
            multiplexed=False,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        )),
    ]),
    (LsaSelectorAccelerator.LHC, False, {AbstractLsaSelectorContext.Category.OPERATIONAL}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1_spare",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="_ZERO_",
            user="LEI.USER.ZERO",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(
            name="_NON_MULTIPLEXED_LHC",
            category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="BP_CAN_BE_RESIDENT_OP",
            multiplexed=True,
            can_become_resident=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="_NON_PPM_CAN_BE_RESIDENT_OP",
            multiplexed=False,
            can_become_resident=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="STANDALONE_NON_RESIDENT_OP",
            multiplexed=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="_NON_PPM_NON_RESIDENT_OP",
            multiplexed=False,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        )),
    ]),
    (LsaSelectorAccelerator.SPS, False, {AbstractLsaSelectorContext.Category.OPERATIONAL}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1_spare",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="_ZERO_",
            user="LEI.USER.ZERO",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(
            name="_NON_MULTIPLEXED_SPS",
            category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="BP_CAN_BE_RESIDENT_OP",
            multiplexed=True,
            can_become_resident=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="_NON_PPM_CAN_BE_RESIDENT_OP",
            multiplexed=False,
            can_become_resident=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="STANDALONE_NON_RESIDENT_OP",
            multiplexed=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="_NON_PPM_NON_RESIDENT_OP",
            multiplexed=False,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        )),
    ]),
    (LsaSelectorAccelerator.LHC, False, {AbstractLsaSelectorContext.Category.MD}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="MD4003_Pb54_3BP_B_Train",
            user="LEI.USER.AMD",
            category=LsaSelectorMultiplexedResidentContext.Category.MD,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="STANDALONE_NON_RESIDENT_MD",
            multiplexed=True,
            category=LsaSelectorNonResidentContext.Category.MD,
        )),
    ]),
    (LsaSelectorAccelerator.SPS, False, {AbstractLsaSelectorContext.Category.MD}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
            name="MD4003_Pb54_3BP_B_Train",
            user="LEI.USER.AMD",
            category=LsaSelectorMultiplexedResidentContext.Category.MD,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        )),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="STANDALONE_NON_RESIDENT_MD",
            multiplexed=True,
            category=LsaSelectorNonResidentContext.Category.MD,
        )),
    ]),
    (LsaSelectorAccelerator.LHC, False,
     {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OPERATIONAL}, [
         LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
             name="LIN3MEASv1",
             user="LEI.USER.LIN3MEAS",
             category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
             user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
             name="LIN3MEASv1_spare",
             user="LEI.USER.LIN3MEAS",
             category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
             user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
             name="MD4003_Pb54_3BP_B_Train",
             user="LEI.USER.AMD",
             category=LsaSelectorMultiplexedResidentContext.Category.MD,
             user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
             name="_ZERO_",
             user="LEI.USER.ZERO",
             category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
             user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(
             name="_NON_MULTIPLEXED_LHC",
             category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
             name="BP_CAN_BE_RESIDENT_OP",
             multiplexed=True,
             can_become_resident=True,
             category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
             name="_NON_PPM_CAN_BE_RESIDENT_OP",
             multiplexed=False,
             can_become_resident=True,
             category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
             name="STANDALONE_NON_RESIDENT_MD",
             multiplexed=True,
             category=LsaSelectorNonResidentContext.Category.MD,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
             name="STANDALONE_NON_RESIDENT_OP",
             multiplexed=True,
             category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
             name="_NON_PPM_NON_RESIDENT_OP",
             multiplexed=False,
             category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
         )),
     ]),
    (LsaSelectorAccelerator.SPS, False,
     {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OPERATIONAL}, [
         LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
             name="LIN3MEASv1",
             user="LEI.USER.LIN3MEAS",
             category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
             user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
             name="LIN3MEASv1_spare",
             user="LEI.USER.LIN3MEAS",
             category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
             user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
             name="MD4003_Pb54_3BP_B_Train",
             user="LEI.USER.AMD",
             category=LsaSelectorMultiplexedResidentContext.Category.MD,
             user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
             name="_ZERO_",
             user="LEI.USER.ZERO",
             category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
             user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(
             name="_NON_MULTIPLEXED_SPS",
             category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
             name="BP_CAN_BE_RESIDENT_OP",
             multiplexed=True,
             can_become_resident=True,
             category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
             name="_NON_PPM_CAN_BE_RESIDENT_OP",
             multiplexed=False,
             can_become_resident=True,
             category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
             name="STANDALONE_NON_RESIDENT_MD",
             multiplexed=True,
             category=LsaSelectorNonResidentContext.Category.MD,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
             name="STANDALONE_NON_RESIDENT_OP",
             multiplexed=True,
             category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
             name="_NON_PPM_NON_RESIDENT_OP",
             multiplexed=False,
             category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
         )),
     ]),
    (LsaSelectorAccelerator.LHC, False,
     {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE}, [
         LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
             name="MD4003_Pb54_3BP_B_Train",
             user="LEI.USER.AMD",
             category=LsaSelectorMultiplexedResidentContext.Category.MD,
             user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
             name="STANDALONE_NON_RESIDENT_MD",
             multiplexed=True,
             category=LsaSelectorNonResidentContext.Category.MD,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
             name="STANDALONE_NON_RESIDENT_OBS",
             multiplexed=True,
             category=LsaSelectorNonResidentContext.Category.OBSOLETE,
         )),
     ]),
    (LsaSelectorAccelerator.SPS, False,
     {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE}, [
         LsaSelectorRowViewModel(ctx=LsaSelectorMultiplexedResidentContext(
             name="MD4003_Pb54_3BP_B_Train",
             user="LEI.USER.AMD",
             category=LsaSelectorMultiplexedResidentContext.Category.MD,
             user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
             name="STANDALONE_NON_RESIDENT_MD",
             multiplexed=True,
             category=LsaSelectorNonResidentContext.Category.MD,
         )),
         LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
             name="STANDALONE_NON_RESIDENT_OBS",
             multiplexed=True,
             category=LsaSelectorNonResidentContext.Category.OBSOLETE,
         )),
     ]),
    (LsaSelectorAccelerator.LHC, False, {AbstractLsaSelectorContext.Category.OBSOLETE}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="STANDALONE_NON_RESIDENT_OBS",
            multiplexed=True,
            category=LsaSelectorNonResidentContext.Category.OBSOLETE,
        )),
    ]),
    (LsaSelectorAccelerator.SPS, False, {AbstractLsaSelectorContext.Category.OBSOLETE}, [
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(
            name="STANDALONE_NON_RESIDENT_OBS",
            multiplexed=True,
            category=LsaSelectorNonResidentContext.Category.OBSOLETE,
        )),
    ]),
])
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
@mock.patch("accwidgets.lsa_selector._model.is_designer", return_value=True)
def test_model_rows_on_success_designer(_, __, accelerator, resident_only, categories, expected_rows):
    model = LsaSelectorModel(accelerator=accelerator, resident_only=resident_only, categories=categories)
    assert model._row_models == expected_rows


@pytest.mark.parametrize("java_error,should_emit_signal", [
    (True, True),
    (False, False),
])
@mock.patch("accwidgets.lsa_selector._model.contexts_for_accelerator")
@mock.patch("accwidgets.lsa_selector._model.LSAClient")
@mock.patch("accwidgets.lsa_selector._model.is_designer", return_value=False)
def test_model_lsa_error_emits_signal(_, __, contexts_for_accelerator, qtbot: QtBot, java_error, should_emit_signal):
    model = LsaSelectorModel()
    contexts_for_accelerator.reset_mock()
    if java_error:
        from jpype import JClass, getDefaultJVMPath, startJVM, isJVMStarted
        if not isJVMStarted():
            startJVM(getDefaultJVMPath())
        contexts_for_accelerator.side_effect = JClass("java.lang.IllegalArgumentException")
    else:
        contexts_for_accelerator.return_value = []
    with qtbot.wait_signal(model.lsa_error_received, raising=False, timeout=100) as blocker:
        model.refetch()
    assert blocker.signal_triggered == should_emit_signal


@pytest.mark.parametrize("new_val,expected_new_val,expect_invalidate", [
    (None, None, False),
    ("", "", True),
    ("abc", "abc", True),
    ("9", "9", True),
])
def test_filter_model_name_setter(new_val, expected_new_val, expect_invalidate):
    model = LsaSelectorFilterModel()
    assert model.name_filter is None
    with mock.patch.object(model, "invalidateFilter") as invalidateFilter:
        model.name_filter = new_val
        assert model.name_filter == expected_new_val
        if expect_invalidate:
            invalidateFilter.assert_called_once()
        else:
            invalidateFilter.assert_not_called()


@pytest.mark.parametrize("new_val,expected_new_val,expect_invalidate", [
    (None, None, False),
    ({}, {}, True),
    ({AbstractLsaSelectorContext.Category.OPERATIONAL}, {AbstractLsaSelectorContext.Category.OPERATIONAL}, True),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OPERATIONAL}, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OPERATIONAL}, True),
    ({AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.ARCHIVED}, True),
])
def test_filter_model_categories_setter(new_val, expected_new_val, expect_invalidate):
    model = LsaSelectorFilterModel()
    assert model.category_filter is None
    with mock.patch.object(model, "invalidateFilter") as invalidateFilter:
        model.category_filter = new_val
        assert model.category_filter == expected_new_val
        if expect_invalidate:
            invalidateFilter.assert_called_once()
        else:
            invalidateFilter.assert_not_called()


@pytest.mark.parametrize("context_names,context_categories,name_filter,category_filter,expected_filered_names", [
    ([], [], None, None, []),
    ([], [], "", None, []),
    ([], [], None, set(), []),
    ([], [], "", set(), []),
    ([], [], "al", None, []),
    ([], [], "brav", None, []),
    ([], [], "al", set(), []),
    ([], [], "brav", set(), []),
    ([], [], "al", {AbstractLsaSelectorContext.Category.MD}, []),
    ([], [], "brav", {AbstractLsaSelectorContext.Category.MD}, []),
    ([], [], "al", {AbstractLsaSelectorContext.Category.OBSOLETE}, []),
    ([], [], "brav", {AbstractLsaSelectorContext.Category.OBSOLETE}, []),
    ([], [], "al", {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE}, []),
    ([], [], "brav", {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE}, []),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     None, None, ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"]),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     "", None, ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"]),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     None, set(), ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"]),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     "", set(), ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"]),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     "al", None, ["alpha", "alpha1"]),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     "brav", None, ["bravo", "bravo1"]),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     "al", set(), ["alpha", "alpha1"]),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     "brav", set(), ["bravo", "bravo1"]),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     "al", {AbstractLsaSelectorContext.Category.MD}, ["alpha"]),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     "brav", {AbstractLsaSelectorContext.Category.MD}, []),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     "al", {AbstractLsaSelectorContext.Category.OBSOLETE}, []),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     "brav", {AbstractLsaSelectorContext.Category.OBSOLETE}, ["bravo"]),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     "al", {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE}, ["alpha"]),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     "brav", {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE}, ["bravo"]),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD,
      AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     None, {AbstractLsaSelectorContext.Category.MD}, ["alpha", "delta", "echo"]),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD,
      AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     "", {AbstractLsaSelectorContext.Category.MD}, ["alpha", "delta", "echo"]),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD,
      AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     None, {AbstractLsaSelectorContext.Category.OBSOLETE}, ["bravo", "charlie", "foxtrot"]),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD,
      AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     "", {AbstractLsaSelectorContext.Category.OBSOLETE}, ["bravo", "charlie", "foxtrot"]),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD,
      AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     None, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE}, ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot"]),
    (["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "alpha1", "bravo1", "charlie1", "delta1", "echo1", "foxtrot1"],
     [AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.MD,
      AbstractLsaSelectorContext.Category.OBSOLETE,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.OPERATIONAL],
     "", {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OBSOLETE}, ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot"]),
])
def test_filter_model_name_filters(context_names, context_categories, name_filter, category_filter, expected_filered_names):
    model = LsaSelectorFilterModel()
    model.name_filter = name_filter
    model.category_filter = category_filter
    rows = [LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(name=name, category=cat))
            for name, cat in zip(context_names, context_categories)]
    source_model = LsaSelectorTableModel(row_models=rows,
                                         color_map={},
                                         resident_font=QFont(),
                                         non_resident_font=QFont())
    model.setSourceModel(source_model)
    assert model.rowCount() == len(expected_filered_names)
    for idx, expected_name in enumerate(expected_filered_names):
        assert model.index(idx, 1).data() == expected_name


@pytest.mark.parametrize("filter", [
    "abc",
    "ABC",
])
def test_filter_model_name_filters_case_insensitive(filter):
    model = LsaSelectorFilterModel()
    model.name_filter = filter
    rows = [LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(name=name, category=AbstractLsaSelectorContext.Category.MD))
            for name in ["abc1", "abc2", "def"]]
    source_model = LsaSelectorTableModel(row_models=rows,
                                         color_map={},
                                         resident_font=QFont(),
                                         non_resident_font=QFont())
    model.setSourceModel(source_model)
    assert model.rowCount() == 2
    for idx, expected_name in enumerate(["abc1", "abc2"]):
        assert model.index(idx, 1).data() == expected_name


@pytest.mark.parametrize("initial_data,new_data,should_reset", [
    ([], [], False),
    ([], ["test"], True),
    (["test"], [], True),
    (["test"], ["test"], False),
    (["test"], ["test2"], True),
    (["test"], ["test", "test2"], True),
    (["test", "test2"], ["test"], True),
    (["test", "test2"], ["test", "test2"], False),
])
def test_table_model_rows_setter_resets(initial_data, new_data, should_reset, qtbot: QtBot):
    def make_row(name: str):
        return LsaSelectorRowViewModel(ctx=LsaSelectorNonMultiplexedResidentContext(name=name, category=AbstractLsaSelectorContext.Category.MD))
    rows = [make_row(name) for name in initial_data]
    model = LsaSelectorTableModel(row_models=rows,
                                  color_map={},
                                  resident_font=QFont(),
                                  non_resident_font=QFont())
    with qtbot.wait_signal(model.modelReset, raising=False, timeout=100) as blocker:
        model.set_row_models([make_row(name) for name in new_data])
    assert blocker.signal_triggered == should_reset


@pytest.mark.parametrize("initial_val,expected_initial_val,new_val,expected_new_val", [
    ({}, {}, {}, {}),
    ({}, {}, {LsaSelectorColorRole.FG_USER: QColor(Qt.black)}, {LsaSelectorColorRole.FG_USER: QColor(Qt.black)}),
    ({LsaSelectorColorRole.FG_USER: QColor(Qt.black)}, {LsaSelectorColorRole.FG_USER: QColor(Qt.black)}, {LsaSelectorColorRole.FG_USER: QColor(Qt.black)}, {LsaSelectorColorRole.FG_USER: QColor(Qt.black)}),
    ({LsaSelectorColorRole.FG_USER: QColor(Qt.red)}, {LsaSelectorColorRole.FG_USER: QColor(Qt.red)}, {LsaSelectorColorRole.FG_USER: QColor(Qt.black)}, {LsaSelectorColorRole.FG_USER: QColor(Qt.black)}),
])
def test_table_model_color_map_prop(initial_val, expected_initial_val, new_val, expected_new_val):
    model = LsaSelectorTableModel(row_models=[],
                                  color_map=initial_val,
                                  resident_font=QFont(),
                                  non_resident_font=QFont())
    assert model.color_map == expected_initial_val
    model.color_map = new_val
    assert model.color_map == expected_new_val


@pytest.mark.parametrize("initial_val,new_val,expect_reset", [
    ({}, {}, False),
    ({}, {LsaSelectorColorRole.FG_USER: QColor(Qt.black)}, True),
    ({LsaSelectorColorRole.FG_USER: QColor(Qt.black)}, {LsaSelectorColorRole.FG_USER: QColor(Qt.black)}, False),
    ({LsaSelectorColorRole.FG_USER: QColor(Qt.red)}, {LsaSelectorColorRole.FG_USER: QColor(Qt.black)}, True),
])
def test_table_model_color_map_setter_resets(qtbot: QtBot, initial_val, new_val, expect_reset):
    model = LsaSelectorTableModel(row_models=[],
                                  color_map=initial_val,
                                  resident_font=QFont(),
                                  non_resident_font=QFont())
    with qtbot.wait_signal(model.modelReset, raising=False, timeout=100) as blocker:
        model.color_map = new_val
    assert blocker.signal_triggered == expect_reset


@pytest.mark.parametrize("initial_val,expected_initial_val,new_val,expected_new_val", [
    (QFont("Arial"), QFont("Arial"), QFont("Arial"), QFont("Arial")),
    (QFont("Arial", 12), QFont("Arial", 12), QFont("Arial", 12), QFont("Arial", 12)),
    (QFont("Arial", 12, QFont.Bold), QFont("Arial", 12, QFont.Bold), QFont("Arial", 12), QFont("Arial", 12)),
    (QFont("Arial", 12, QFont.Medium), QFont("Arial", 12, QFont.Medium), QFont("Arial"), QFont("Arial")),
])
def test_table_model_resident_font_prop(initial_val, expected_initial_val, new_val, expected_new_val):
    model = LsaSelectorTableModel(row_models=[],
                                  color_map={},
                                  resident_font=initial_val,
                                  non_resident_font=QFont())
    assert model.resident_font == expected_initial_val
    model.resident_font = new_val
    assert model.resident_font == expected_new_val


@pytest.mark.parametrize("initial_val,new_val,expect_reset", [
    (QFont("Arial"), QFont("Arial"), False),
    (QFont("Arial", 12), QFont("Arial", 12), False),
    (QFont("Arial", 12, QFont.Bold), QFont("Arial", 12), True),
    (QFont("Arial", 12, QFont.Medium), QFont("Arial"), True),
])
def test_table_model_resident_font_setter_resets(qtbot: QtBot, initial_val, new_val, expect_reset):
    model = LsaSelectorTableModel(row_models=[],
                                  color_map={},
                                  resident_font=initial_val,
                                  non_resident_font=QFont())
    with qtbot.wait_signal(model.modelReset, raising=False, timeout=100) as blocker:
        model.resident_font = new_val
    assert blocker.signal_triggered == expect_reset


@pytest.mark.parametrize("initial_val,expected_initial_val,new_val,expected_new_val", [
    (QFont("Arial"), QFont("Arial"), QFont("Arial"), QFont("Arial")),
    (QFont("Arial", 12), QFont("Arial", 12), QFont("Arial", 12), QFont("Arial", 12)),
    (QFont("Arial", 12, QFont.Bold), QFont("Arial", 12, QFont.Bold), QFont("Arial", 12), QFont("Arial", 12)),
    (QFont("Arial", 12, QFont.Medium), QFont("Arial", 12, QFont.Medium), QFont("Arial"), QFont("Arial")),
])
def test_table_model_non_resident_font_prop(initial_val, expected_initial_val, new_val, expected_new_val):
    model = LsaSelectorTableModel(row_models=[],
                                  color_map={},
                                  resident_font=QFont(),
                                  non_resident_font=initial_val)
    assert model.non_resident_font == expected_initial_val
    model.non_resident_font = new_val
    assert model.non_resident_font == expected_new_val


@pytest.mark.parametrize("initial_val,new_val,expect_reset", [
    (QFont("Arial"), QFont("Arial"), False),
    (QFont("Arial", 12), QFont("Arial", 12), False),
    (QFont("Arial", 12, QFont.Bold), QFont("Arial", 12), True),
    (QFont("Arial", 12, QFont.Medium), QFont("Arial"), True),
])
def test_table_model_non_resident_font_setter_resets(qtbot: QtBot, initial_val, new_val, expect_reset):
    model = LsaSelectorTableModel(row_models=[],
                                  color_map={},
                                  resident_font=QFont(),
                                  non_resident_font=initial_val)
    with qtbot.wait_signal(model.modelReset, raising=False, timeout=100) as blocker:
        model.non_resident_font = new_val
    assert blocker.signal_triggered == expect_reset


@pytest.mark.parametrize("role,orientation,section,expected_label", [
    (Qt.DisplayRole, Qt.Horizontal, 0, " TGM User "),
    (Qt.DisplayRole, Qt.Horizontal, 1, " LSA Context "),
    (Qt.DisplayRole, Qt.Vertical, 0, 1),
    (Qt.DisplayRole, Qt.Vertical, 1, 2),
    (Qt.EditRole, Qt.Horizontal, 0, None),
    (Qt.EditRole, Qt.Horizontal, 1, None),
    (Qt.EditRole, Qt.Vertical, 0, None),
    (Qt.EditRole, Qt.Vertical, 1, None),
    (Qt.ToolTipRole, Qt.Horizontal, 0, None),
    (Qt.ToolTipRole, Qt.Horizontal, 1, None),
    (Qt.ToolTipRole, Qt.Vertical, 0, None),
    (Qt.ToolTipRole, Qt.Vertical, 1, None),
])
def test_table_model_headers(role, orientation, section, expected_label):
    model = LsaSelectorTableModel(row_models=[],
                                  color_map={},
                                  resident_font=QFont(),
                                  non_resident_font=QFont())
    assert model.headerData(section, orientation, role) == expected_label


@pytest.mark.parametrize("ctxs", [
    ([
        LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1_spare",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
        ),
        LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
        ),
        LsaSelectorNonMultiplexedResidentContext(
            name="_NON_MULTIPLEXED_LHC",
            category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
        ),
        LsaSelectorMultiplexedResidentContext(
            name="_ZERO_",
            user="LEI.USER.ZERO",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        ),
        LsaSelectorNonResidentContext(
            name="BP_CAN_BE_RESIDENT_OP",
            multiplexed=True,
            can_become_resident=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        ),
        LsaSelectorNonResidentContext(
            name="STANDALONE_NON_RESIDENT_OP",
            multiplexed=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        ),
        LsaSelectorNonResidentContext(
            name="_NON_PPM_NON_RESIDENT_OP",
            multiplexed=False,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        ),
        LsaSelectorNonResidentContext(
            name="_NON_PPM_CAN_BE_RESIDENT_OP",
            multiplexed=False,
            can_become_resident=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        ),
    ]),
])
@pytest.mark.parametrize("color_map_mod,row,column,role,expected_color_name", [
    ({}, 0, 0, Qt.ForegroundRole, "#ffffff"),
    ({}, 0, 0, Qt.BackgroundRole, "#000000"),
    ({}, 0, 1, Qt.ForegroundRole, "#00ffff"),
    ({}, 0, 1, Qt.BackgroundRole, "#000000"),
    ({}, 1, 0, Qt.ForegroundRole, "#ffffff"),
    ({}, 1, 0, Qt.BackgroundRole, "#000000"),
    ({}, 1, 1, Qt.ForegroundRole, "#00ff00"),
    ({}, 1, 1, Qt.BackgroundRole, "#000000"),
    ({}, 2, 0, Qt.ForegroundRole, "#ffffff"),
    ({}, 2, 0, Qt.BackgroundRole, "#000000"),
    ({}, 2, 1, Qt.ForegroundRole, "#ffa500"),
    ({}, 2, 1, Qt.BackgroundRole, "#000000"),
    ({}, 3, 0, Qt.ForegroundRole, "#ffffff"),
    ({}, 3, 0, Qt.BackgroundRole, "#000000"),
    ({}, 3, 1, Qt.ForegroundRole, "#ffff00"),
    ({}, 3, 1, Qt.BackgroundRole, "#000000"),
    ({}, 4, 0, Qt.ForegroundRole, "#ffffff"),
    ({}, 4, 0, Qt.BackgroundRole, "#c8c8c8"),
    ({}, 4, 1, Qt.ForegroundRole, "#000000"),
    ({}, 4, 1, Qt.BackgroundRole, "#c8c8c8"),
    ({}, 5, 0, Qt.ForegroundRole, "#ffffff"),
    ({}, 5, 0, Qt.BackgroundRole, "#ffffff"),
    ({}, 5, 1, Qt.ForegroundRole, "#000000"),
    ({}, 5, 1, Qt.BackgroundRole, "#ffffff"),
    ({}, 6, 0, Qt.ForegroundRole, "#ffffff"),
    ({}, 6, 0, Qt.BackgroundRole, "#ffffff"),
    ({}, 6, 1, Qt.ForegroundRole, "#c66600"),
    ({}, 6, 1, Qt.BackgroundRole, "#ffffff"),
    ({}, 7, 0, Qt.ForegroundRole, "#ffffff"),
    ({}, 7, 0, Qt.BackgroundRole, "#c8c8c8"),
    ({}, 7, 1, Qt.ForegroundRole, "#c66600"),
    ({}, 7, 1, Qt.BackgroundRole, "#c8c8c8"),
    (
        {
            LsaSelectorColorRole.BG_CTX_NON_RESIDENT: QColor(Qt.green),
            LsaSelectorColorRole.BG_CTX_RESIDENT: QColor(Qt.blue),
            LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE: QColor(Qt.yellow),
            LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM: QColor(Qt.black),
            LsaSelectorColorRole.FG_USER: QColor(Qt.red),
            LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL: QColor(Qt.cyan),
        },
        0, 0, Qt.ForegroundRole, "#ff0000",
    ),
    (
        {
            LsaSelectorColorRole.BG_CTX_NON_RESIDENT: QColor(Qt.green),
            LsaSelectorColorRole.BG_CTX_RESIDENT: QColor(Qt.blue),
            LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE: QColor(Qt.yellow),
            LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM: QColor(Qt.black),
            LsaSelectorColorRole.FG_USER: QColor(Qt.red),
            LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL: QColor(Qt.cyan),
        },
        0, 1, Qt.ForegroundRole, "#ffff00",
    ),
    (
        {
            LsaSelectorColorRole.BG_CTX_NON_RESIDENT: QColor(Qt.green),
            LsaSelectorColorRole.BG_CTX_RESIDENT: QColor(Qt.blue),
            LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE: QColor(Qt.yellow),
            LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM: QColor(Qt.black),
            LsaSelectorColorRole.FG_USER: QColor(Qt.red),
            LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL: QColor(Qt.cyan),
        },
        1, 0, Qt.ForegroundRole, "#ff0000",
    ),
    (
        {
            LsaSelectorColorRole.BG_CTX_NON_RESIDENT: QColor(Qt.green),
            LsaSelectorColorRole.BG_CTX_RESIDENT: QColor(Qt.blue),
            LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE: QColor(Qt.yellow),
            LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM: QColor(Qt.black),
            LsaSelectorColorRole.FG_USER: QColor(Qt.red),
            LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL: QColor(Qt.cyan),
        },
        1, 1, Qt.ForegroundRole, "#00ff00",
    ),
    (
        {
            LsaSelectorColorRole.BG_CTX_NON_RESIDENT: QColor(Qt.green),
            LsaSelectorColorRole.BG_CTX_RESIDENT: QColor(Qt.blue),
            LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE: QColor(Qt.yellow),
            LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM: QColor(Qt.black),
            LsaSelectorColorRole.FG_USER: QColor(Qt.red),
            LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL: QColor(Qt.cyan),
        },
        2, 0, Qt.ForegroundRole, "#ff0000",
    ),
    (
        {
            LsaSelectorColorRole.BG_CTX_NON_RESIDENT: QColor(Qt.green),
            LsaSelectorColorRole.BG_CTX_RESIDENT: QColor(Qt.blue),
            LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE: QColor(Qt.yellow),
            LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM: QColor(Qt.black),
            LsaSelectorColorRole.FG_USER: QColor(Qt.red),
            LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL: QColor(Qt.cyan),
        },
        2, 1, Qt.ForegroundRole, "#ffa500",
    ),
    (
        {
            LsaSelectorColorRole.BG_CTX_NON_RESIDENT: QColor(Qt.green),
            LsaSelectorColorRole.BG_CTX_RESIDENT: QColor(Qt.blue),
            LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE: QColor(Qt.yellow),
            LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM: QColor(Qt.black),
            LsaSelectorColorRole.FG_USER: QColor(Qt.red),
            LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL: QColor(Qt.cyan),
        },
        3, 0, Qt.ForegroundRole, "#ff0000",
    ),
    (
        {
            LsaSelectorColorRole.BG_CTX_NON_RESIDENT: QColor(Qt.green),
            LsaSelectorColorRole.BG_CTX_RESIDENT: QColor(Qt.blue),
            LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE: QColor(Qt.yellow),
            LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM: QColor(Qt.black),
            LsaSelectorColorRole.FG_USER: QColor(Qt.red),
            LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL: QColor(Qt.cyan),
        },
        3, 1, Qt.ForegroundRole, "#00ffff",
    ),
    (
        {
            LsaSelectorColorRole.BG_CTX_NON_RESIDENT: QColor(Qt.green),
            LsaSelectorColorRole.BG_CTX_RESIDENT: QColor(Qt.blue),
            LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE: QColor(Qt.yellow),
            LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM: QColor(Qt.black),
            LsaSelectorColorRole.FG_USER: QColor(Qt.red),
            LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL: QColor(Qt.cyan),
        },
        4, 0, Qt.ForegroundRole, "#ff0000",
    ),
    (
        {
            LsaSelectorColorRole.BG_CTX_NON_RESIDENT: QColor(Qt.green),
            LsaSelectorColorRole.BG_CTX_RESIDENT: QColor(Qt.blue),
            LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE: QColor(Qt.yellow),
            LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM: QColor(Qt.black),
            LsaSelectorColorRole.FG_USER: QColor(Qt.red),
            LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL: QColor(Qt.cyan),
        },
        4, 1, Qt.ForegroundRole, "#000000",
    ),
    (
        {
            LsaSelectorColorRole.BG_CTX_NON_RESIDENT: QColor(Qt.green),
            LsaSelectorColorRole.BG_CTX_RESIDENT: QColor(Qt.blue),
            LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE: QColor(Qt.yellow),
            LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM: QColor(Qt.black),
            LsaSelectorColorRole.FG_USER: QColor(Qt.red),
            LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL: QColor(Qt.cyan),
        },
        5, 0, Qt.ForegroundRole, "#ff0000",
    ),
    (
        {
            LsaSelectorColorRole.BG_CTX_NON_RESIDENT: QColor(Qt.green),
            LsaSelectorColorRole.BG_CTX_RESIDENT: QColor(Qt.blue),
            LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE: QColor(Qt.yellow),
            LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM: QColor(Qt.black),
            LsaSelectorColorRole.FG_USER: QColor(Qt.red),
            LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL: QColor(Qt.cyan),
        },
        5, 1, Qt.ForegroundRole, "#000000",
    ),
    (
        {
            LsaSelectorColorRole.BG_CTX_NON_RESIDENT: QColor(Qt.green),
            LsaSelectorColorRole.BG_CTX_RESIDENT: QColor(Qt.blue),
            LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE: QColor(Qt.yellow),
            LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM: QColor(Qt.black),
            LsaSelectorColorRole.FG_USER: QColor(Qt.red),
            LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL: QColor(Qt.cyan),
        },
        6, 0, Qt.ForegroundRole, "#ff0000",
    ),
    (
        {
            LsaSelectorColorRole.BG_CTX_NON_RESIDENT: QColor(Qt.green),
            LsaSelectorColorRole.BG_CTX_RESIDENT: QColor(Qt.blue),
            LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE: QColor(Qt.yellow),
            LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM: QColor(Qt.black),
            LsaSelectorColorRole.FG_USER: QColor(Qt.red),
            LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL: QColor(Qt.cyan),
        },
        6, 1, Qt.ForegroundRole, "#000000",
    ),
    (
        {
            LsaSelectorColorRole.BG_CTX_NON_RESIDENT: QColor(Qt.green),
            LsaSelectorColorRole.BG_CTX_RESIDENT: QColor(Qt.blue),
            LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE: QColor(Qt.yellow),
            LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM: QColor(Qt.black),
            LsaSelectorColorRole.FG_USER: QColor(Qt.red),
            LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL: QColor(Qt.cyan),
        },
        7, 0, Qt.ForegroundRole, "#ff0000",
    ),
    (
        {
            LsaSelectorColorRole.BG_CTX_NON_RESIDENT: QColor(Qt.green),
            LsaSelectorColorRole.BG_CTX_RESIDENT: QColor(Qt.blue),
            LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE: QColor(Qt.yellow),
            LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM: QColor(Qt.black),
            LsaSelectorColorRole.FG_USER: QColor(Qt.red),
            LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL: QColor(Qt.cyan),
        },
        7, 1, Qt.ForegroundRole, "#000000",
    ),
])
def test_table_model_table_colors(color_map_mod, row, column, role, expected_color_name, ctxs, qapp):
    _ = qapp  # This is prevention for segfault that occurs randomly
    color_map = {**LsaSelectorModel.DEFAULT_COLOR_MAP, **color_map_mod}
    rows = [LsaSelectorRowViewModel(ctx=ctx) for ctx in ctxs]
    model = LsaSelectorTableModel(row_models=rows,
                                  color_map=color_map,
                                  resident_font=QFont(),
                                  non_resident_font=QFont())
    actual_data = model.index(row, column).data(role)
    assert isinstance(actual_data, QColor)
    assert actual_data.name() == expected_color_name


@pytest.mark.parametrize("ctxs", [
    ([
        LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1_spare",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
        ),
        LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
        ),
        LsaSelectorNonMultiplexedResidentContext(
            name="_NON_MULTIPLEXED_LHC",
            category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
        ),
        LsaSelectorMultiplexedResidentContext(
            name="_ZERO_",
            user="LEI.USER.ZERO",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        ),
        LsaSelectorNonResidentContext(
            name="BP_CAN_BE_RESIDENT_OP",
            multiplexed=True,
            can_become_resident=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        ),
        LsaSelectorNonResidentContext(
            name="STANDALONE_NON_RESIDENT_OP",
            multiplexed=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        ),
        LsaSelectorNonResidentContext(
            name="_NON_PPM_NON_RESIDENT_OP",
            multiplexed=False,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        ),
        LsaSelectorNonResidentContext(
            name="_NON_PPM_CAN_BE_RESIDENT_OP",
            multiplexed=False,
            can_become_resident=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        ),
    ]),
])
@pytest.mark.parametrize("row,column,expected_text", [
    (0, 0, "LIN3MEAS"),
    (0, 1, "LIN3MEASv1_spare"),
    (1, 0, "LIN3MEAS"),
    (1, 1, "LIN3MEASv1"),
    (2, 0, ""),
    (2, 1, "_NON_MULTIPLEXED_LHC"),
    (3, 0, "ZERO"),
    (3, 1, "_ZERO_"),
    (4, 0, ""),
    (4, 1, "BP_CAN_BE_RESIDENT_OP"),
    (5, 0, ""),
    (5, 1, "STANDALONE_NON_RESIDENT_OP"),
    (6, 0, ""),
    (6, 1, "_NON_PPM_NON_RESIDENT_OP"),
    (7, 0, ""),
    (7, 1, "_NON_PPM_CAN_BE_RESIDENT_OP"),
])
def test_table_model_table_cell_text(ctxs, row, column, expected_text):
    rows = [LsaSelectorRowViewModel(ctx=ctx) for ctx in ctxs]
    model = LsaSelectorTableModel(row_models=rows,
                                  color_map={},
                                  resident_font=QFont(),
                                  non_resident_font=QFont())
    assert model.index(row, column).data() == expected_text


@pytest.mark.parametrize("ctxs", [
    ([
        LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1_spare",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE,
        ),
        LsaSelectorMultiplexedResidentContext(
            name="LIN3MEASv1",
            user="LEI.USER.LIN3MEAS",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL,
        ),
        LsaSelectorNonMultiplexedResidentContext(
            name="_NON_MULTIPLEXED_LHC",
            category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL,
        ),
        LsaSelectorMultiplexedResidentContext(
            name="_ZERO_",
            user="LEI.USER.ZERO",
            category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
            user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE,
        ),
        LsaSelectorNonResidentContext(
            name="BP_CAN_BE_RESIDENT_OP",
            multiplexed=True,
            can_become_resident=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        ),
        LsaSelectorNonResidentContext(
            name="STANDALONE_NON_RESIDENT_OP",
            multiplexed=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        ),
        LsaSelectorNonResidentContext(
            name="_NON_PPM_NON_RESIDENT_OP",
            multiplexed=False,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        ),
        LsaSelectorNonResidentContext(
            name="_NON_PPM_CAN_BE_RESIDENT_OP",
            multiplexed=False,
            can_become_resident=True,
            category=LsaSelectorNonResidentContext.Category.OPERATIONAL,
        ),
    ]),
])
@pytest.mark.parametrize("resident_font,non_resident_font,row,column,expected_font", [
    (QFont("Arial", 12), QFont("Verdana", 2), 0, 0, QFont("Arial", 12)),
    (QFont("Arial", 12), QFont("Verdana", 2), 0, 1, QFont("Arial", 12)),
    (QFont("Arial", 12), QFont("Verdana", 2), 1, 0, QFont("Arial", 12)),
    (QFont("Arial", 12), QFont("Verdana", 2), 1, 1, QFont("Arial", 12)),
    (QFont("Arial", 12), QFont("Verdana", 2), 2, 0, QFont("Arial", 12)),
    (QFont("Arial", 12), QFont("Verdana", 2), 2, 1, QFont("Arial", 12)),
    (QFont("Arial", 12), QFont("Verdana", 2), 3, 0, QFont("Arial", 12)),
    (QFont("Arial", 12), QFont("Verdana", 2), 3, 1, QFont("Arial", 12)),
    (QFont("Arial", 12), QFont("Verdana", 2), 4, 0, QFont("Verdana", 2)),
    (QFont("Arial", 12), QFont("Verdana", 2), 4, 1, QFont("Verdana", 2)),
    (QFont("Arial", 12), QFont("Verdana", 2), 5, 0, QFont("Verdana", 2)),
    (QFont("Arial", 12), QFont("Verdana", 2), 5, 1, QFont("Verdana", 2)),
    (QFont("Arial", 12), QFont("Verdana", 2), 6, 0, QFont("Verdana", 2)),
    (QFont("Arial", 12), QFont("Verdana", 2), 6, 1, QFont("Verdana", 2)),
    (QFont("Arial", 12), QFont("Verdana", 2), 7, 0, QFont("Verdana", 2)),
    (QFont("Arial", 12), QFont("Verdana", 2), 7, 1, QFont("Verdana", 2)),
    (QFont("Verdana", 2), QFont("Arial", 12), 0, 0, QFont("Verdana", 2)),
    (QFont("Verdana", 2), QFont("Arial", 12), 0, 1, QFont("Verdana", 2)),
    (QFont("Verdana", 2), QFont("Arial", 12), 1, 0, QFont("Verdana", 2)),
    (QFont("Verdana", 2), QFont("Arial", 12), 1, 1, QFont("Verdana", 2)),
    (QFont("Verdana", 2), QFont("Arial", 12), 2, 0, QFont("Verdana", 2)),
    (QFont("Verdana", 2), QFont("Arial", 12), 2, 1, QFont("Verdana", 2)),
    (QFont("Verdana", 2), QFont("Arial", 12), 3, 0, QFont("Verdana", 2)),
    (QFont("Verdana", 2), QFont("Arial", 12), 3, 1, QFont("Verdana", 2)),
    (QFont("Verdana", 2), QFont("Arial", 12), 4, 0, QFont("Arial", 12)),
    (QFont("Verdana", 2), QFont("Arial", 12), 4, 1, QFont("Arial", 12)),
    (QFont("Verdana", 2), QFont("Arial", 12), 5, 0, QFont("Arial", 12)),
    (QFont("Verdana", 2), QFont("Arial", 12), 5, 1, QFont("Arial", 12)),
    (QFont("Verdana", 2), QFont("Arial", 12), 6, 0, QFont("Arial", 12)),
    (QFont("Verdana", 2), QFont("Arial", 12), 6, 1, QFont("Arial", 12)),
    (QFont("Verdana", 2), QFont("Arial", 12), 7, 0, QFont("Arial", 12)),
    (QFont("Verdana", 2), QFont("Arial", 12), 7, 1, QFont("Arial", 12)),
])
def test_table_model_table_fonts(row, column, resident_font, non_resident_font, expected_font, ctxs):
    rows = [LsaSelectorRowViewModel(ctx=ctx) for ctx in ctxs]
    model = LsaSelectorTableModel(row_models=rows,
                                  color_map={},
                                  resident_font=resident_font,
                                  non_resident_font=non_resident_font)
    actual_data = model.index(row, column).data(Qt.FontRole)
    assert isinstance(actual_data, QFont)
    assert actual_data == expected_font


@pytest.mark.parametrize("rows", [
    ([
        LsaSelectorRowViewModel(
            ctx=LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1_spare",
                                                      user="LEI.USER.LIN3MEAS",
                                                      category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                                      user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE),
            tooltip=LsaSelectorTooltipInfo(users=cast(Set[str], ["TEST.USER.ONE", "TEST.USER.TWO"]),
                                           name="name1",
                                           type_name="type1",
                                           length=13,
                                           description="desc1",
                                           multiplexed=True,
                                           created=datetime(year=2020, day=1, month=1, hour=4, minute=43, second=5),
                                           creator="creator1",
                                           modified=datetime(year=2020, day=1, month=1, hour=4, minute=44, second=5),
                                           modifier="modifier1",
                                           id=1235),

        ),
        LsaSelectorRowViewModel(
            ctx=LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1",
                                                      user="LEI.USER.LIN3MEAS",
                                                      category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                                      user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL),
            tooltip=LsaSelectorTooltipInfo(users={"TEST.USER.ONE"},
                                           name="name2",
                                           type_name="type2",
                                           length=15,
                                           description="desc2",
                                           multiplexed=True,
                                           created=datetime(year=2021, day=1, month=1, hour=4, minute=43, second=5),
                                           creator="creator2",
                                           modified=datetime(year=2019, day=1, month=1, hour=4, minute=44, second=5),
                                           modifier="modifier2",
                                           id=1237),
        ),
        LsaSelectorRowViewModel(
            ctx=LsaSelectorNonMultiplexedResidentContext(name="_NON_MULTIPLEXED_LHC",
                                                         category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL),
            tooltip=LsaSelectorTooltipInfo(users={"TEST.USER.TWO"},
                                           name="name3",
                                           type_name="type3",
                                           length=13,
                                           description="desc3",
                                           multiplexed=True,
                                           created=datetime(year=2018, day=1, month=1, hour=4, minute=43, second=5),
                                           creator="creator3",
                                           modified=datetime(year=2018, day=1, month=1, hour=4, minute=44, second=5),
                                           modifier="modifier3",
                                           id=1238),
        ),
        LsaSelectorRowViewModel(
            ctx=LsaSelectorMultiplexedResidentContext(name="_ZERO_",
                                                      user="LEI.USER.ZERO",
                                                      category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                                      user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE),
            tooltip=LsaSelectorTooltipInfo(users=set(),
                                           name="name4",
                                           type_name="type4",
                                           length=18,
                                           description="desc4",
                                           multiplexed=False,
                                           created=datetime(year=2017, day=1, month=1, hour=4, minute=43, second=5),
                                           creator="creator4",
                                           modified=datetime(year=2017, day=1, month=1, hour=4, minute=44, second=5),
                                           modifier="modifier4",
                                           id=1239),
        ),
        LsaSelectorRowViewModel(
            ctx=LsaSelectorNonResidentContext(name="BP_CAN_BE_RESIDENT_OP",
                                              multiplexed=True,
                                              can_become_resident=True,
                                              category=LsaSelectorNonResidentContext.Category.OPERATIONAL),
            tooltip=LsaSelectorTooltipInfo(users=cast(Set[str], ["TEST.USER.ONE", "TEST2.USER.ONE"]),
                                           name="name5",
                                           type_name="type5",
                                           length=1,
                                           description="desc5",
                                           multiplexed=True,
                                           created=datetime(year=2016, day=1, month=1, hour=4, minute=43, second=5),
                                           creator="creator5",
                                           modified=datetime(year=2016, day=1, month=1, hour=4, minute=44, second=5),
                                           modifier="modifier5",
                                           id=1231),
        ),
        LsaSelectorRowViewModel(
            ctx=LsaSelectorNonResidentContext(name="STANDALONE_NON_RESIDENT_OP",
                                              multiplexed=True,
                                              category=LsaSelectorNonResidentContext.Category.OPERATIONAL),
            tooltip=LsaSelectorTooltipInfo(users=cast(Set[str], ["TEST2.USER.ONE", "TEST2.USER.TWO"]),
                                           name="name6",
                                           type_name="type6",
                                           length=3,
                                           description="desc6",
                                           multiplexed=True,
                                           created=datetime(year=2015, day=1, month=1, hour=4, minute=43, second=5),
                                           creator="creator6",
                                           modified=datetime(year=2015, day=1, month=1, hour=4, minute=44, second=5),
                                           modifier="modifier6",
                                           id=1232),
        ),
        LsaSelectorRowViewModel(ctx=LsaSelectorNonResidentContext(name="_NON_PPM_NON_RESIDENT_OP",
                                                                  multiplexed=False,
                                                                  category=LsaSelectorNonResidentContext.Category.OPERATIONAL)),
        LsaSelectorRowViewModel(
            ctx=LsaSelectorNonResidentContext(name="_NON_PPM_CAN_BE_RESIDENT_OP",
                                              multiplexed=False,
                                              can_become_resident=True,
                                              category=LsaSelectorNonResidentContext.Category.OPERATIONAL),
            tooltip=LsaSelectorTooltipInfo(users=cast(Set[str], ["TEST.USER.ONE", "TEST.USER.TWO"]),
                                           name="name7",
                                           type_name="type7",
                                           length=23,
                                           description="desc7",
                                           multiplexed=False,
                                           created=datetime(year=2014, day=1, month=1, hour=4, minute=43, second=5),
                                           creator="creator7",
                                           modified=datetime(year=2014, day=1, month=1, hour=4, minute=44, second=5),
                                           modifier="modifier7",
                                           id=1233),
        ),
    ]),
])
@pytest.mark.parametrize("column", [0, 1])
@pytest.mark.parametrize("row,expected_string", [
    (0, "<table>"
        '<tr><td align="right"><b>Name:</b></td><td>name1</td></tr>'
        '<tr><td align="right"><b>Type Name:</b></td><td>type1</td></tr>'
        '<tr><td align="right"><b>Length:</b></td><td>13</td></tr>'
        '<tr><td align="right"><b>Description:</b></td><td>desc1</td></tr>'
        '<tr><td align="right"><b>Users:</b></td><td>[TEST.USER.ONE,TEST.USER.TWO]</td></tr>'
        '<tr><td align="right"><b>Multiplexed:</b></td><td>true</td></tr>'
        '<tr><td align="right"><b>Created:</b></td><td>2020-01-01 04:43:05.000</td></tr>'
        '<tr><td align="right"><b>Creator:</b></td><td>creator1</td></tr>'
        '<tr><td align="right"><b>Last Modified:</b></td><td>2020-01-01 04:44:05.000</td></tr>'
        '<tr><td align="right"><b>Modified by:</b></td><td>modifier1</td></tr>'
        '<tr><td align="right"><b>Id:</b></td><td>1235</td></tr>'
        "</table>"),
    (1, "<table>"
        '<tr><td align="right"><b>Name:</b></td><td>name2</td></tr>'
        '<tr><td align="right"><b>Type Name:</b></td><td>type2</td></tr>'
        '<tr><td align="right"><b>Length:</b></td><td>15</td></tr>'
        '<tr><td align="right"><b>Description:</b></td><td>desc2</td></tr>'
        '<tr><td align="right"><b>Users:</b></td><td>[TEST.USER.ONE]</td></tr>'
        '<tr><td align="right"><b>Multiplexed:</b></td><td>true</td></tr>'
        '<tr><td align="right"><b>Created:</b></td><td>2021-01-01 04:43:05.000</td></tr>'
        '<tr><td align="right"><b>Creator:</b></td><td>creator2</td></tr>'
        '<tr><td align="right"><b>Last Modified:</b></td><td>2019-01-01 04:44:05.000</td></tr>'
        '<tr><td align="right"><b>Modified by:</b></td><td>modifier2</td></tr>'
        '<tr><td align="right"><b>Id:</b></td><td>1237</td></tr>'
        "</table>"),
    (2, "<table>"
        '<tr><td align="right"><b>Name:</b></td><td>name3</td></tr>'
        '<tr><td align="right"><b>Type Name:</b></td><td>type3</td></tr>'
        '<tr><td align="right"><b>Length:</b></td><td>13</td></tr>'
        '<tr><td align="right"><b>Description:</b></td><td>desc3</td></tr>'
        '<tr><td align="right"><b>Users:</b></td><td>[TEST.USER.TWO]</td></tr>'
        '<tr><td align="right"><b>Multiplexed:</b></td><td>true</td></tr>'
        '<tr><td align="right"><b>Created:</b></td><td>2018-01-01 04:43:05.000</td></tr>'
        '<tr><td align="right"><b>Creator:</b></td><td>creator3</td></tr>'
        '<tr><td align="right"><b>Last Modified:</b></td><td>2018-01-01 04:44:05.000</td></tr>'
        '<tr><td align="right"><b>Modified by:</b></td><td>modifier3</td></tr>'
        '<tr><td align="right"><b>Id:</b></td><td>1238</td></tr>'
        "</table>"),
    (3, "<table>"
        '<tr><td align="right"><b>Name:</b></td><td>name4</td></tr>'
        '<tr><td align="right"><b>Type Name:</b></td><td>type4</td></tr>'
        '<tr><td align="right"><b>Length:</b></td><td>18</td></tr>'
        '<tr><td align="right"><b>Description:</b></td><td>desc4</td></tr>'
        '<tr><td align="right"><b>Users:</b></td><td>[non-multiplexed]</td></tr>'
        '<tr><td align="right"><b>Multiplexed:</b></td><td>false</td></tr>'
        '<tr><td align="right"><b>Created:</b></td><td>2017-01-01 04:43:05.000</td></tr>'
        '<tr><td align="right"><b>Creator:</b></td><td>creator4</td></tr>'
        '<tr><td align="right"><b>Last Modified:</b></td><td>2017-01-01 04:44:05.000</td></tr>'
        '<tr><td align="right"><b>Modified by:</b></td><td>modifier4</td></tr>'
        '<tr><td align="right"><b>Id:</b></td><td>1239</td></tr>'
        "</table>"),
    (4, "<table>"
        '<tr><td align="right"><b>Name:</b></td><td>name5</td></tr>'
        '<tr><td align="right"><b>Type Name:</b></td><td>type5</td></tr>'
        '<tr><td align="right"><b>Length:</b></td><td>1</td></tr>'
        '<tr><td align="right"><b>Description:</b></td><td>desc5</td></tr>'
        '<tr><td align="right"><b>Users:</b></td><td>[TEST.USER.ONE,TEST2.USER.ONE]</td></tr>'
        '<tr><td align="right"><b>Multiplexed:</b></td><td>true</td></tr>'
        '<tr><td align="right"><b>Created:</b></td><td>2016-01-01 04:43:05.000</td></tr>'
        '<tr><td align="right"><b>Creator:</b></td><td>creator5</td></tr>'
        '<tr><td align="right"><b>Last Modified:</b></td><td>2016-01-01 04:44:05.000</td></tr>'
        '<tr><td align="right"><b>Modified by:</b></td><td>modifier5</td></tr>'
        '<tr><td align="right"><b>Id:</b></td><td>1231</td></tr>'
        "</table>"),
    (5, "<table>"
        '<tr><td align="right"><b>Name:</b></td><td>name6</td></tr>'
        '<tr><td align="right"><b>Type Name:</b></td><td>type6</td></tr>'
        '<tr><td align="right"><b>Length:</b></td><td>3</td></tr>'
        '<tr><td align="right"><b>Description:</b></td><td>desc6</td></tr>'
        '<tr><td align="right"><b>Users:</b></td><td>[TEST2.USER.ONE,TEST2.USER.TWO]</td></tr>'
        '<tr><td align="right"><b>Multiplexed:</b></td><td>true</td></tr>'
        '<tr><td align="right"><b>Created:</b></td><td>2015-01-01 04:43:05.000</td></tr>'
        '<tr><td align="right"><b>Creator:</b></td><td>creator6</td></tr>'
        '<tr><td align="right"><b>Last Modified:</b></td><td>2015-01-01 04:44:05.000</td></tr>'
        '<tr><td align="right"><b>Modified by:</b></td><td>modifier6</td></tr>'
        '<tr><td align="right"><b>Id:</b></td><td>1232</td></tr>'
        "</table>"),
    (6, None),
    (7, "<table>"
        '<tr><td align="right"><b>Name:</b></td><td>name7</td></tr>'
        '<tr><td align="right"><b>Type Name:</b></td><td>type7</td></tr>'
        '<tr><td align="right"><b>Length:</b></td><td>23</td></tr>'
        '<tr><td align="right"><b>Description:</b></td><td>desc7</td></tr>'
        '<tr><td align="right"><b>Users:</b></td><td>[non-multiplexed]</td></tr>'
        '<tr><td align="right"><b>Multiplexed:</b></td><td>false</td></tr>'
        '<tr><td align="right"><b>Created:</b></td><td>2014-01-01 04:43:05.000</td></tr>'
        '<tr><td align="right"><b>Creator:</b></td><td>creator7</td></tr>'
        '<tr><td align="right"><b>Last Modified:</b></td><td>2014-01-01 04:44:05.000</td></tr>'
        '<tr><td align="right"><b>Modified by:</b></td><td>modifier7</td></tr>'
        '<tr><td align="right"><b>Id:</b></td><td>1233</td></tr>'
        "</table>"),
])
def test_table_model_table_tooltips(rows, row, column, expected_string):
    model = LsaSelectorTableModel(row_models=rows,
                                  color_map={},
                                  resident_font=QFont(),
                                  non_resident_font=QFont())
    assert model.index(row, column).data(Qt.ToolTipRole) == expected_string


@pytest.mark.parametrize("active_users", [
    ["LIN3MEAS"],
])
@pytest.mark.parametrize("spare_users", [
    ["SPARE"],
])
@pytest.mark.parametrize("all_ctxs", [
    ([
        (True, "LIN3MEASv1_spare", "LEI.USER.SPARE", LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL, True, False),
        (True, "LIN3MEASv1", "LEI.USER.LIN3MEAS", LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL, True, False),
        (True, "LIN3MEASv1_MD", "LEI.USER.LIN3MEAS", LsaSelectorMultiplexedResidentContext.Category.MD, True, False),
        (True, "_NON_MULTIPLEXED_LHC", "", LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL, False, False),
        (True, "_ZERO_", "LEI.USER.ZERO", LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL, True, False),
        (False, "BP_CAN_BE_RESIDENT_OP", None, LsaSelectorNonResidentContext.Category.OPERATIONAL, True, True),
        (False, "STANDALONE_NON_RESIDENT_OP", None, LsaSelectorNonResidentContext.Category.OPERATIONAL, True, False),
        (False, "_NON_PPM_NON_RESIDENT_OP", None, LsaSelectorNonResidentContext.Category.OPERATIONAL, False, False),
        (False, "_NON_PPM_CAN_BE_RESIDENT_OP", None, LsaSelectorNonResidentContext.Category.OPERATIONAL, False, True),
    ]),
])
@pytest.mark.parametrize("accelerator", [
    LsaSelectorAccelerator.AD,
    LsaSelectorAccelerator.CTF,
    LsaSelectorAccelerator.ISOLDE,
    LsaSelectorAccelerator.LEIR,
    LsaSelectorAccelerator.LHC,
    LsaSelectorAccelerator.PS,
    LsaSelectorAccelerator.PSB,
    LsaSelectorAccelerator.SPS,
    LsaSelectorAccelerator.NORTH,
    LsaSelectorAccelerator.AWAKE,
    LsaSelectorAccelerator.ELENA,
])
@pytest.mark.parametrize("resident_only,categories,expected_ctxs", [
    (True, set(), [
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1_spare",
                                              user="LEI.USER.SPARE",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE),
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1",
                                              user="LEI.USER.LIN3MEAS",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL),
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1_MD",
                                              user="LEI.USER.LIN3MEAS",
                                              category=LsaSelectorMultiplexedResidentContext.Category.MD,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL),
        LsaSelectorNonMultiplexedResidentContext(name="_NON_MULTIPLEXED_LHC",
                                                 category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL),
        LsaSelectorMultiplexedResidentContext(name="_ZERO_",
                                              user="LEI.USER.ZERO",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE),
    ]),
    (True, {AbstractLsaSelectorContext.Category.OPERATIONAL}, [
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1_spare",
                                              user="LEI.USER.SPARE",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE),
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1",
                                              user="LEI.USER.LIN3MEAS",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL),
        LsaSelectorNonMultiplexedResidentContext(name="_NON_MULTIPLEXED_LHC",
                                                 category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL),
        LsaSelectorMultiplexedResidentContext(name="_ZERO_",
                                              user="LEI.USER.ZERO",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE),
    ]),
    (True, {AbstractLsaSelectorContext.Category.MD}, [
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1_MD",
                                              user="LEI.USER.LIN3MEAS",
                                              category=LsaSelectorMultiplexedResidentContext.Category.MD,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL),
    ]),
    (True, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, [
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1_MD",
                                              user="LEI.USER.LIN3MEAS",
                                              category=LsaSelectorMultiplexedResidentContext.Category.MD,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL),
    ]),
    (True, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.OPERATIONAL}, [
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1_spare",
                                              user="LEI.USER.SPARE",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE),
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1",
                                              user="LEI.USER.LIN3MEAS",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL),
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1_MD",
                                              user="LEI.USER.LIN3MEAS",
                                              category=LsaSelectorMultiplexedResidentContext.Category.MD,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL),
        LsaSelectorNonMultiplexedResidentContext(name="_NON_MULTIPLEXED_LHC",
                                                 category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL),
        LsaSelectorMultiplexedResidentContext(name="_ZERO_",
                                              user="LEI.USER.ZERO",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE),
    ]),
    (False, set(), [
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1_spare",
                                              user="LEI.USER.SPARE",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE),
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1",
                                              user="LEI.USER.LIN3MEAS",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL),
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1_MD",
                                              user="LEI.USER.LIN3MEAS",
                                              category=LsaSelectorMultiplexedResidentContext.Category.MD,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL),
        LsaSelectorNonMultiplexedResidentContext(name="_NON_MULTIPLEXED_LHC",
                                                 category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL),
        LsaSelectorMultiplexedResidentContext(name="_ZERO_",
                                              user="LEI.USER.ZERO",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE),
        LsaSelectorNonResidentContext(name="BP_CAN_BE_RESIDENT_OP",
                                      multiplexed=True,
                                      can_become_resident=True,
                                      category=LsaSelectorNonResidentContext.Category.OPERATIONAL),
        LsaSelectorNonResidentContext(name="STANDALONE_NON_RESIDENT_OP",
                                      multiplexed=True,
                                      category=LsaSelectorNonResidentContext.Category.OPERATIONAL),
        LsaSelectorNonResidentContext(name="_NON_PPM_NON_RESIDENT_OP",
                                      multiplexed=False,
                                      category=LsaSelectorNonResidentContext.Category.OPERATIONAL),
        LsaSelectorNonResidentContext(name="_NON_PPM_CAN_BE_RESIDENT_OP",
                                      multiplexed=False,
                                      can_become_resident=True,
                                      category=LsaSelectorNonResidentContext.Category.OPERATIONAL),
    ]),
    (False, {AbstractLsaSelectorContext.Category.OPERATIONAL}, [
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1_spare",
                                              user="LEI.USER.SPARE",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE),
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1",
                                              user="LEI.USER.LIN3MEAS",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL),
        LsaSelectorNonMultiplexedResidentContext(name="_NON_MULTIPLEXED_LHC",
                                                 category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL),
        LsaSelectorMultiplexedResidentContext(name="_ZERO_",
                                              user="LEI.USER.ZERO",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE),
        LsaSelectorNonResidentContext(name="BP_CAN_BE_RESIDENT_OP",
                                      multiplexed=True,
                                      can_become_resident=True,
                                      category=LsaSelectorNonResidentContext.Category.OPERATIONAL),
        LsaSelectorNonResidentContext(name="STANDALONE_NON_RESIDENT_OP",
                                      multiplexed=True,
                                      category=LsaSelectorNonResidentContext.Category.OPERATIONAL),
        LsaSelectorNonResidentContext(name="_NON_PPM_NON_RESIDENT_OP",
                                      multiplexed=False,
                                      category=LsaSelectorNonResidentContext.Category.OPERATIONAL),
        LsaSelectorNonResidentContext(name="_NON_PPM_CAN_BE_RESIDENT_OP",
                                      multiplexed=False,
                                      can_become_resident=True,
                                      category=LsaSelectorNonResidentContext.Category.OPERATIONAL),
    ]),
    (False, {AbstractLsaSelectorContext.Category.MD}, [
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1_MD",
                                              user="LEI.USER.LIN3MEAS",
                                              category=LsaSelectorMultiplexedResidentContext.Category.MD,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL),
    ]),
    (False, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, [
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1_MD",
                                              user="LEI.USER.LIN3MEAS",
                                              category=LsaSelectorMultiplexedResidentContext.Category.MD,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL),
    ]),
    (False, {AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.OPERATIONAL}, [
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1_spare",
                                              user="LEI.USER.SPARE",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE),
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1",
                                              user="LEI.USER.LIN3MEAS",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL),
        LsaSelectorMultiplexedResidentContext(name="LIN3MEASv1_MD",
                                              user="LEI.USER.LIN3MEAS",
                                              category=LsaSelectorMultiplexedResidentContext.Category.MD,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL),
        LsaSelectorNonMultiplexedResidentContext(name="_NON_MULTIPLEXED_LHC",
                                                 category=LsaSelectorNonMultiplexedResidentContext.Category.OPERATIONAL),
        LsaSelectorMultiplexedResidentContext(name="_ZERO_",
                                              user="LEI.USER.ZERO",
                                              category=LsaSelectorMultiplexedResidentContext.Category.OPERATIONAL,
                                              user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE),
        LsaSelectorNonResidentContext(name="BP_CAN_BE_RESIDENT_OP",
                                      multiplexed=True,
                                      can_become_resident=True,
                                      category=LsaSelectorNonResidentContext.Category.OPERATIONAL),
        LsaSelectorNonResidentContext(name="STANDALONE_NON_RESIDENT_OP",
                                      multiplexed=True,
                                      category=LsaSelectorNonResidentContext.Category.OPERATIONAL),
        LsaSelectorNonResidentContext(name="_NON_PPM_NON_RESIDENT_OP",
                                      multiplexed=False,
                                      category=LsaSelectorNonResidentContext.Category.OPERATIONAL),
        LsaSelectorNonResidentContext(name="_NON_PPM_CAN_BE_RESIDENT_OP",
                                      multiplexed=False,
                                      can_become_resident=True,
                                      category=LsaSelectorNonResidentContext.Category.OPERATIONAL),
    ]),
])
def test_contexts_for_accelerator(accelerator, resident_only, categories, expected_ctxs, all_ctxs, active_users, spare_users):

    sys.modules["cern.accsoft.commons.domain"].CernAccelerator = LsaSelectorAccelerator
    sys.modules["cern.lsa.domain.settings"].ContextFamily.BEAMPROCESS = 13

    def make_category_mock(cat: AbstractLsaSelectorContext.Category):
        obj = mock.MagicMock()
        obj.getName.return_value = cat.name
        return obj

    def make_drivable_mock(ctx: Tuple[bool, str, Optional[str], AbstractLsaSelectorContext.Category, bool, bool]):
        is_resident, name, user, cat, is_multiplexed, beam_process = ctx
        obj = mock.MagicMock()
        obj.getName.return_value = name
        obj.getUser.return_value = user
        obj.getContextCategory.return_value = make_category_mock(cat)
        obj.getContextFamily.return_value = sys.modules["cern.lsa.domain.settings"].ContextFamily.BEAMPROCESS if beam_process else None  # type: ignore
        obj.isResident.return_value = is_resident
        obj.isMultiplexed.return_value = is_multiplexed
        return obj

    def make_active_users_mock():
        obj = mock.MagicMock()
        obj.contains.side_effect = lambda x: (x in active_users) or (x in spare_users)
        obj.getNormalUsers.return_value.contains.side_effect = lambda x: x in active_users
        obj.getSpareUsers.return_value.contains.side_effect = lambda x: x in spare_users
        return obj

    def filter_contexts(contexts: Iterable[mock.MagicMock], *_):
        return [ctx for ctx in contexts if ctx.isResident()]

    def filter_category(contexts: Iterable[mock.MagicMock], categories: List[mock.MagicMock]):
        return [ctx for ctx in contexts if ctx.getContextCategory().getName() in map(operator.methodcaller("getName"), categories)]

    def drivable_contexts(contexts: Iterable[mock.MagicMock]):
        return contexts

    def standalone_context(context: mock.MagicMock):
        return context

    def can_become_resident(context: mock.MagicMock, *_):
        return context.getContextFamily() == sys.modules["cern.lsa.domain.settings"].ContextFamily.BEAMPROCESS  # type: ignore

    def get_users(context: mock.MagicMock):
        return {context.getUser()} if context.isResident() else set()

    sys.modules["cern.lsa.client"].ServiceLocator.getService.return_value.findStandAloneCycles.return_value = [make_drivable_mock(ctx) for ctx in all_ctxs]
    sys.modules["cern.lsa.client"].ServiceLocator.getService.return_value.findContextCategories.return_value = [make_category_mock(cat) for cat in AbstractLsaSelectorContext.Category]
    sys.modules["cern.lsa.client"].ServiceLocator.getService.return_value.findActiveTimingUsers.return_value = make_active_users_mock()
    sys.modules["cern.lsa.domain.settings"].Contexts.filterResidentContexts.side_effect = filter_contexts
    sys.modules["cern.lsa.domain.settings"].Contexts.filterByCategories.side_effect = filter_category
    sys.modules["cern.lsa.domain.settings"].Contexts.getDrivableContexts.side_effect = drivable_contexts
    sys.modules["cern.lsa.domain.settings"].Contexts.canBecomeResident.side_effect = can_become_resident
    sys.modules["cern.lsa.domain.settings"].Contexts.getStandAloneContext.side_effect = standalone_context
    sys.modules["cern.lsa.domain.settings"].Contexts.getUsers.side_effect = get_users

    res = contexts_for_accelerator(accelerator=accelerator,
                                   resident_only=resident_only,
                                   categories=categories,
                                   lsa=mock.MagicMock())
    assert list(map(operator.attrgetter("ctx"), res)) == expected_ctxs
