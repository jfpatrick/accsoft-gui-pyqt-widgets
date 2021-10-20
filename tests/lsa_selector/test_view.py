import pytest
import operator
from pytestqt.qtbot import QtBot
from unittest import mock
from typing import cast
from qtpy.QtCore import QObject, QItemSelectionModel
from qtpy.QtWidgets import QLineEdit, QToolButton
from qtpy.QtGui import QColor, QFont
from accwidgets.lsa_selector import (LsaSelectorAccelerator, LsaSelector, AbstractLsaSelectorContext, LsaSelectorModel,
                                     LsaSelectorMultiplexedResidentContext, LsaSelectorNonMultiplexedResidentContext,
                                     LsaSelectorNonResidentContext)
from accwidgets.lsa_selector._model import sample_contexts_for_accelerator, sorted_row_models, LsaSelectorRowViewModel


@pytest.fixture
def sample_model():

    class SampleLsaSelectorModel(LsaSelectorModel):

        def __init__(self, *args, fixed_rows=None, **kwargs):
            self._fixed_rows = fixed_rows
            super().__init__(*args, lsa=mock.MagicMock(), **kwargs)

        def simulate_error(self, message: str):
            self._last_error = message
            self.lsa_error_received.emit(message)

        @property
        def _row_models(self):
            if self._fixed_rows is not None:
                return self._fixed_rows
            if self._rows is None:
                self._rows = sorted_row_models(sample_contexts_for_accelerator(accelerator=self._acc,
                                                                               categories=self._fetch_categories,
                                                                               resident_only=self._fetch_resident_only))
            return self._rows

    return SampleLsaSelectorModel


@pytest.mark.parametrize("widget_enum,expected_enum", [
    (LsaSelector.AD, LsaSelectorAccelerator.AD),
    (LsaSelector.CTF, LsaSelectorAccelerator.CTF),
    (LsaSelector.ISOLDE, LsaSelectorAccelerator.ISOLDE),
    (LsaSelector.LEIR, LsaSelectorAccelerator.LEIR),
    (LsaSelector.LHC, LsaSelectorAccelerator.LHC),
    (LsaSelector.PS, LsaSelectorAccelerator.PS),
    (LsaSelector.PSB, LsaSelectorAccelerator.PSB),
    (LsaSelector.SPS, LsaSelectorAccelerator.SPS),
    (LsaSelector.NORTH, LsaSelectorAccelerator.NORTH),
    (LsaSelector.AWAKE, LsaSelectorAccelerator.AWAKE),
    (LsaSelector.ELENA, LsaSelectorAccelerator.ELENA),
])
def test_accelerator_enum(widget_enum, expected_enum):
    assert widget_enum == expected_enum


@pytest.mark.parametrize("designer_flags,expected_widget_flags,expected_val", [
    (LsaSelector.Test, LsaSelector.ContextCategories.TEST, 0b000001),
    (LsaSelector.Md, LsaSelector.ContextCategories.MD, 0b000010),
    (LsaSelector.Operational, LsaSelector.ContextCategories.OPERATIONAL, 0b000100),
    (LsaSelector.Obsolete, LsaSelector.ContextCategories.OBSOLETE, 0b001000),
    (LsaSelector.Archived, LsaSelector.ContextCategories.ARCHIVED, 0b010000),
    (LsaSelector.Reference, LsaSelector.ContextCategories.REFERENCE, 0b100000),
    (LsaSelector.Test | LsaSelector.Obsolete, LsaSelector.ContextCategories.TEST | LsaSelector.ContextCategories.OBSOLETE, 0b001001),
    (LsaSelector.Reference | LsaSelector.Archived | LsaSelector.Operational,
     LsaSelector.ContextCategories.REFERENCE | LsaSelector.ContextCategories.ARCHIVED | LsaSelector.ContextCategories.OPERATIONAL,
     0b110100),
    (LsaSelector.All, LsaSelector.ContextCategories.ALL, 0b111111),
    (LsaSelector.All,
     (LsaSelector.ContextCategories.MD | LsaSelector.ContextCategories.OBSOLETE | LsaSelector.ContextCategories.TEST
      | LsaSelector.ContextCategories.REFERENCE | LsaSelector.ContextCategories.ARCHIVED | LsaSelector.ContextCategories.OPERATIONAL),
     0b111111),
])
def test_categories_flags(designer_flags, expected_widget_flags, expected_val):
    assert designer_flags == expected_widget_flags == expected_val


@pytest.mark.parametrize("initial_parent", [QObject(), None])
def test_lsa_selector_set_model_changes_ownership(qtbot: QtBot, initial_parent, sample_model):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    new_model = sample_model(parent=initial_parent)
    assert new_model.parent() == initial_parent
    assert widget.model != new_model
    widget.model = new_model
    assert widget.model == new_model
    assert new_model.parent() != initial_parent
    assert new_model.parent() == widget


def test_lsa_selector_disconnects_old_model(qtbot: QtBot, sample_model):
    initial_model = sample_model()
    widget = LsaSelector(model=initial_model)
    qtbot.add_widget(widget)
    initial_table_model = widget._table.model()
    new_model = sample_model()
    assert widget.model == initial_model
    assert widget.model != new_model
    assert initial_model.receivers(initial_model.lsa_error_received) > 0
    assert initial_model.receivers(initial_model.background_color_changed) > 0
    assert initial_model.receivers(initial_model.category_filter_changed) > 0
    assert initial_model.receivers(initial_model.title_filter_changed) > 0
    initial_model_reset_receivers = initial_table_model.receivers(initial_table_model.modelReset)
    initial_data_changed_receivers = initial_table_model.receivers(initial_table_model.dataChanged)
    widget.model = new_model
    new_table_model = widget._table.model()
    assert initial_table_model != new_table_model
    assert widget.model == new_model
    assert widget.model != initial_model
    assert initial_model.receivers(initial_model.lsa_error_received) == 0
    assert initial_model.receivers(initial_model.background_color_changed) == 0
    assert initial_model.receivers(initial_model.category_filter_changed) == 0
    assert initial_model.receivers(initial_model.title_filter_changed) == 0
    assert initial_table_model.receivers(initial_table_model.modelReset) < initial_model_reset_receivers
    assert initial_table_model.receivers(initial_table_model.dataChanged) < initial_data_changed_receivers


def test_lsa_selector_connects_new_model(qtbot: QtBot, sample_model):
    initial_model = sample_model()
    widget = LsaSelector(model=initial_model)
    qtbot.add_widget(widget)
    new_model = sample_model()
    new_table_model = new_model._table_filter
    assert widget.model == initial_model
    assert widget.model != new_model
    assert new_model.receivers(new_model.lsa_error_received) == 0
    assert new_model.receivers(new_model.background_color_changed) == 0
    assert new_model.receivers(new_model.category_filter_changed) == 0
    assert new_model.receivers(new_model.title_filter_changed) == 0
    initial_model_reset_receivers = new_table_model.receivers(new_table_model.modelReset)
    initial_data_changed_receivers = new_table_model.receivers(new_table_model.dataChanged)
    widget.model = new_model
    assert widget._table.model() == new_table_model
    assert new_model.receivers(new_model.lsa_error_received) > 0
    assert new_model.receivers(new_model.background_color_changed) > 0
    assert new_model.receivers(new_model.category_filter_changed) > 0
    assert new_model.receivers(new_model.title_filter_changed) > 0
    assert new_table_model.receivers(new_table_model.modelReset) > initial_model_reset_receivers
    assert new_table_model.receivers(new_table_model.dataChanged) > initial_data_changed_receivers


@pytest.mark.parametrize("initial_val,expected_initial_val", [
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
@pytest.mark.parametrize("new_val,expected_new_val", [
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
    (LsaSelectorAccelerator.AD.value, LsaSelectorAccelerator.AD),
    (LsaSelectorAccelerator.CTF.value, LsaSelectorAccelerator.CTF),
    (LsaSelectorAccelerator.ISOLDE.value, LsaSelectorAccelerator.ISOLDE),
    (LsaSelectorAccelerator.LEIR.value, LsaSelectorAccelerator.LEIR),
    (LsaSelectorAccelerator.LHC.value, LsaSelectorAccelerator.LHC),
    (LsaSelectorAccelerator.PS.value, LsaSelectorAccelerator.PS),
    (LsaSelectorAccelerator.PSB.value, LsaSelectorAccelerator.PSB),
    (LsaSelectorAccelerator.SPS.value, LsaSelectorAccelerator.SPS),
    (LsaSelectorAccelerator.NORTH.value, LsaSelectorAccelerator.NORTH),
    (LsaSelectorAccelerator.AWAKE.value, LsaSelectorAccelerator.AWAKE),
    (LsaSelectorAccelerator.ELENA.value, LsaSelectorAccelerator.ELENA),
])
@pytest.mark.parametrize("is_designer_val", [True, False])
@mock.patch("accwidgets.lsa_selector._view.is_designer")
def test_lsa_selector_accelerator_prop(is_designer, qtbot: QtBot, is_designer_val, sample_model, new_val, expected_new_val,
                                       initial_val, expected_initial_val):
    is_designer.return_value = is_designer_val
    widget = LsaSelector(model=sample_model(accelerator=initial_val))
    qtbot.add_widget(widget)
    assert widget.accelerator == expected_initial_val
    widget.accelerator = new_val
    assert widget.accelerator == expected_new_val


@pytest.mark.parametrize("initial_val,expected_initial_val", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("new_val,expected_new_val", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("is_designer_val", [True, False])
@mock.patch("accwidgets.lsa_selector._view.is_designer")
def test_lsa_selector_resident_only_prop(is_designer, qtbot: QtBot, is_designer_val, sample_model, initial_val,
                                         expected_initial_val, new_val, expected_new_val):
    is_designer.return_value = is_designer_val
    widget = LsaSelector(model=sample_model(resident_only=initial_val))
    qtbot.add_widget(widget)
    assert widget.fetchResidentOnly == expected_initial_val
    widget.fetchResidentOnly = new_val
    assert widget.fetchResidentOnly == expected_new_val
    assert widget.model.resident_only == expected_new_val


@pytest.mark.parametrize("initial_val,expected_initial_val", [
    (None, LsaSelector.ContextCategories.OPERATIONAL),
    (set(), LsaSelector.ContextCategories.OPERATIONAL),
    ({AbstractLsaSelectorContext.Category.MD}, LsaSelector.ContextCategories.MD),
    ({AbstractLsaSelectorContext.Category.TEST}, LsaSelector.ContextCategories.TEST),
    ({AbstractLsaSelectorContext.Category.TEST, AbstractLsaSelectorContext.Category.MD}, LsaSelector.ContextCategories.TEST | LsaSelector.ContextCategories.MD),
    ({AbstractLsaSelectorContext.Category.TEST, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OPERATIONAL},
     LsaSelector.ContextCategories.TEST | LsaSelector.ContextCategories.MD | LsaSelector.ContextCategories.OPERATIONAL),
    ({AbstractLsaSelectorContext.Category.TEST, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OPERATIONAL,
      AbstractLsaSelectorContext.Category.OBSOLETE, AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.REFERENCE},
     LsaSelector.ContextCategories.ALL),
])
@pytest.mark.parametrize("new_val,expected_new_val,expected_model_val", [
    (LsaSelector.ContextCategories.MD, LsaSelector.ContextCategories.MD, {AbstractLsaSelectorContext.Category.MD}),
    (LsaSelector.ContextCategories.TEST, LsaSelector.ContextCategories.TEST, {AbstractLsaSelectorContext.Category.TEST}),
    (LsaSelector.ContextCategories.TEST | LsaSelector.ContextCategories.MD,
     LsaSelector.ContextCategories.TEST | LsaSelector.ContextCategories.MD,
     {AbstractLsaSelectorContext.Category.TEST, AbstractLsaSelectorContext.Category.MD}),
    (LsaSelector.ContextCategories.TEST | LsaSelector.ContextCategories.MD | LsaSelector.ContextCategories.OPERATIONAL,
     LsaSelector.ContextCategories.TEST | LsaSelector.ContextCategories.MD | LsaSelector.ContextCategories.OPERATIONAL,
     {AbstractLsaSelectorContext.Category.TEST, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OPERATIONAL}),
    (LsaSelector.ContextCategories.ALL, LsaSelector.ContextCategories.ALL, set(AbstractLsaSelectorContext.Category)),
])
@pytest.mark.parametrize("is_designer_val", [True, False])
@mock.patch("accwidgets.lsa_selector._view.is_designer")
def test_lsa_selector_displayed_categories_prop(is_designer, qtbot: QtBot, is_designer_val, sample_model, initial_val,
                                                expected_initial_val, new_val, expected_new_val, expected_model_val):
    is_designer.return_value = is_designer_val
    widget = LsaSelector(model=sample_model(categories=initial_val))
    qtbot.add_widget(widget)
    assert widget.contextCategories == expected_initial_val
    widget.contextCategories = new_val
    assert widget.contextCategories == expected_new_val
    assert widget.model.categories == expected_model_val


@pytest.mark.parametrize("new_val,expected_new_val", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("is_designer_val", [True, False])
@mock.patch("accwidgets.lsa_selector._view.is_designer")
def test_lsa_selector_hide_horizontal_header_prop(is_designer, qtbot: QtBot, is_designer_val, sample_model,
                                                  new_val, expected_new_val):
    is_designer.return_value = is_designer_val
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    assert widget.hideHorizontalHeader is False
    assert widget._table.horizontalHeader().isVisible()
    widget.hideHorizontalHeader = new_val
    assert widget.hideHorizontalHeader == expected_new_val
    assert widget._table.horizontalHeader().isHidden() == expected_new_val


@pytest.mark.parametrize("new_val,expected_new_val,expected_widget_class", [
    (True, True, QLineEdit),
    (False, False, type(None)),
])
@pytest.mark.parametrize("is_designer_val", [True, False])
@mock.patch("accwidgets.lsa_selector._view.is_designer")
def test_lsa_selector_show_name_filter_prop(is_designer, qtbot: QtBot, is_designer_val, sample_model,
                                            new_val, expected_new_val, expected_widget_class):
    is_designer.return_value = is_designer_val
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    assert widget.showNameFilter is False
    assert widget._name_filter is None
    widget.showNameFilter = new_val
    assert widget.showNameFilter == expected_new_val
    assert isinstance(widget._name_filter, expected_widget_class)


@pytest.mark.parametrize("new_val,expected_new_val,expected_widget_class", [
    (True, True, QToolButton),
    (False, False, type(None)),
])
@pytest.mark.parametrize("is_designer_val", [True, False])
@mock.patch("accwidgets.lsa_selector._view.is_designer")
def test_lsa_selector_show_category_filter_prop(is_designer, qtbot: QtBot, is_designer_val, sample_model,
                                                new_val, expected_new_val, expected_widget_class):
    is_designer.return_value = is_designer_val
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    with qtbot.wait_exposed(widget):
        widget.show()
    assert widget.showCategoryFilter is False
    assert widget._category_filter is None
    widget.showCategoryFilter = new_val
    assert widget.showCategoryFilter == expected_new_val
    assert isinstance(widget._category_filter, expected_widget_class)


@pytest.mark.parametrize("all_ctxs,resident_only,selected_user,expected_context_name", [
    (
        [
            LsaSelectorMultiplexedResidentContext(name="CTX1", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX2", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX3", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonMultiplexedResidentContext(name="CTX4", category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        ],
        True,
        "TEST.USER.TEST",
        "CTX1",
    ),
    (
        [
            LsaSelectorMultiplexedResidentContext(name="CTX1", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX2", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX3", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonMultiplexedResidentContext(name="CTX4", category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        ],
        True,
        "TEST.USER.TEST",
        "CTX1",
    ),
    (
        [
            LsaSelectorMultiplexedResidentContext(name="CTX1", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX2", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX3", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonMultiplexedResidentContext(name="CTX4", category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        ],
        True,
        "TEST.USER.TEST",
        "CTX1",
    ),
    (
        [
            LsaSelectorMultiplexedResidentContext(name="CTX1", user="TEST.USER.TEST2", user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX2", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX3", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonMultiplexedResidentContext(name="CTX4", category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        ],
        True,
        "TEST.USER.TEST",
        "CTX2",
    ),
    (
        [
            LsaSelectorMultiplexedResidentContext(name="CTX1", user="TEST.USER.TEST2", user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX2", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX3", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonMultiplexedResidentContext(name="CTX4", category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        ],
        True,
        "",
        "CTX4",
    ),
    (
        [
            LsaSelectorMultiplexedResidentContext(name="CTX1", user="TEST.USER.TEST2", user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX2", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX3", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonMultiplexedResidentContext(name="CTX4", category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonResidentContext(name="CTX5", can_become_resident=True, multiplexed=True, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonResidentContext(name="CTX6", can_become_resident=True, multiplexed=False, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonResidentContext(name="CTX7", multiplexed=True, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonResidentContext(name="CTX8", multiplexed=False, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        ],
        False,
        "TEST.USER.TEST",
        "CTX2",
    ),
    (
        [
            LsaSelectorMultiplexedResidentContext(name="CTX1", user="TEST.USER.TEST2", user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX2", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX3", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonMultiplexedResidentContext(name="CTX4", category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonResidentContext(name="CTX5", can_become_resident=True, multiplexed=True, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonResidentContext(name="CTX6", can_become_resident=True, multiplexed=False, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonResidentContext(name="CTX7", multiplexed=True, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonResidentContext(name="CTX8", multiplexed=False, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        ],
        False,
        "",
        "CTX4",
    ),
])
def test_lsa_selector_select_user_selects_first_found(qtbot: QtBot, all_ctxs, resident_only, selected_user, expected_context_name, sample_model):
    rows = [LsaSelectorRowViewModel(ctx=ctx) for ctx in all_ctxs]
    widget = LsaSelector(model=sample_model(fixed_rows=rows, resident_only=resident_only))
    qtbot.add_widget(widget)
    assert not widget._table.selectionModel().hasSelection()
    assert widget.selected_context is None
    widget.select_user(selected_user)
    assert widget._table.selectionModel().hasSelection()
    assert widget.selected_context is not None
    assert widget.selected_context.name == expected_context_name


@pytest.mark.parametrize("all_ctxs,resident_only,selected_user", [
    (
        [
            LsaSelectorMultiplexedResidentContext(name="CTX1", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX2", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX3", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonMultiplexedResidentContext(name="CTX4", category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        ],
        True,
        "TEST.USER.NOTEXISTING",
    ),
    (
        [
            LsaSelectorMultiplexedResidentContext(name="CTX1", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_SPARE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX2", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX3", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonMultiplexedResidentContext(name="CTX4", category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        ],
        True,
        "TEST.USER.NOTEXISTING",
    ),
    (
        [
            LsaSelectorMultiplexedResidentContext(name="CTX1", user="TEST.USER.TEST2", user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX2", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX3", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        ],
        True,
        "",
    ),
    (
        [
            LsaSelectorMultiplexedResidentContext(name="CTX1", user="TEST.USER.TEST2", user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX2", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX3", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonMultiplexedResidentContext(name="CTX4", category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonResidentContext(name="CTX5", can_become_resident=True, multiplexed=True, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonResidentContext(name="CTX6", can_become_resident=True, multiplexed=False, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonResidentContext(name="CTX7", multiplexed=True, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonResidentContext(name="CTX8", multiplexed=False, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        ],
        False,
        "TEST.USER.NOTEXISTING",
    ),
    (
        [
            LsaSelectorMultiplexedResidentContext(name="CTX1", user="TEST.USER.TEST2", user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX2", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorMultiplexedResidentContext(name="CTX3", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonResidentContext(name="CTX5", can_become_resident=True, multiplexed=True, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonResidentContext(name="CTX6", can_become_resident=True, multiplexed=False, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonResidentContext(name="CTX7", multiplexed=True, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
            LsaSelectorNonResidentContext(name="CTX8", multiplexed=False, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        ],
        False,
        "",
    ),
])
def test_lsa_selector_select_user_when_not_found(qtbot: QtBot, all_ctxs, resident_only, selected_user, sample_model):
    rows = [LsaSelectorRowViewModel(ctx=ctx) for ctx in all_ctxs]
    widget = LsaSelector(model=sample_model(fixed_rows=rows, resident_only=resident_only))
    qtbot.add_widget(widget)
    assert not widget._table.selectionModel().hasSelection()
    assert widget.selected_context is None
    widget.select_user(selected_user)
    assert not widget._table.selectionModel().hasSelection()
    assert widget.selected_context is None


def test_lsa_selector_user_color(qtbot, sample_model):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    new_color = QColor(234, 111, 203)
    assert QColor(widget.userColor).name() != new_color.name()
    widget.userColor = new_color
    assert QColor(widget.userColor).name() == new_color.name()


def test_lsa_selector_resident_color(qtbot, sample_model):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    new_color = QColor(234, 111, 203)
    assert QColor(widget.residentColor).name() != new_color.name()
    widget.residentColor = new_color
    assert QColor(widget.residentColor).name() == new_color.name()


def test_lsa_selector_active_color(qtbot, sample_model):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    new_color = QColor(234, 111, 203)
    assert QColor(widget.activeColor).name() != new_color.name()
    widget.activeColor = new_color
    assert QColor(widget.activeColor).name() == new_color.name()


def test_lsa_selector_non_resident_color(qtbot, sample_model):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    new_color = QColor(234, 111, 203)
    assert QColor(widget.nonResidentColor).name() != new_color.name()
    widget.nonResidentColor = new_color
    assert QColor(widget.nonResidentColor).name() == new_color.name()


def test_lsa_selector_spare_color(qtbot, sample_model):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    new_color = QColor(234, 111, 203)
    assert QColor(widget.spareColor).name() != new_color.name()
    widget.spareColor = new_color
    assert QColor(widget.spareColor).name() == new_color.name()


def test_lsa_selector_non_resident_non_ppm_color(qtbot, sample_model):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    new_color = QColor(234, 111, 203)
    assert QColor(widget.nonResidentNonMultiplexedColor).name() != new_color.name()
    widget.nonResidentNonMultiplexedColor = new_color
    assert QColor(widget.nonResidentNonMultiplexedColor).name() == new_color.name()


def test_lsa_selector_resident_bkg_color(qtbot, sample_model):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    new_color = QColor(234, 111, 203)
    assert QColor(widget.residentBackgroundColor).name() != new_color.name()
    widget.residentBackgroundColor = new_color
    assert QColor(widget.residentBackgroundColor).name() == new_color.name()


def test_lsa_selector_non_resident_bkg_color(qtbot, sample_model):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    new_color = QColor(234, 111, 203)
    assert QColor(widget.nonResidentBackgroundColor).name() != new_color.name()
    widget.nonResidentBackgroundColor = new_color
    assert QColor(widget.nonResidentBackgroundColor).name() == new_color.name()


def test_lsa_selector_can_become_resident_bkg_color(qtbot, sample_model):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    new_color = QColor(234, 111, 203)
    assert QColor(widget.canBecomeResidentBackgroundColor).name() != new_color.name()
    widget.canBecomeResidentBackgroundColor = new_color
    assert QColor(widget.canBecomeResidentBackgroundColor).name() == new_color.name()


def test_lsa_selector_selection_bkg_color(qtbot, sample_model):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    new_color = QColor(234, 111, 203)
    assert QColor(widget.selectionBackgroundColor).name() != new_color.name()
    widget.selectionBackgroundColor = new_color
    assert QColor(widget.selectionBackgroundColor).name() == new_color.name()


def test_lsa_selector_selection_color(qtbot, sample_model):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    new_color = QColor(234, 111, 203)
    assert QColor(widget.selectionColor).name() != new_color.name()
    widget.selectionColor = new_color
    assert QColor(widget.selectionColor).name() == new_color.name()


def test_lsa_selector_resident_font(qtbot, sample_model):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    new_font = QFont("Arial", 8)
    assert widget.residentFont != new_font
    widget.residentFont = new_font
    assert widget.residentFont == new_font


def test_lsa_selector_non_resident_font(qtbot, sample_model):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    new_font = QFont("Arial", 8)
    assert widget.nonResidentFont != new_font
    widget.nonResidentFont = new_font
    assert widget.nonResidentFont == new_font


def test_lsa_selector_qss(qtbot, sample_model):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    new_user = QColor(1, 2, 3)
    new_resident = QColor(1, 2, 3)
    new_active = QColor(1, 2, 3)
    new_non_resident = QColor(1, 2, 3)
    new_spare = QColor(1, 2, 3)
    new_non_resident_non_ppm = QColor(1, 2, 3)
    new_resident_bkg = QColor(1, 2, 3)
    new_non_resident_bkg = QColor(1, 2, 3)
    new_can_become_resident_bkg = QColor(1, 2, 3)
    new_selection_bkg = QColor(1, 2, 3)
    new_selection = QColor(1, 2, 3)
    new_resident_font = QFont("Arial", 15)
    new_non_resident_font = QFont("Arial", 14)
    with qtbot.wait_exposed(widget):
        widget.show()
    assert widget.userColor.name() != new_user.name()
    assert widget.residentColor.name() != new_resident.name()
    assert widget.activeColor.name() != new_active.name()
    assert widget.nonResidentColor.name() != new_non_resident.name()
    assert widget.spareColor.name() != new_spare.name()
    assert widget.nonResidentNonMultiplexedColor.name() != new_non_resident_non_ppm.name()
    assert widget.residentBackgroundColor.name() != new_resident_bkg.name()
    assert widget.nonResidentBackgroundColor.name() != new_non_resident_bkg.name()
    assert widget.canBecomeResidentBackgroundColor.name() != new_can_become_resident_bkg.name()
    assert widget.selectionBackgroundColor.name() != new_selection_bkg.name()
    assert widget.selectionColor.name() != new_selection.name()
    assert widget.residentFont != new_resident_font
    assert widget.nonResidentFont != new_non_resident_font

    widget.setStyleSheet(f"LsaSelector{{"
                         f"  qproperty-userColor: {new_user.name()};"
                         f"  qproperty-residentColor: {new_resident.name()};"
                         f"  qproperty-activeColor: {new_active.name()};"
                         f"  qproperty-nonResidentColor: {new_non_resident.name()};"
                         f"  qproperty-spareColor: {new_spare.name()};"
                         f"  qproperty-nonResidentNonMultiplexedColor: {new_non_resident_non_ppm.name()};"
                         f"  qproperty-residentBackgroundColor: {new_resident_bkg.name()};"
                         f"  qproperty-nonResidentBackgroundColor: {new_non_resident_bkg.name()};"
                         f"  qproperty-canBecomeResidentBackgroundColor: {new_can_become_resident_bkg.name()};"
                         f"  qproperty-selectionBackgroundColor: {new_selection_bkg.name()};"
                         f"  qproperty-selectionColor: {new_selection.name()};"
                         f'  qproperty-residentFont: "{new_resident_font.toString()}";'
                         f'  qproperty-nonResidentFont: "{new_non_resident_font.toString()}";'
                         f"}}")
    assert widget.userColor.name() == new_user.name()
    assert widget.residentColor.name() == new_resident.name()
    assert widget.activeColor.name() == new_active.name()
    assert widget.nonResidentColor.name() == new_non_resident.name()
    assert widget.spareColor.name() == new_spare.name()
    assert widget.nonResidentNonMultiplexedColor.name() == new_non_resident_non_ppm.name()
    assert widget.residentBackgroundColor.name() == new_resident_bkg.name()
    assert widget.nonResidentBackgroundColor.name() == new_non_resident_bkg.name()
    assert widget.canBecomeResidentBackgroundColor.name() == new_can_become_resident_bkg.name()
    assert widget.selectionBackgroundColor.name() == new_selection_bkg.name()
    assert widget.selectionColor.name() == new_selection.name()
    assert widget.residentFont == new_resident_font
    assert widget.nonResidentFont == new_non_resident_font


def test_lsa_selector_error_shows(qtbot, sample_model):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    assert widget._stack.currentIndex() == 0
    assert not widget._error_label.text()
    widget.model.simulate_error("Test simulated error")
    assert widget._stack.currentIndex() == 1
    assert widget._error_label.text() == "<b>LSA problem occurred</b>:<br/>Test simulated error"


@pytest.mark.parametrize("initial_resident_only,initial_categories,expected_initial_title,expected_initial_menu,expected_initial_checked", [
    (True, None, "Showing: OPERATIONAL", ["OPERATIONAL"], [True]),
    (True, set(), "Showing: OPERATIONAL", ["OPERATIONAL"], [True]),
    (True, {AbstractLsaSelectorContext.Category.OPERATIONAL}, "Showing: OPERATIONAL", ["OPERATIONAL"], [True]),
    (True, {AbstractLsaSelectorContext.Category.MD}, "Showing: MD", ["MD"], [True]),
    (True, {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD}, "Showing: MD, OPERATIONAL", ["MD", "OPERATIONAL"], [True, True]),
    (False, None, "Showing: OPERATIONAL", ["OPERATIONAL"], [True]),
    (False, set(), "Showing: OPERATIONAL", ["OPERATIONAL"], [True]),
    (False, {AbstractLsaSelectorContext.Category.OPERATIONAL}, "Showing: OPERATIONAL", ["OPERATIONAL"], [True]),
    (False, {AbstractLsaSelectorContext.Category.MD}, "Showing: MD", ["MD"], [True]),
    (False, {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD}, "Showing: MD, OPERATIONAL", ["MD", "OPERATIONAL"], [True, True]),
])
@pytest.mark.parametrize("new_resident_only,new_categories,expected_new_title,expected_new_menu,expected_new_checked", [
    (True, set(), "Showing: MD, OPERATIONAL", ["MD", "OPERATIONAL"], [True, True]),
    (True, {AbstractLsaSelectorContext.Category.OPERATIONAL}, "Showing: OPERATIONAL", ["OPERATIONAL"], [True]),
    (True, {AbstractLsaSelectorContext.Category.MD}, "Showing: MD", ["MD"], [True]),
    (True, {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD}, "Showing: MD, OPERATIONAL", ["MD", "OPERATIONAL"], [True, True]),
    (False, set(), "Showing: ARCHIVED, MD, OBSOLETE, OPERATIONAL, REFERENCE, TEST", ["ARCHIVED", "MD", "OBSOLETE", "OPERATIONAL", "REFERENCE", "TEST"], [True, True, True, True, True, True]),
    (False, {AbstractLsaSelectorContext.Category.OPERATIONAL}, "Showing: OPERATIONAL", ["OPERATIONAL"], [True]),
    (False, {AbstractLsaSelectorContext.Category.MD}, "Showing: MD", ["MD"], [True]),
    (False, {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD}, "Showing: MD, OPERATIONAL", ["MD", "OPERATIONAL"], [True, True]),
])
def test_lsa_selector_category_filter_reacts_to_model_changes(qtbot, sample_model, initial_categories, initial_resident_only,
                                                              expected_initial_menu, expected_initial_title, expected_initial_checked,
                                                              new_categories, new_resident_only, expected_new_menu, expected_new_title,
                                                              expected_new_checked):
    widget = LsaSelector(model=sample_model(resident_only=initial_resident_only, categories=initial_categories))
    qtbot.add_widget(widget)
    widget.showCategoryFilter = True
    assert widget._category_filter.text() == expected_initial_title
    assert list(map(operator.methodcaller("text"), widget._category_filter.menu().actions())) == expected_initial_menu
    assert list(map(operator.methodcaller("isChecked"), widget._category_filter.menu().actions())) == expected_initial_checked
    widget.model.resident_only = new_resident_only
    widget.model.categories = new_categories
    assert widget._category_filter.text() == expected_new_title
    assert list(map(operator.methodcaller("text"), widget._category_filter.menu().actions())) == expected_new_menu
    assert list(map(operator.methodcaller("isChecked"), widget._category_filter.menu().actions())) == expected_new_checked


@pytest.mark.parametrize("filter_title,expected_field_text", [
    ("abc", "abc"),
    ("9A,'", "9A,'"),
    (None, ""),
    ("", ""),
])
def test_lsa_selector_name_filter_reacts_to_model_changes(qtbot: QtBot, sample_model, filter_title, expected_field_text):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    widget.showNameFilter = True
    name_filter = cast(QLineEdit, widget._name_filter)
    assert not name_filter.text()
    widget.model.filter_title = filter_title
    assert name_filter.text() == expected_field_text


@pytest.mark.parametrize("typed_text,expected_filter", [
    ("abc", "abc"),
    ("9A,'", "9A,'"),
    ("", ""),
])
def test_lsa_selector_name_filter_typing_updates_model(qtbot: QtBot, sample_model, typed_text, expected_filter):
    widget = LsaSelector(model=sample_model())
    qtbot.add_widget(widget)
    widget.showNameFilter = True
    assert widget.model.filter_title == ""
    assert isinstance(widget._name_filter, QLineEdit)
    qtbot.keyClicks(widget._name_filter, typed_text)
    assert widget.model.filter_title == expected_filter


@pytest.mark.parametrize("resident_only,initial_categories,leave_selected,expected_categories", [
    (True, None, set(), set()),
    (True, set(), set(), set()),
    (True, {AbstractLsaSelectorContext.Category.OPERATIONAL}, set(), set()),
    (True, {AbstractLsaSelectorContext.Category.MD}, set(), set()),
    (True, {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD}, set(), set()),
    (True, {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, set(), set()),
    (False, None, set(), set()),
    (False, set(), set(), set()),
    (False, {AbstractLsaSelectorContext.Category.OPERATIONAL}, set(), set()),
    (False, {AbstractLsaSelectorContext.Category.MD}, set(), set()),
    (False, {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED}, set(), set()),
    (True, None, {AbstractLsaSelectorContext.Category.OPERATIONAL}, set()),
    (True, set(), {AbstractLsaSelectorContext.Category.OPERATIONAL}, set()),
    (True, {AbstractLsaSelectorContext.Category.OPERATIONAL}, {AbstractLsaSelectorContext.Category.OPERATIONAL}, set()),
    (True,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.OPERATIONAL},
     {AbstractLsaSelectorContext.Category.OPERATIONAL}),
    (True,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.OPERATIONAL},
     {AbstractLsaSelectorContext.Category.OPERATIONAL}),
    (False, None, {AbstractLsaSelectorContext.Category.OPERATIONAL}, set()),
    (False, set(), {AbstractLsaSelectorContext.Category.OPERATIONAL}, set()),
    (False, {AbstractLsaSelectorContext.Category.OPERATIONAL}, {AbstractLsaSelectorContext.Category.OPERATIONAL}, set()),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.OPERATIONAL},
     {AbstractLsaSelectorContext.Category.OPERATIONAL}),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.OPERATIONAL},
     {AbstractLsaSelectorContext.Category.OPERATIONAL}),
    (True, {AbstractLsaSelectorContext.Category.MD}, {AbstractLsaSelectorContext.Category.MD}, set()),
    (True,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.MD}),
    (True,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.MD}),
    (False, {AbstractLsaSelectorContext.Category.MD}, {AbstractLsaSelectorContext.Category.MD}, set()),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.MD}),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.MD}),
    (True,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     set()),
    (True,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     set()),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     set()),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD}),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.ARCHIVED}),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.MD}),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OPERATIONAL},
     set()),
])
def test_lsa_selector_toggling_category_filter_updates_model(qtbot, sample_model, initial_categories, resident_only,
                                                             leave_selected, expected_categories):
    widget = LsaSelector(model=sample_model(resident_only=resident_only, categories=initial_categories))
    qtbot.add_widget(widget)
    widget.showCategoryFilter = True
    leave_selected_titles = list(map(operator.attrgetter("name"), leave_selected))
    for action in widget._category_filter.menu().actions():
        if ((action.text() in leave_selected_titles and not action.isChecked())
                or (action.text() not in leave_selected_titles and action.isChecked())):
            action.trigger()
    assert widget.model.filter_categories == expected_categories


@pytest.mark.parametrize("resident_only,initial_categories,leave_selected,expected_title", [
    (True, None, set(), "Showing: OPERATIONAL"),
    (True, set(), set(), "Showing: OPERATIONAL"),
    (True, {AbstractLsaSelectorContext.Category.OPERATIONAL}, set(), "Showing: OPERATIONAL"),
    (True, {AbstractLsaSelectorContext.Category.MD}, set(), "Showing: MD"),
    (True,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     set(),
     "Showing: MD, OPERATIONAL"),
    (True,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     set(),
     "Showing: MD, OPERATIONAL"),
    (False, None, set(), "Showing: OPERATIONAL"),
    (False, set(), set(), "Showing: OPERATIONAL"),
    (False, {AbstractLsaSelectorContext.Category.OPERATIONAL}, set(), "Showing: OPERATIONAL"),
    (False, {AbstractLsaSelectorContext.Category.MD}, set(), "Showing: MD"),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     set(),
     "Showing: ARCHIVED, MD, OPERATIONAL"),
    (True, None, {AbstractLsaSelectorContext.Category.OPERATIONAL}, "Showing: OPERATIONAL"),
    (True, set(), {AbstractLsaSelectorContext.Category.OPERATIONAL}, "Showing: OPERATIONAL"),
    (True,
     {AbstractLsaSelectorContext.Category.OPERATIONAL},
     {AbstractLsaSelectorContext.Category.OPERATIONAL},
     "Showing: OPERATIONAL"),
    (True,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.OPERATIONAL},
     "Showing: OPERATIONAL"),
    (True,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.OPERATIONAL},
     "Showing: OPERATIONAL"),
    (False, None, {AbstractLsaSelectorContext.Category.OPERATIONAL}, "Showing: OPERATIONAL"),
    (False, set(), {AbstractLsaSelectorContext.Category.OPERATIONAL}, "Showing: OPERATIONAL"),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL},
     {AbstractLsaSelectorContext.Category.OPERATIONAL},
     "Showing: OPERATIONAL"),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.OPERATIONAL},
     "Showing: OPERATIONAL"),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.OPERATIONAL},
     "Showing: OPERATIONAL"),
    (True, {AbstractLsaSelectorContext.Category.MD}, {AbstractLsaSelectorContext.Category.MD}, "Showing: MD"),
    (True,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.MD},
     "Showing: MD"),
    (True,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.MD},
     "Showing: MD"),
    (False, {AbstractLsaSelectorContext.Category.MD}, {AbstractLsaSelectorContext.Category.MD}, "Showing: MD"),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.MD},
     "Showing: MD"),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.MD},
     "Showing: MD"),
    (True,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     "Showing: MD, OPERATIONAL"),
    (True,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     "Showing: MD, OPERATIONAL"),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     "Showing: MD, OPERATIONAL"),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD},
     "Showing: MD, OPERATIONAL"),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.ARCHIVED},
     "Showing: ARCHIVED"),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.MD},
     "Showing: ARCHIVED, MD"),
    (False,
     {AbstractLsaSelectorContext.Category.OPERATIONAL, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.ARCHIVED},
     {AbstractLsaSelectorContext.Category.ARCHIVED, AbstractLsaSelectorContext.Category.MD, AbstractLsaSelectorContext.Category.OPERATIONAL},
     "Showing: ARCHIVED, MD, OPERATIONAL"),
])
def test_lsa_selector_toggling_category_filter_updates_its_title(qtbot, sample_model, initial_categories, resident_only,
                                                                 leave_selected, expected_title):
    widget = LsaSelector(model=sample_model(resident_only=resident_only, categories=initial_categories))
    qtbot.add_widget(widget)
    widget.showCategoryFilter = True
    leave_selected_titles = list(map(operator.attrgetter("name"), leave_selected))
    for action in widget._category_filter.menu().actions():
        if ((action.text() in leave_selected_titles and not action.isChecked())
                or (action.text() not in leave_selected_titles and action.isChecked())):
            action.trigger()
    assert widget._category_filter.text() == expected_title


@pytest.mark.parametrize("all_ctxts", [
    [
        LsaSelectorMultiplexedResidentContext(name="CTX1", user="TEST.USER.TEST2", user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        LsaSelectorMultiplexedResidentContext(name="CTX2", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        LsaSelectorMultiplexedResidentContext(name="CTX3", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        LsaSelectorNonMultiplexedResidentContext(name="CTX4", category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        LsaSelectorNonResidentContext(name="CTX5", can_become_resident=True, multiplexed=True, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        LsaSelectorNonResidentContext(name="CTX6", can_become_resident=True, multiplexed=False, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        LsaSelectorNonResidentContext(name="CTX7", multiplexed=True, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        LsaSelectorNonResidentContext(name="CTX8", multiplexed=False, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
    ],
])
@pytest.mark.parametrize("is_resident,selected_row,expected_context", [
    (True, 0, LsaSelectorMultiplexedResidentContext(name="CTX1", user="TEST.USER.TEST2", user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE, category=AbstractLsaSelectorContext.Category.OPERATIONAL)),
    (True, 1, LsaSelectorMultiplexedResidentContext(name="CTX2", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL)),
    (True, 2, LsaSelectorMultiplexedResidentContext(name="CTX3", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL)),
    (True, 3, LsaSelectorNonMultiplexedResidentContext(name="CTX4", category=AbstractLsaSelectorContext.Category.OPERATIONAL)),
    (False, 0, LsaSelectorMultiplexedResidentContext(name="CTX1", user="TEST.USER.TEST2", user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE, category=AbstractLsaSelectorContext.Category.OPERATIONAL)),
    (False, 1, LsaSelectorMultiplexedResidentContext(name="CTX2", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL)),
    (False, 2, LsaSelectorMultiplexedResidentContext(name="CTX3", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL)),
    (False, 3, LsaSelectorNonMultiplexedResidentContext(name="CTX4", category=AbstractLsaSelectorContext.Category.OPERATIONAL)),
    (False, 4, LsaSelectorNonResidentContext(name="CTX5", can_become_resident=True, multiplexed=True, category=AbstractLsaSelectorContext.Category.OPERATIONAL)),
    (False, 5, LsaSelectorNonResidentContext(name="CTX6", can_become_resident=True, multiplexed=False, category=AbstractLsaSelectorContext.Category.OPERATIONAL)),
    (False, 6, LsaSelectorNonResidentContext(name="CTX7", multiplexed=True, category=AbstractLsaSelectorContext.Category.OPERATIONAL)),
    (False, 7, LsaSelectorNonResidentContext(name="CTX8", multiplexed=False, category=AbstractLsaSelectorContext.Category.OPERATIONAL)),
])
def test_lsa_selector_table_selection_emits_context_signal(qtbot: QtBot, sample_model, is_resident, selected_row, expected_context, all_ctxts):
    used_contexts = all_ctxts if not is_resident else [ctx for ctx in all_ctxts if not isinstance(ctx, LsaSelectorNonResidentContext)]
    rows = [LsaSelectorRowViewModel(ctx=ctx) for ctx in used_contexts]
    widget = LsaSelector(model=sample_model(fixed_rows=rows, resident_only=is_resident))
    qtbot.add_widget(widget)
    with qtbot.wait_signal(widget.contextSelectionChanged) as blocker:
        widget._table.selectionModel().select(widget._table.model().index(selected_row, 1), QItemSelectionModel.Select)
    assert blocker.args == [expected_context]


@pytest.mark.parametrize("all_ctxts", [
    [
        LsaSelectorMultiplexedResidentContext(name="CTX1", user="TEST.USER.TEST2", user_type=LsaSelectorMultiplexedResidentContext.UserType.INACTIVE, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        LsaSelectorMultiplexedResidentContext(name="CTX2", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        LsaSelectorMultiplexedResidentContext(name="CTX3", user="TEST.USER.TEST", user_type=LsaSelectorMultiplexedResidentContext.UserType.ACTIVE_NORMAL, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        LsaSelectorNonMultiplexedResidentContext(name="CTX4", category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        LsaSelectorNonResidentContext(name="CTX5", can_become_resident=True, multiplexed=True, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        LsaSelectorNonResidentContext(name="CTX6", can_become_resident=True, multiplexed=False, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        LsaSelectorNonResidentContext(name="CTX7", multiplexed=True, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
        LsaSelectorNonResidentContext(name="CTX8", multiplexed=False, category=AbstractLsaSelectorContext.Category.OPERATIONAL),
    ],
])
@pytest.mark.parametrize("is_resident,selected_row,expect_signal,expected_user", [
    (True, 0, True, "TEST.USER.TEST2"),
    (True, 1, True, "TEST.USER.TEST"),
    (True, 2, True, "TEST.USER.TEST"),
    (True, 3, True, ""),
    (False, 0, True, "TEST.USER.TEST2"),
    (False, 1, True, "TEST.USER.TEST"),
    (False, 2, True, "TEST.USER.TEST"),
    (False, 3, True, ""),
    (False, 4, False, None),
    (False, 5, False, None),
    (False, 6, False, None),
    (False, 7, False, None),
])
def test_lsa_selector_table_selection_emits_user_signal_for_resident_contexts(qtbot: QtBot, sample_model, is_resident,
                                                                              selected_row, expect_signal,
                                                                              expected_user, all_ctxts):
    used_contexts = all_ctxts if not is_resident else [ctx for ctx in all_ctxts if not isinstance(ctx, LsaSelectorNonResidentContext)]
    rows = [LsaSelectorRowViewModel(ctx=ctx) for ctx in used_contexts]
    widget = LsaSelector(model=sample_model(fixed_rows=rows, resident_only=is_resident))
    qtbot.add_widget(widget)
    with qtbot.wait_signal(widget.userSelectionChanged, raising=False, timeout=100) as blocker:
        widget._table.selectionModel().select(widget._table.model().index(selected_row, 1), QItemSelectionModel.Select)
    assert blocker.signal_triggered == expect_signal
    if expect_signal:
        assert blocker.args == [expected_user]
