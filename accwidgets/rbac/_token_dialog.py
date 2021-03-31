import json
import operator
from typing import Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
from qtpy import uic
from qtpy.QtGui import QColor, QPalette
from qtpy.QtWidgets import QDialog, QDialogButtonBox, QWidget, QFormLayout, QLabel
from ._token import RbaToken


class RbaTokenDialog(QDialog):

    def __init__(self, token: RbaToken, parent: Optional[QWidget] = None):
        """
        Dialog to select user roles.

        Args:
            token: Token that contains the information.
            parent: Parent widget to own this object.
        """
        super().__init__(parent)

        # For IDE support, assign types to dynamically created items from the *.ui file
        self.btn_box: QDialogButtonBox = None
        self.form: QFormLayout = None

        uic.loadUi(Path(__file__).parent / "token_dialog.ui", self)

        self.btn_box.rejected.connect(self.close)

        form = self.form

        def add_form_row(title: str, content: Union[str, QLabel]):
            lbl_title = QLabel(title)
            font = lbl_title.font()
            font.setBold(True)
            lbl_title.setFont(font)
            if isinstance(content, str):
                content = QLabel(content)
            form.addRow(lbl_title, content)

        add_form_row("User Name", f"{token.username} [{token.user_full_name}, "
                                  f"{token.user_email}]")
        add_form_row("Account Type", token.account_type)
        valid_lbl = QLabel(json.dumps(token.valid))
        valid_lbl.setAutoFillBackground(True)
        # QPalette approach (default behavior)
        palette = valid_lbl.palette()
        palette.setColor(QPalette.Window, _QPALETTE_POSITIVE if token.valid else _QPALETTE_CRITICAL)
        valid_lbl.setPalette(palette)
        # Dynamic property approach (when used with QSS, will override QPalette)
        valid_lbl.setProperty("qss-role", "bg-positive" if token.valid else "bg-critical")
        add_form_row("Is Valid ?", valid_lbl)
        add_form_row("Start Time", _create_date_label(token.auth_timestamp))
        add_form_row("Expiration Time", _create_date_label(token.expiration_timestamp, highlight_past_due=True))
        add_form_row("Renewed automatically ?", json.dumps(token.auto_renewable))

        roles = [f"{role.name} [critical={json.dumps(role.is_critical)}; lifetime={role.lifetime}]"
                 for role in sorted(filter(operator.attrgetter("active"), token.roles), key=operator.attrgetter("name"))]
        add_form_row("Roles", "\n".join(roles))

        add_form_row("Application", token.app_name)
        add_form_row("Location", f"{token.location.name} ["
                                 f"address={token.location.address!s}; "
                                 f"auth-reqd={json.dumps(token.location.auth_required)}]")
        add_form_row("Serial ID", token.serial_id)


_QPALETTE_POSITIVE = QColor("#66ff66")
_QPALETTE_CRITICAL = QColor("#ff5050")


def _create_date_label(date: datetime, highlight_past_due: bool = False) -> QLabel:
    dt = date - datetime.now()
    lbl = QLabel(f'{date.isoformat(sep=" ")} (About {_format_timedelta(dt)})')
    if highlight_past_due and dt < timedelta(0):
        # QPalette approach (default behavior)
        palette = lbl.palette()
        palette.setColor(QPalette.WindowText, _QPALETTE_CRITICAL)
        lbl.setPalette(palette)
        # Dynamic property approach (when used with QSS, will override QPalette)
        lbl.setProperty("qss-role", "critical")
    return lbl


def _format_timedelta(td: timedelta) -> str:

    if td == timedelta(0):
        return "now"

    def multiple(word: str, amount: int) -> str:
        return word + ("" if amount == 1 else "s")

    res = []
    abs_td = abs(td)
    if abs_td.days > 0:
        res.append(f'{abs_td.days} {multiple("day", abs_td.days)}')
    hours, remainder = divmod(abs_td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        res.append(f'{hours} {multiple("hour", hours)}')
    if minutes > 0:
        res.append(f"{minutes} min.")
    if seconds > 0:
        res.append(f"{seconds} sec.")
    if abs_td.days == 0 and hours == 0 and minutes == 0 and seconds == 0:
        # The td == timedelta(0) on the top is not reliably (probably because of subsecond precision)
        return "now"
    if td > timedelta(0):
        res.append("from now")
    else:
        res.append("ago")
    return " ".join(res)
