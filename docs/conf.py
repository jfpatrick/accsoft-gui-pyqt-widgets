# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
# In our case we have to point Sphinx to the accwidgets package
# which is located two directories upwards.

import sphinx.ext.autodoc
from typing import List
from datetime import datetime
from sys import version_info as py_version
from qtpy.QtCore import qVersion, PYQT_VERSION_STR
import pyjapc
import accwidgets
from accwidgets._api import REAL_MODULE_NAME_VAR

# -- Project information -----------------------------------------------------

project = "accwidgets"
copyright = f"{datetime.now().year}, BE-CO, CERN"
author = "Ivan Sinkarenko, Fabian Sorn"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.autosectionlabel",  # To allow cross-referencing sections between documents
    "sphinx.ext.intersphinx",  # To connect external docs, e.g. PyQt5
    "sphinx.ext.napoleon",  # Support for Google-style docstrings. This needs to be before typehints
    "sphinx_autodoc_typehints",
    "sphinx.ext.inheritance_diagram",  # Draw inheritance diagrams
    "sphinx.ext.graphviz",  # Needed to draw diagrams produced by plugin above (and also by hand)
    "sphinx.ext.todo",
    "acc_py_sphinx.theme",  # Enable "acc_py" HTML theme
    "acc_py_sphinx.utils.exclude",  # Exclude members per-class
    "acc_py_sphinx.utils.autocontent",  # Smarter merge of __init__ and class docstring
    "acc_py_sphinx.utils.attrdoc",  # Fix propagation of attribute docstrings
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to sphinx_doc directory, that match files and
# directories to ignore when looking for sphinx_doc files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns: List[str] = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "acc_py"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_short_title = f"{project} v{accwidgets.__version__}"
html_title = f"{html_short_title} wiki"

html_favicon = html_logo = "./img/logo.png"  # Must be png here, as ico won't be rendered by Chrome (and is not advised by MDN)

html_css_files = [
    "collapsible.css",
]

html_js_files = [
    "collapsible.js",
]

# Both the class’ and the __init__ method’s docstring are concatenated and inserted.
autoclass_content = "init"
custom_autoclass_content = True
# This value controls the docstrings inheritance. If set to True the docstring for classes or methods,
# if not explicitly set, is inherited form parents.
autodoc_inherit_docstrings = True
# The default options for autodoc directives. They are applied to all autodoc directives automatically.

autodoc_default_options = {
    "show-inheritance": True,
    "member-order": "bysource",
    "exclude-members": "__init__,"
                       "__str__,"
                       "__sizeof__,"
                       "__setattr__,"
                       "__repr__,"
                       "__reduce_ex__,"
                       "__reduce__,"
                       "__new__,"
                       "__ne__,"
                       "__lt__,"
                       "__le__,"
                       "__init_subclass__,"
                       "__hash__,"
                       "__gt__,"
                       "__getattribute__,"
                       "__getattr__,"
                       "__ge__,"
                       "__format__,"
                       "__eq__,"
                       "__dir__,"
                       "__delattr__,"
                       "AllDockWidgetFeatures,"
                       "DockWidgetClosable,"
                       "DockWidgetFeature,"
                       "DockWidgetFeatures,"
                       "DockWidgetFloatable,"
                       "DockWidgetMovable,"
                       "DockWidgetVerticalTitleBar,"
                       "AllowNestedDocks,"
                       "AllowTabbedDocks,"
                       "AnimatedDocks,"
                       "DrawChildren,"
                       "DrawWindowBackground,"
                       "ForceTabbedDocks,"
                       "GroupedDragging,"
                       "IgnoreMask,"
                       "LeadingPosition,"
                       "NoDockWidgetFeatures,"
                       "NoEcho,"
                       "PaintDeviceMetric,"
                       "PasswordEchoOnEdit,"
                       "PdmDepth,"
                       "PdmDevicePixelRatio,"
                       "PdmDevicePixelRatioScaled,"
                       "PdmDpiX,"
                       "PdmDpiY,"
                       "PdmHeight,"
                       "PdmHeightMM,"
                       "PdmNumColors,"
                       "PdmPhysicalDpiX,"
                       "PdmPhysicalDpiY,"
                       "PdmWidth,"
                       "PdmWidthMM,"
                       "RenderFlag,"
                       "RenderFlags,"
                       "Shadow,"
                       "Shape,"
                       "StyleMask,"
                       "TrailingPosition,"
                       "__weakref__,"
                       "__subclasshook__,"
                       "acceptDrops,"
                       "accessibleDescription,"
                       "accessibleName,"
                       "actionEvent,"
                       "actions,"
                       "activateWindow,"
                       "addAction,"
                       "addActions,"
                       "adjustSize,"
                       "alarmSeverityChanged,"
                       "alarm_severity_changed,"
                       "alignment,"
                       "animateClick,"
                       "autoDefault,"
                       "autoExclusive,"
                       "autoFillBackground,"
                       "autoRepeat,"
                       "autoRepeatDelay,"
                       "autoRepeatInterval,"
                       "allowedAreasChanged,"
                       "baseSize,"
                       "backgroundRole,"
                       "blockSignals,"
                       "buddy,"
                       "changeEvent,"
                       "checkStateSet,"
                       "childAt,"
                       "childEvent,"
                       "children,"
                       "childrenRect,"
                       "childrenRegion,"
                       "clearFocus,"
                       "clearMask,"
                       "close,"
                       "closeEvent,"
                       "colorCount,"
                       "connectNotify,"
                       "contentsMargins,"
                       "contentsRect,"
                       "contextMenuEvent,"
                       "contextMenuPolicy,"
                       "createWindowContainer,"
                       "ctrl_limit_changed,"
                       "cursor,"
                       "customContextMenuRequested,"
                       "customEvent,"
                       "deleteLater,"
                       "depth,"
                       "destroy,"
                       "destroyed,"
                       "devType,"
                       "devicePixelRatio,"
                       "devicePixelRatioF,"
                       "devicePixelRatioFScale,"
                       "disconnectNotify,"
                       "dockLocationChanged,"
                       "dragEnterEvent,"
                       "dragLeaveEvent,"
                       "dragMoveEvent,"
                       "drawFrame,"
                       "dropEvent,"
                       "dumpObjectTree,"
                       "dumpObjectInfo,"
                       "dynamicPropertyNames,"
                       "effectiveWinId,"
                       "ensurePolished,"
                       "enterEvent,"
                       "event,"
                       "eventFilter,"
                       "featuresChanged,"
                       "find,"
                       "findChild,"
                       "findChildren,"
                       "focusInEvent,"
                       "focusNextChild,"
                       "focusNextPrevChild,"
                       "focusOutEvent,"
                       "focusPolicy,"
                       "focusPreviousChild,"
                       "focusProxy,"
                       "focusWidget,"
                       "font,"
                       "fontInfo,"
                       "fontMetrics,"
                       "foregroundRole,"
                       "frameGeometry,"
                       "frameRect,"
                       "frameShadow,"
                       "frameShape,"
                       "frameSize,"
                       "frameStyle,"
                       "frameWidth,"
                       "geometry,"
                       "getContentsMargins,"
                       "grab,"
                       "grabGesture,"
                       "grabKeyboard,"
                       "grabMouse,"
                       "grabShortcut,"
                       "graphicsEffect,"
                       "graphicsProxyWidget,"
                       "hasFocus,"
                       "hasHeightForWidth,"
                       "hasMouseTracking,"
                       "hasScaledContents,"
                       "hasSelectedText,"
                       "hasTabletTracking,"
                       "height,"
                       "heightForWidth,"
                       "heightMM,"
                       "hide,"
                       "hideEvent,"
                       "indent,"
                       "inherits,"
                       "initPainter,"
                       "initStyleOption,"
                       "inputMethodEvent,"
                       "inputMethodHints,"
                       "inputMethodQuery,"
                       "inputRejected,"
                       "insertAction,"
                       "insertActions,"
                       "insertToolBarBreak,"
                       "installEventFilter,"
                       "isActiveWindow,"
                       "isAncestorOf,"
                       "isEnabled,"
                       "isEnabledTo,"
                       "isDockNestingEnabled,"
                       "isFullScreen,"
                       "isHidden,"
                       "isLeftToRight,"
                       "isMaximized,"
                       "isMinimized,"
                       "isModal,"
                       "isRightToLeft,"
                       "isSignalConnected,"
                       "isVisible,"
                       "isVisibleTo,"
                       "isWidgetType,"
                       "isWindow,"
                       "isWindowModified,"
                       "isWindowType,"
                       "keyPressEvent,"
                       "keyReleaseEvent,"
                       "keyboardGrabber,"
                       "killTimer,"
                       "layout,"
                       "layoutDirection,"
                       "leaveEvent,"
                       "lineWidth,"
                       "linkActivated,"
                       "linkHovered,"
                       "locale,"
                       "logicalDpiX,"
                       "logicalDpiY,"
                       "lower,"
                       "lowerCtrlLimitChanged,"
                       "mapFrom,"
                       "mapFromGlobal,"
                       "mapFromParent,"
                       "mapTo,"
                       "mapToGlobal,"
                       "mapToParent,"
                       "margin,"
                       "mask,"
                       "maximumHeight,"
                       "maximumSize,"
                       "maximumWidth,"
                       "metaObject,"
                       "metric,"
                       "midLineWidth,"
                       "minimumHeight,"
                       "minimumSize,"
                       "minimumSizeHint,"
                       "minimumWidth,"
                       "mouseDoubleClickEvent,"
                       "mouseDragEvent,"
                       "mouseGrabber,"
                       "mouseMoveEvent,"
                       "mousePressEvent,"
                       "mouseReleaseEvent,"
                       "move,"
                       "moveEvent,"
                       "moveToThread,"
                       "movie,"
                       "nativeEvent,"
                       "nativeParentWidget,"
                       "nextInFocusChain,"
                       "normalGeometry,"
                       "objectName,"
                       "objectNameChanged,"
                       "openExternalLinks,"
                       "overrideWindowFlags,"
                       "overrideWindowState,"
                       "paintEngine,"
                       "paintEvent,"
                       "paintingActive,"
                       "palette,"
                       "parent,"
                       "parentWidget,"
                       "physicalDpiX,"
                       "physicalDpiY,"
                       "picture,"
                       "pixmap,"
                       "pos,"
                       "precisionChanged,"
                       "precision_changed,"
                       "previousInFocusChain,"
                       "property,"
                       "pyqtConfigure,"
                       "raise_,"
                       "receivers,"
                       "rect,"
                       "releaseKeyboard,"
                       "releaseMouse,"
                       "releaseShortcut,"
                       "removeAction,"
                       "removeEventFilter,"
                       "render,"
                       "repaint,"
                       "resize,"
                       "resizeEvent,"
                       "restoreGeometry,"
                       "saveGeometry,"
                       "scroll,"
                       "selectedText,"
                       "selectionStart,"
                       "sender,"
                       "senderSignalIndex,"
                       "setAcceptDrops,"
                       "setAccessibleDescription,"
                       "setAccessibleName,"
                       "setAlignment,"
                       "setAttribute,"
                       "setAutoFillBackground,"
                       "setBackgroundRole,"
                       "setBaseSize,"
                       "setBuddy,"
                       "setContentsMargins,"
                       "setContextMenuPolicy,"
                       "setCursor,"
                       "setDisabled,"
                       "setEnabled,"
                       "setFixedHeight,"
                       "setFixedSize,"
                       "setFixedWidth,"
                       "setFocus,"
                       "setFocusPolicy,"
                       "setFocusProxy,"
                       "setFont,"
                       "setForegroundRole,"
                       "setFrameRect,"
                       "setFrameShadow,"
                       "setFrameShape,"
                       "setFrameStyle,"
                       "setGeometry,"
                       "setGraphicsEffect,"
                       "setHidden,"
                       "setIndent,"
                       "setInputMethodHints,"
                       "setLayout,"
                       "setLayoutDirection,"
                       "setLineWidth,"
                       "setLocale,"
                       "setMargin,"
                       "setMask,"
                       "setMaximumHeight,"
                       "setMaximumSize,"
                       "setMaximumWidth,"
                       "setMidLineWidth,"
                       "setMinimumHeight,"
                       "setMinimumSize,"
                       "setMinimumWidth,"
                       "setMouseTracking,"
                       "setMovie,"
                       "setObjectName,"
                       "setOpenExternalLinks,"
                       "setPalette,"
                       "setParent,"
                       "setPicture,"
                       "setPixmap,"
                       "setProperty,"
                       "setScaledContents,"
                       "setSelection,"
                       "setShortcutAutoRepeat,"
                       "setShortcutEnabled,"
                       "setSizeIncrement,"
                       "setSizePolicy,"
                       "setStatusTip,"
                       "setStyle,"
                       "setStyleSheet,"
                       "setTabOrder,"
                       "setTabletTracking,"
                       "setText,"
                       "setTextFormat,"
                       "setTextInteractionFlags,"
                       "setToolTip,"
                       "setToolTipDuration,"
                       "setUpdatesEnabled,"
                       "setVisible,"
                       "setWhatsThis,"
                       "setWindowFilePath,"
                       "setWindowFlag,"
                       "setWindowFlags,"
                       "setWindowIcon,"
                       "setWindowIconText,"
                       "setWindowModality,"
                       "setWindowModified,"
                       "setWindowOpacity,"
                       "setWindowRole,"
                       "setWindowState,"
                       "setWindowTitle,"
                       "setWordWrap,"
                       "setX,"
                       "setY,"
                       "sharedPainter,"
                       "show,"
                       "showEvent,"
                       "showFullScreen,"
                       "showMaximized,"
                       "showMinimized,"
                       "showNormal,"
                       "signalsBlocked,"
                       "size,"
                       "sizeHint,"
                       "sizeIncrement,"
                       "sizePolicy,"
                       "stackUnder,"
                       "staticMetaObject,"
                       "startTimer,"
                       "statusTip,"
                       "style,"
                       "styleSheet,"
                       "tabletEvent,"
                       "testAttribute,"
                       "text,"
                       "textFormat,"
                       "textInteractionFlags,"
                       "thread,"
                       "timerEvent,"
                       "toolTip,"
                       "toolTipDuration,"
                       "tr,"
                       "underMouse,"
                       "ungrabGesture,"
                       "unitChanged,"
                       "unit_changed,"
                       "unsetCursor,"
                       "unsetLayoutDirection,"
                       "unsetLocale,"
                       "update,"
                       "updateGeometry,"
                       "updateMicroFocus,"
                       "updatesEnabled,"
                       "upperCtrlLimitChanged,"
                       "visibleRegion,"
                       "whatsThis,"
                       "wheelEvent,"
                       "width,"
                       "widthMM,"
                       "winId,"
                       "window,"
                       "windowFilePath,"
                       "windowFlags,"
                       "windowHandle,"
                       "windowIcon,"
                       "windowIconChanged,"
                       "windowIconText,"
                       "windowIconTextChanged,"
                       "windowModality,"
                       "windowOpacity,"
                       "windowRole,"
                       "windowState,"
                       "windowTitle,"
                       "windowTitleChanged,"
                       "windowType,"
                       "wordWrap,"
                       "x,"
                       "y,"
                       "ActionPosition,"
                       "EchoMode,"
                       "backspace,"
                       "completer,"
                       "copy,"
                       "createStandardContextMenu,"
                       "cursorBackward,"
                       "cursorForward,"
                       "cursorMoveStyle,"
                       "cursorPosition,"
                       "cursorPositionAt,"
                       "cursorPositionChanged,"
                       "cursorRect,"
                       "cursorWordBackward,"
                       "cursorWordForward,"
                       "cut,"
                       "del_,"
                       "deselect,"
                       "displayText,"
                       "dragEnabled,"
                       "echoMode,"
                       "editingFinished,"
                       "getTextMargins,"
                       "hasAcceptableInput,"
                       "hasFrame,"
                       "home,"
                       "inputMask,"
                       "isClearButtonEnabled,"
                       "isModified,"
                       "isReadOnly,"
                       "isRedoAvailable,"
                       "isUndoAvailable,"
                       "maxLength,"
                       "paste,"
                       "placeholderText,"
                       "returnPressed,"
                       "selectAll,"
                       "selectionChanged,"
                       "selectionEnd,"
                       "selectionLength,"
                       "setClearButtonEnabled,"
                       "setCompleter,"
                       "setCursorMoveStyle,"
                       "setCursorPosition,"
                       "setDragEnabled,"
                       "setEchoMode,"
                       "setFrame,"
                       "setInputMask,"
                       "setMaxLength,"
                       "setModified,"
                       "setPlaceholderText,"
                       "setReadOnly,"
                       "setTextMargins,"
                       "setValidator,"
                       "textChanged,"
                       "textEdited,"
                       "textMargins,"
                       "validator,"
                       "CacheMode,"
                       "ColorSpec,"
                       "DeviceCoordinateCache,"
                       "aboutQt,"
                       "aboutToQuit,"
                       "activeModalWidget,"
                       "activePopupWidget,"
                       "activeWindow,"
                       "addLibraryPath,"
                       "alert,"
                       "allWidgets,"
                       "allWindows,"
                       "GraphicsItemChange,"
                       "GraphicsItemFlag,"
                       "GraphicsItemFlags,"
                       "ItemAcceptsInputMethod,"
                       "ItemChildAddedChange,"
                       "ItemChildRemovedChange,"
                       "ItemClipsChildrenToShape,"
                       "ItemClipsToShape,"
                       "ItemContainsChildrenInShape,"
                       "ItemCoordinateCache,"
                       "ItemCursorChange,"
                       "ItemCursorHasChanged,"
                       "ItemDoesntPropagateOpacityToChildren,"
                       "ItemEnabledChange,"
                       "ItemEnabledHasChanged,"
                       "ItemFlagsChange,"
                       "ItemFlagsHaveChanged,"
                       "ItemHasNoContents,"
                       "ItemIgnoresParentOpacity,"
                       "ItemIgnoresTransformations,"
                       "ItemIsFocusable,"
                       "ItemIsMovable,"
                       "ItemIsPanel,"
                       "ItemIsSelectable,"
                       "ItemMatrixChange,"
                       "ItemNegativeZStacksBehindParent,"
                       "ItemOpacityChange,"
                       "ItemOpacityHasChanged,"
                       "ItemParentChange,"
                       "ItemParentHasChanged,"
                       "ItemPositionChange,"
                       "ItemPositionHasChanged,"
                       "ItemRotationChange,"
                       "ItemRotationHasChanged,"
                       "ItemScaleChange,"
                       "ItemScaleHasChanged,"
                       "ItemSceneChange,"
                       "ItemSceneHasChanged,"
                       "ItemScenePositionHasChanged,"
                       "ItemSelectedChange,"
                       "ItemSelectedHasChanged,"
                       "ItemSendsGeometryChanges,"
                       "ItemSendsScenePositionChanges,"
                       "ItemStacksBehindParent,"
                       "ItemToolTipChange,"
                       "ItemToolTipHasChanged,"
                       "ItemTransformChange,"
                       "ItemTransformHasChanged,"
                       "ItemTransformOriginPointChange,"
                       "ItemTransformOriginPointHasChanged,"
                       "ItemUsesExtendedStyleOption,"
                       "ItemVisibleChange,"
                       "ItemVisibleHasChanged,"
                       "ItemZValueChange,"
                       "ItemZValueHasChanged,"
                       "NoCache,"
                       "NonModal,"
                       "PanelModal,"
                       "PanelModality,"
                       "SceneModal,"
                       "acceptHoverEvents,"
                       "acceptTouchEvents,"
                       "acceptedMouseButtons,"
                       "allChildItems,"
                       "boundingRegionGranularity,"
                       "childrenBoundingRect,"
                       "childrenShape,"
                       "collidesWithItem,"
                       "collidesWithPath,"
                       "commonAncestorItem,"
                       "effectiveOpacity,"
                       "effectiveSizeHint,"
                       "filtersChildEvents,"
                       "forgetViewBox,"
                       "forgetViewWidget,"
                       "geometryChanged,"
                       "getContextMenus,"
                       "getWindowFrameMargins,"
                       "grabKeyboardEvent,"
                       "grabMouseEvent,"
                       "graphicsItem,"
                       "hoverEvent,"
                       "hoverEnterEvent,"
                       "hoverLeaveEvent,"
                       "hoverMoveEvent,"
                       "installSceneEventFilter,"
                       "isBlockedByModalPanel,"
                       "isObscuredBy,"
                       "mapFromItem,"
                       "mapFromScene,"
                       "mapFromView,"
                       "mapRectFromItem,"
                       "mapRectFromParent,"
                       "mapRectFromScene,"
                       "mapRectFromView,"
                       "mapRectToItem,"
                       "mapRectToParent,"
                       "mapRectToScene,"
                       "mapRectToView,"
                       "mapToItem,"
                       "mapToScene,"
                       "mapToView,"
                       "mouseClickEvent,"
                       "ownedByLayout,"
                       "paintWindowFrame,"
                       "panelModality,"
                       "parentLayoutItem,"
                       "polishEvent,"
                       "prepareGeometryChange,"
                       "removeSceneEventFilter,"
                       "sceneBoundingRect,"
                       "sceneEvent,"
                       "sceneEventFilter,"
                       "setAcceptHoverEvents,"
                       "setAcceptTouchEvents,"
                       "setAcceptedMouseButtons,"
                       "setBoundingRegionGranularity,"
                       "setCacheMode,"
                       "setFiltersChildEvents,"
                       "setGraphicsItem,"
                       "setOwnedByLayout,"
                       "setPanelModality,"
                       "setParentLayoutItem,"
                       "setTransformOriginPoint,"
                       "setWindowFrameMargins,"
                       "toGraphicsObject,"
                       "ungrabKeyboard,"
                       "ungrabKeyboardEvent,"
                       "ungrabMouse,"
                       "ungrabMouseEvent,"
                       "unsetWindowFrameMargins,"
                       "windowFrameEvent,"
                       "windowFrameGeometry,"
                       "windowFrameRect,"
                       "windowFrameSectionAt,"
                       "viewportEvent,"
                       "setDockNestingEnabled,"
                       "setTabShape,"
                       "setUnifiedTitleAndToolBarOnMac,"
                       "splitDockWidget,"
                       "tabShape,"
                       "tabifiedDockWidgetActivated,"
                       "tabifiedDockWidgets,"
                       "tabifyDockWidget,"
                       "unifiedTitleAndToolBarOnMac,",
}

# Scan all found documents for autosummary directives, and generate stub pages for each.
autosummary_generate = True
# Document classes and functions imported in modules
autosummary_imported_members = True
# if True, set typing.TYPE_CHECKING to True to enable “expensive” typing imports
set_type_checking_flag = True


qt_major = qVersion().split(".")[0]
pyqt_major = PYQT_VERSION_STR.split(".")[0]


intersphinx_mapping = {
    "python": (f"https://docs.python.org/{py_version.major}.{py_version.minor}", None),
    "Qt": (f"https://doc.qt.io/qt-{qt_major}/", "./qt.inv"),
    f"PyQt{pyqt_major}": (f"https://www.riverbankcomputing.com/static/Docs/PyQt{pyqt_major}/", "./pyqt.inv"),
    "numpy": ("http://docs.scipy.org/doc/numpy/", None),
    "pyqtgraph": ("http://www.pyqtgraph.org/documentation/", None),
    "comrad": ("https://acc-py.web.cern.ch/gitlab/acc-co/accsoft/gui/rad/accsoft-gui-rad-comrad/docs/stable/", None),
    "pyjapc": (f"https://acc-py.web.cern.ch/gitlab/scripting-tools/pyjapc/docs/v{pyjapc.__version__}/", None),
}


inheritance_graph_attrs = {
    "fontsize": 14,
    "size": '"60, 30"',
}


todo_include_todos = True


autosectionlabel_prefix_document = True


# Support for text colors, proposed here: https://stackoverflow.com/a/60991308
rst_epilog = """
.. include:: <s5defs.txt>
"""
html_css_files.append("s5defs-roles.css")


# This is a workaround to make Sphinx compatible with the modules that have been replaced for the "public API"
# paradigm.

def get_real_modname(self):
    return (self.get_attr(self.object, REAL_MODULE_NAME_VAR, None)
            or self.get_attr(self.object, "__module__", None)
            or self.modname)


sphinx.ext.autodoc.Documenter.get_real_modname = get_real_modname
