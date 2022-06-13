import operator
import qtawesome as qta
from typing import Optional, cast, Set
from enum import IntFlag
from qtpy.QtCore import (Qt, Signal, Property, Q_ENUMS, Q_FLAGS, QItemSelectionModel, QSignalBlocker,
                         QEvent, QTimer, QItemSelection)
from qtpy.QtGui import QColor, QFont, QPalette, QMouseEvent
from qtpy.QtWidgets import (QFrame, QWidget, QTableView, QAbstractItemView, QVBoxLayout, QHeaderView, QLineEdit,
                            QToolButton, QMenu, QAction, QSizePolicy, QStackedLayout, QLabel, QSpacerItem)
from accwidgets.designer_check import is_designer
from ._model import (LsaSelectorModel, AbstractLsaSelectorContext, LsaSelectorAccelerator, CONTEXT_TABLE_ROLE,
                     LsaSelectorColorRole, Color, AbstractLsaSelectorResidentContext)


class _QtDesignerAccelerator:
    pass


for acc in LsaSelectorAccelerator:
    setattr(_QtDesignerAccelerator, acc.name, LsaSelectorAccelerator[acc.name].value)


def index_of_category_enum_item(cat: AbstractLsaSelectorContext.Category):
    return list(AbstractLsaSelectorContext.Category.__members__.keys()).index(cat.name)


class _QtDesignerContextCategories:
    pass


all_categories_val = 0
for cat in AbstractLsaSelectorContext.Category:
    # This has to be before LsaSelector class definition for Qt Designer to correctly pick up options
    shift = index_of_category_enum_item(cat)
    value = 1 << shift
    setattr(_QtDesignerContextCategories, cat.name.title(), value)
    all_categories_val |= value

_QtDesignerContextCategories.All = all_categories_val  # type: ignore


class LsaSelector(QWidget, _QtDesignerAccelerator, _QtDesignerContextCategories):

    class ContextCategories(IntFlag):
        """
        Context category options, similar to that of :class:`AbstractLsaSelectorContext.Category`, except
        converted into a flags object rather than enumeration to allow multi-choice selection in Qt Designer.
        """

        TEST = _QtDesignerContextCategories.Test                # type: ignore  # this is populated dynamically
        """Test."""

        MD = _QtDesignerContextCategories.Md                    # type: ignore  # this is populated dynamically
        """Machine Development."""

        OPERATIONAL = _QtDesignerContextCategories.Operational  # type: ignore  # this is populated dynamically
        """Operational."""

        OBSOLETE = _QtDesignerContextCategories.Obsolete        # type: ignore  # this is populated dynamically
        """Obsolete."""

        ARCHIVED = _QtDesignerContextCategories.Archived        # type: ignore  # this is populated dynamically
        """Set of LSA settings that is archived can be used to restore the accelerator to a previously known state."""

        REFERENCE = _QtDesignerContextCategories.Reference      # type: ignore  # this is populated dynamically
        """Reference settings allow highlighting the differences between the current setup and some known state."""

        ALL = _QtDesignerContextCategories.All                  # type: ignore  # this is populated dynamically
        """Convenience flag to select all categories at once."""

    Q_ENUMS(_QtDesignerAccelerator)
    Q_FLAGS(_QtDesignerContextCategories)

    contextSelectionChanged = Signal(AbstractLsaSelectorContext)
    """
    Signal fired whenever users selects a new context in the table. The argument is a context object associated with
    the selected table row.

    :type: pyqtSignal
    """

    userSelectionChanged = Signal(str)
    """
    Signal fired whenever user selects a new resident contexts. Since non-resident contexts are not associated with any
    user, this signal is omitted. The argument is a complete timing user selector, e.g. ``LEI.USER.LIN3MEAS``.

    :type: pyqtSignal
    """

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 model: Optional[LsaSelectorModel] = None):
        """
        LSA selector exposes a selectable table with a list of LSA cycles/contexts and associated timing users.
        User can select one cycle at a time, which triggers :attr:`contextSelectionChanged` signal and
        :attr:`userSelectionChanged` for resident contexts.

        Args:
            parent: Owning object.
            model: Model that handles communication with LSA server.
        """
        super().__init__(parent)

        if is_designer():
            # This is a workaround for Qt Designer. We cause instance of QtAwesome to be created in order
            # to register its fonts. Because if it is done later, when it registers fonts in QFontDatabase,
            # Qt Designer weirdly reacts to it by resetting all QFont-based widget properties to a non-default
            # font (presumably first in the database list, called "aakar"). This call ensures that font is
            # registered before Qt Designer gets to affect properties.
            _ = qta.font("mdi", self.font().pointSize())

        stack_layout = QStackedLayout()
        stack_layout.setStackingMode(QStackedLayout.StackAll)

        main_widget = QWidget(self)

        self._table = LeftClickTableView(self)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(1)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._table)
        main_widget.setLayout(main_layout)
        stack_layout.addWidget(main_widget)
        self.setLayout(stack_layout)
        self._main_layout = main_layout
        self.__error_label: Optional[QLabel] = None
        self._stack = stack_layout

        self._color_selection = self._table.palette().color(QPalette.Highlight)
        self._color_selection_text = self._table.palette().color(QPalette.HighlightedText)
        self._hide_header = False
        self._name_filter: Optional[QLineEdit] = None
        self._category_filter: Optional[LsaSelectorCategoryFilterButton] = None

        self._model = model or LsaSelectorModel()

        self._table.setShowGrid(False)
        self._table.verticalHeader().hide()
        self._table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self._table.verticalHeader().setDefaultSectionSize(10)
        self._table.setSelectionBehavior(QTableView.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setFrameShape(QFrame.Box)
        self._table.setFrameShadow(QFrame.Sunken)
        self._table.setAlternatingRowColors(False)

        self._connect_model(self._model)

    def _get_model(self) -> LsaSelectorModel:
        return self._model

    def _set_model(self, new_val: LsaSelectorModel):
        if new_val == self._model:
            return
        self._disconnect_model(self._model)
        self._model = new_val
        self._connect_model(new_val)

    model = property(fget=_get_model, fset=_set_model)
    """
    Model that handles communication with LSA server.

    When assigning a new model, its ownership is transferred to the widget.
    """

    def _get_accelerator(self) -> LsaSelectorAccelerator:
        if is_designer():
            return self.model.accelerator.value
        return self.model.accelerator

    def _set_accelerator(self, new_val: LsaSelectorAccelerator):
        if isinstance(new_val, int) or isinstance(new_val, _QtDesignerAccelerator):
            new_val = LsaSelectorAccelerator(new_val)
        self.model.accelerator = new_val

    accelerator = Property(_QtDesignerAccelerator, fget=_get_accelerator, fset=_set_accelerator)
    """
    LSA accelerator to retrieve cycles for. Updating this property will automatically re-fetch data.

    :type: LsaSelectorAccelerator
    """

    def _get_resident_only(self) -> bool:
        return self.model.resident_only

    def _set_resident_only(self, new_val: bool):
        self.model.resident_only = new_val

    fetchResidentOnly = Property(bool, fget=_get_resident_only, fset=_set_resident_only)
    """
    Choice for retrieving only resident or all LSA cycles. Updating this property will automatically re-fetch data.

    :type: bool
    """

    def _get_displayed_categories(self) -> "LsaSelector.ContextCategories":
        flags = LsaSelector.ContextCategories(0)
        for cat in self.model.categories:
            shift = index_of_category_enum_item(cat)
            flags |= LsaSelector.ContextCategories(1 << shift)

        if is_designer():
            return int(flags)  # type: ignore
        return flags

    def _set_displayed_categories(self, new_val: "LsaSelector.ContextCategories"):
        if not isinstance(new_val, LsaSelector.ContextCategories) or isinstance(new_val, _QtDesignerContextCategories):
            new_val = LsaSelector.ContextCategories(new_val)
        new_set: Set[AbstractLsaSelectorContext.Category] = set()
        for member in LsaSelector.ContextCategories:
            if member == LsaSelector.ContextCategories.ALL:
                continue
            if (new_val & member) and member.name:
                new_set.add(AbstractLsaSelectorContext.Category[member.name])
        self.model.categories = new_set

    contextCategories = Property(_QtDesignerContextCategories, fget=_get_displayed_categories, fset=_set_displayed_categories)
    """
    Choice to limit cycles to only specific context categories. Updating this property will automatically re-fetch data.

    :type: LsaSelector.ContextCategories
    """

    def _get_hide_header(self) -> bool:
        # We use local value, not isHidden(), because isHidden will be affected by window shown/not shown, not
        # representing logical intention
        return self._hide_header

    def _set_hide_header(self, new_val: bool):
        self._hide_header = new_val
        self._table.horizontalHeader().setHidden(new_val)

    hideHorizontalHeader = Property(bool, fget=_get_hide_header, fset=_set_hide_header)
    """
    Flag to hide table header with column names.

    :type: bool
    """

    def _get_show_name_filter(self) -> bool:
        return self._name_filter is not None

    def _set_show_name_filter(self, new_val: bool):
        if self.showNameFilter == new_val:
            return
        if self._name_filter:
            self._main_layout.removeWidget(self._name_filter)
            self._name_filter.deleteLater()
            self._name_filter = None
        elif new_val:
            self._name_filter = QLineEdit(self)
            self._name_filter.setPlaceholderText("Type context name to filter…")
            self._name_filter.textEdited.connect(self._on_name_filter_typed)
            self._main_layout.insertWidget(1, self._name_filter)
            self._update_name_filter()

    showNameFilter = Property(bool, fget=_get_show_name_filter, fset=_set_show_name_filter)
    """
    Flag to show the text input that filters the displayed contexts by name.

    :type: bool
    """

    def _get_show_category_filter(self) -> bool:
        return self._category_filter is not None

    def _set_show_category_filter(self, new_val: bool):
        if self.showCategoryFilter == new_val:
            return
        if self._category_filter:
            self._main_layout.removeWidget(self._category_filter)
            self._category_filter.deleteLater()
            self._category_filter = None
        elif new_val:
            self._category_filter = LsaSelectorCategoryFilterButton(self)
            self._category_filter.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            self._category_filter.setPopupMode(QToolButton.InstantPopup)
            self._category_filter.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            self._main_layout.insertWidget(self._main_layout.count(), self._category_filter)
            self._update_category_filter()

    showCategoryFilter = Property(bool, fget=_get_show_category_filter, fset=_set_show_category_filter)
    """
    Flag to show the dropdown menu that filters the displayed contexts by category.

    :type: bool
    """

    def select_user(self, user: str):
        """
        Select the context corresponding to the given user.

        If more than one context corresponds to the given user, the one higher up in the table will be selected.
        If such user does not exist in the list (either because there is not such user in retrieved data, or because
        it was filtered out using name or category filter) the selection will not happen.

        This is useful when you already have a control system layer working on a certain user, and you want to
        reflect that in the widget transparently for the user, without requiring interaction.

        Args:
            user: Timing user corresponding to the context to be selected, e.g. ``LEI.USER.LIN3MEAS``.
        """
        model = self._table.model()
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            ctx = index.data(CONTEXT_TABLE_ROLE)
            if not isinstance(ctx, AbstractLsaSelectorResidentContext):
                continue
            if ctx.user == user:
                self._table.selectionModel().setCurrentIndex(index, (QItemSelectionModel.ClearAndSelect
                                                                     | QItemSelectionModel.Current
                                                                     | QItemSelectionModel.Rows))
                break

    @property
    def selected_context(self) -> Optional[AbstractLsaSelectorContext]:
        """
        Read-only property to find out currently displayed context. If no selection is visible, :obj:`None`
        is returned.
        """
        index = self._table.selectionModel().currentIndex()
        return self._table.model().data(index, CONTEXT_TABLE_ROLE)

    def _get_color_user(self) -> QColor:
        return self.model.color(LsaSelectorColorRole.FG_USER)

    def _set_color_user(self, new_val: Color):
        self.model.set_color(role=LsaSelectorColorRole.FG_USER, color=new_val)

    userColor: Color = Property(QColor, fget=_get_color_user, fset=_set_color_user)
    """Foreground color of the "TGM User" column. This property enables ability to restyle the widget with QSS."""

    def _get_color_resident(self) -> QColor:
        return self.model.color(LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL)

    def _set_color_resident(self, new_val: Color):
        self.model.set_color(role=LsaSelectorColorRole.FG_CTX_RESIDENT_NORMAL, color=new_val)

    residentColor: Color = Property(QColor, fget=_get_color_resident, fset=_set_color_resident)
    """
    Foreground color of the inactive resident cycles. This property enables ability to restyle the widget with QSS.
    """

    def _get_color_active(self) -> QColor:
        return self.model.color(LsaSelectorColorRole.FG_CTX_RESIDENT_ACTIVE)

    def _set_color_active(self, new_val: Color):
        self.model.set_color(role=LsaSelectorColorRole.FG_CTX_RESIDENT_ACTIVE, color=new_val)

    activeColor: Color = Property(QColor, fget=_get_color_active, fset=_set_color_active)
    """
    Foreground color of the active resident cycles mapped to a normal timing user. This property enables ability to
    restyle the widget with QSS.
    """

    def _get_color_non_resident(self) -> QColor:
        return self.model.color(LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NORMAL)

    def _set_color_non_resident(self, new_val: Color):
        self.model.set_color(role=LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NORMAL, color=new_val)

    nonResidentColor: Color = Property(QColor, fget=_get_color_non_resident, fset=_set_color_non_resident)
    """
    Foreground color of the multiplexed non-resident cycles. This property enables ability to restyle the widget
    with QSS.
    """

    def _get_color_resident_non_ppm(self) -> QColor:
        return self.model.color(LsaSelectorColorRole.FG_CTX_RESIDENT_NON_PPM)

    def _set_color_resident_non_ppm(self, new_val: Color):
        self.model.set_color(role=LsaSelectorColorRole.FG_CTX_RESIDENT_NON_PPM, color=new_val)

    residentNonMultiplexedColor: Color = Property(QColor, fget=_get_color_resident_non_ppm, fset=_set_color_resident_non_ppm)
    """
    Foreground color of the non-multiplexed resident cycles. This property enables ability to restyle the widget
    with QSS.
    """

    def _get_color_spare(self) -> QColor:
        return self.model.color(LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE)

    def _set_color_spare(self, new_val: Color):
        self.model.set_color(role=LsaSelectorColorRole.FG_CTX_RESIDENT_SPARE, color=new_val)

    spareColor: Color = Property(QColor, fget=_get_color_spare, fset=_set_color_spare)
    """
    Foreground color of the active resident cycles mapped to a spare timing user. This property enables ability to
    restyle the widget with QSS.
    """

    def _get_color_non_resident_non_ppm(self) -> QColor:
        return self.model.color(LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM)

    def _set_color_non_resident_non_ppm(self, new_val: Color):
        self.model.set_color(role=LsaSelectorColorRole.FG_CTX_NON_RESIDENT_NON_PPM, color=new_val)

    nonResidentNonMultiplexedColor: Color = Property(QColor, fget=_get_color_non_resident_non_ppm, fset=_set_color_non_resident_non_ppm)
    """
    Foreground color of the non-multiplexed non-resident cycles. This property enables ability to restyle the widget
    with QSS.
    """

    def _get_color_resident_bkg(self) -> QColor:
        return self.model.color(LsaSelectorColorRole.BG_CTX_RESIDENT)

    def _set_color_resident_bkg(self, new_val: Color):
        self.model.set_color(role=LsaSelectorColorRole.BG_CTX_RESIDENT, color=new_val)

    residentBackgroundColor: Color = Property(QColor, fget=_get_color_resident_bkg, fset=_set_color_resident_bkg)
    """
    Background color of the resident cycles. Same color is applied as a background for the table. This property
    enables ability to restyle the widget with QSS.
    """

    def _get_color_non_resident_bkg(self) -> QColor:
        return self.model.color(LsaSelectorColorRole.BG_CTX_NON_RESIDENT)

    def _set_color_non_resident_bkg(self, new_val: Color):
        self.model.set_color(role=LsaSelectorColorRole.BG_CTX_NON_RESIDENT, color=new_val)

    nonResidentBackgroundColor: Color = Property(QColor, fget=_get_color_non_resident_bkg, fset=_set_color_non_resident_bkg)
    """Background color of the non-resident cycles. This property enables ability to restyle the widget with QSS."""

    def _get_color_can_become_resident_bkg(self) -> QColor:
        return self.model.color(LsaSelectorColorRole.BG_CTX_CAN_BE_RESIDENT)

    def _set_color_can_become_resident_bkg(self, new_val: Color):
        self.model.set_color(role=LsaSelectorColorRole.BG_CTX_CAN_BE_RESIDENT, color=new_val)

    canBecomeResidentBackgroundColor: Color = Property(QColor, fget=_get_color_can_become_resident_bkg, fset=_set_color_can_become_resident_bkg)
    """
    Background color of the non-resident cycles that can become resident (see
    :attr:`LsaSelectorNonResidentContext.can_become_resident`). This property enables ability to restyle the widget
    with QSS.
    """

    def _get_color_selection(self) -> QColor:
        return self._color_selection

    def _set_color_selection(self, new_val: Color):
        if not isinstance(new_val, QColor):
            new_val = QColor(new_val)
        if new_val == self._color_selection:
            return
        self._color_selection = new_val
        self._update_table_colors()

    selectionBackgroundColor: Color = Property(QColor, fget=_get_color_selection, fset=_set_color_selection)
    """Background color of the selected row. This property enables ability to restyle the widget with QSS."""

    def _get_color_selection_text(self) -> QColor:
        return self._color_selection_text

    def _set_color_selection_text(self, new_val: Color):
        if not isinstance(new_val, QColor):
            new_val = QColor(new_val)
        if new_val == self._color_selection_text:
            return
        self._color_selection_text = new_val
        self._update_table_colors()

    selectionColor: Color = Property(QColor, fget=_get_color_selection_text, fset=_set_color_selection_text)
    """Foreground color of the selected row. This property enables ability to restyle the widget with QSS."""

    def _get_resident_font(self) -> QFont:
        return self.model.resident_font

    def _set_resident_font(self, new_val: QFont):
        self.model.resident_font = new_val

    residentFont: QFont = Property(QFont, fget=_get_resident_font, fset=_set_resident_font)
    """Font used to display resident cycles. This property enables ability to restyle the widget with QSS."""

    def _get_non_resident_font(self) -> QFont:
        return self.model.non_resident_font

    def _set_non_resident_font(self, new_val: QFont):
        self.model.non_resident_font = new_val

    nonResidentFont: QFont = Property(QFont, fget=_get_non_resident_font, fset=_set_non_resident_font)
    """Font used to display non-resident cycles. This property enables ability to restyle the widget with QSS."""

    def _connect_model(self, model: LsaSelectorModel):
        model.setParent(self)
        model.connect_table(table=self._table)
        self._update_table_colors()
        self._update_category_filter()
        model.title_filter_changed.connect(self._update_name_filter)
        model.category_filter_changed.connect(self._update_category_filter)
        model.background_color_changed.connect(self._update_table_colors)
        model.lsa_error_received.connect(self._on_lsa_error)
        self._table.selectionModel().selectionChanged.connect(self._on_table_selection)
        self._table.model().dataChanged.connect(self._update_category_filter)
        self._table.model().modelReset.connect(self._update_category_filter)
        if self._name_filter:
            self._name_filter.setText(model.filter_title)
        if model.last_error:
            self._on_lsa_error(model.last_error)

    def _disconnect_model(self, model: LsaSelectorModel):
        self._table.model().modelReset.disconnect(self._update_category_filter)
        self._table.model().dataChanged.disconnect(self._update_category_filter)
        self._table.selectionModel().selectionChanged.disconnect(self._on_table_selection)
        self._table.setModel(None)
        model.lsa_error_received.disconnect(self._on_lsa_error)
        model.background_color_changed.disconnect(self._update_table_colors)
        model.category_filter_changed.disconnect(self._update_category_filter)
        model.title_filter_changed.disconnect(self._update_name_filter)
        model.setParent(None)
        model.deleteLater()

    def _update_table_colors(self):
        # Styling must be done with style sheets and not QPalette, to stay compatible with external QSS stylesheets,
        # as explained here: https://doc.qt.io/qt-5/qwidget.html#palette-prop
        if self._table.testAttribute(Qt.WA_StyleSheet):
            self._table.setStyleSheet("QTableView{"
                                      "  border-width: 1px;"  # Compensate for border style being reset by stylesheet
                                      "  border-style: inset;"
                                      f"  background-color: {self.residentBackgroundColor.name()};"
                                      f"  selection-color: {self.selectionColor.name()};"
                                      f"  selection-background-color: {self.selectionBackgroundColor.name()};"
                                      "}")
        else:
            palette = self._table.palette()
            palette.setColor(QPalette.Base, self.residentBackgroundColor)
            palette.setColor(QPalette.Highlight, self.selectionBackgroundColor)
            palette.setColor(QPalette.HighlightedText, self.selectionColor)
            self._table.setPalette(palette)

    def _update_category_filter(self):
        self._update_category_filter_title()

        if not self._category_filter:
            return
        menu = QMenu()
        for cat in sorted(self.model.find_stored_categories(), key=operator.attrgetter("name")):
            act = menu.addAction(cat.name, self._on_category_filter_toggled)
            act.setCheckable(True)
            act.setData(cat)
            act.setChecked(not self.model.filter_categories or (cat in self.model.filter_categories))
        self._category_filter.setMenu(menu)

    def _update_category_filter_title(self):
        if not self._category_filter:
            return
        categories = self.model.filter_categories or set(AbstractLsaSelectorContext.Category)
        categories &= self.model.find_stored_categories()
        self._category_filter.setText("Showing: " + ", ".join((flag.name for flag in sorted(categories, key=operator.attrgetter("name")))))

    def _on_table_selection(self, selected: QItemSelection, _: QItemSelection):
        try:
            index = selected.indexes()[0]
        except IndexError:
            # Selection indexes are empty. We are not interested to fire signals on deselection. We want to send only
            # when a new row is selected, since the intention is only to fire signals on user interaction.
            return

        ctx = self._table.model().data(index, CONTEXT_TABLE_ROLE)
        if not ctx:
            return
        self.contextSelectionChanged.emit(ctx)
        if isinstance(ctx, AbstractLsaSelectorResidentContext):
            # Emit notification only for resident contexts that have a user, otherwise
            # it won't be possible to plug into pyjapc, and this signal will be harmful.
            # If people want to be notified for all contexts, they should listen on contextSelectionChanged
            self.userSelectionChanged.emit(ctx.user)

    def _on_lsa_error(self, error: str):
        self._error_label.setText("<b>LSA problem occurred</b>:<br/>" + error)
        self._stack.setCurrentIndex(1)

    def _on_name_filter_typed(self, filter: str):
        blocker = QSignalBlocker(self.model)
        self.model.filter_title = filter
        blocker.unblock()

    def _update_name_filter(self):
        if self._name_filter:
            self._name_filter.setText(self.model.filter_title)

    def _on_category_filter_toggled(self):
        if not isinstance(self.sender(), QAction):
            return
        action = cast(QAction, self.sender())
        category = AbstractLsaSelectorContext.Category(action.data())
        filter_categories = self.model.filter_categories
        if action.isChecked():
            filter_categories.add(category)
        else:
            if not filter_categories:
                filter_categories = self.model.find_stored_categories()
            try:
                filter_categories.remove(category)
            except KeyError:
                # Assuming model has changed and was not synchronized with menu properly. Silently ignoring error.
                return
        blocker = QSignalBlocker(self.model)
        self.model.filter_categories = filter_categories
        blocker.unblock()
        self._update_category_filter_title()

    @property
    def _error_label(self) -> QLabel:
        if self.__error_label is None:
            label = QLabel()
            label.setWordWrap(True)
            label.setContentsMargins(10, 15, 10, 10)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.__error_label = label

            error_widget = QWidget()
            error_widget.setAutoFillBackground(True)
            palette = error_widget.palette()
            color = palette.color(QPalette.Window)
            color.setAlphaF(0.95)
            palette.setColor(QPalette.Window, color)
            error_widget.setPalette(palette)
            layout = QVBoxLayout()
            layout.addWidget(label)
            layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Preferred, QSizePolicy.Expanding))
            error_widget.setLayout(layout)

            self._stack.addWidget(error_widget)
        return self.__error_label


class LsaSelectorCategoryFilterButton(QToolButton):

    def __init__(self, parent: Optional[QWidget] = None):
        """
        This class is wrapping logic to react to the style change.
        This approach is chosen over eventFilter in the parent widget, because eventFilter causes a crash when
        closing widget preview in Qt Designer.
        """
        super().__init__(parent)
        self._update_icon()

    def event(self, event: QEvent) -> bool:
        """
        This event handler is reimplemented to react to the external style change, e.g. via QSS, to adjust
        colors painted in the line edit.

        This is the main event handler; it handles event ``event``. You can reimplement this function in a
        subclass, but we recommend using one of the specialized event handlers instead.

        Args:
            event: Handled event.

        Returns:
            :obj:`True` if the event was recognized, otherwise it returns :obj:`False`. If the recognized event
            was accepted (see :meth:`QEvent.accepted`), any further processing such as event propagation to the
            parent widget stops.
        """
        res = super().event(event)
        if event.type() == QEvent.StyleChange:
            # Update this at the end of the event loop, when palette has been synchronized with the updated style
            QTimer.singleShot(0, self._update_icon)
        return res

    def _update_icon(self):
        self.setIcon(qta.icon("mdi.format-list-bulleted-type", color=self.palette().color(QPalette.Text)))


class LeftClickTableView(QTableView):

    def mousePressEvent(self, event: QMouseEvent):
        # Suppress right-click, middle-click and all others except left click
        if event.button() & Qt.LeftButton:
            super().mousePressEvent(event)
