from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from qfluentwidgets import ScrollArea

from ..widget.banner_widget import BannerWidget
from ..widget.game_widget import GameWidget
from ..widget.converter_widget import ConverterWidget
from ...common.tool import signal_bus


class GameInterface(ScrollArea):

    def __init__(self):
        super().__init__()

        self.setObjectName("game_interface")

        self.setStyleSheet("border: none; background: transparent;")

        self.main_wgt = QWidget(self)

        self.main_lyt = QVBoxLayout(self.main_wgt)
        self.main_lyt.setContentsMargins(0, 0, 0, 0)
        self.main_lyt.setSpacing(10)
        self.main_lyt.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.banner_widget = BannerWidget(self)
        self.game_widget = GameWidget(self)
        self.converter_widget = ConverterWidget(self)

        self.main_lyt.addWidget(self.banner_widget)
        self.main_lyt.addWidget(self.game_widget)
        self.main_lyt.addWidget(self.converter_widget)

        self.setViewportMargins(36, 36, 36, 36)
        self.setWidget(self.main_wgt)
        self.setWidgetResizable(True)

        signal_bus.window_width.connect(self.edge_spacer)

    def edge_spacer(self, width):

        spacer_width = int((width - 1082) / 2)
        self.setViewportMargins(spacer_width, 36, spacer_width, 36)
