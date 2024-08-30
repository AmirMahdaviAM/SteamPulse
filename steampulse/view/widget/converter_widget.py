import logging

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget

from qfluentwidgets import (
    FluentIcon,
    IconWidget,
    setCustomStyleSheet,
)

from ..ui.converter_ui import ConverterUi
from ...common.config import cfg
from ...common.info import CURRENCY_KEY_PRICE, currency
from ...common.tool import SteamPulseIcon, signal_bus


logger = logging.getLogger("SteamPulse")


class ConverterWidget(QWidget, ConverterUi):

    def __init__(self, infobar_pos):
        super().__init__()

        self.INFOBAR_POS = infobar_pos

        self.setupUi(self)
        self.init_ui()
        self.calculate()
        self.key_updated(False)

        signal_bus.region_change.connect(lambda: QTimer.singleShot(1, self.calculate))
        signal_bus.key_updated.connect(self.key_updated)

    def init_ui(self):

        self.converter_lyt.setAlignment(Qt.AlignCenter)

        self.convert_icon.setIcon(FluentIcon.UPDATE)
        self.convert_icon.setFixedSize(20, 20)

        self.key_icon.setIcon(":/vector/key.svg")
        self.key_icon.setFixedSize(34, 34)

        self.key_spnbx.textChanged.connect(self.calculate)
        self.key_spnbx.clearFocus()

        self.target_cmb.currentIndexChanged.connect(self.calculate)
        self.target_cmb.addItems([self.tr("Current"), "Tooman"])

        self.irt_icon.setIcon(SteamPulseIcon.KEY_IRT)
        self.irt_icon.setFixedSize(23, 23)

        style = "LineEdit, ComboBox {border-radius: 16px}"
        widgets = [
            self.target_cmb,
            self.key_spnbx,
        ]
        for widget in widgets:
            setCustomStyleSheet(widget, style, style)

    def calculate(self):

        if self.key_spnbx.text():
            locale = currency(cfg.region.value)

            source = self.target_cmb.currentText()

            if source.startswith("Current"):
                self.irt_icon.hide()

                source = locale["name"]
                price = float(f"{CURRENCY_KEY_PRICE[source] * int(self.key_spnbx.text()):.2f}")

                if not locale["float"]:
                    price = int(price)

                if locale["symbol_pos"] == "prefix":
                    price = f"{locale['symbol']} {price:,}"
                elif "suffix":
                    price = f"{price:,} {locale['symbol']}"

            else:
                self.irt_icon.show()

                source = "Tooman"
                price = f"{int(CURRENCY_KEY_PRICE[source] * int(self.key_spnbx.text())):,}"

            self.target_lbl.setText(price)

    def key_updated(self, updated):

        if updated:
            self.key_spnbx.setEnabled(True)
            self.target_cmb.setEnabled(True)
            self.calculate()

        else:
            self.key_spnbx.setDisabled(True)
            self.target_cmb.setDisabled(True)
