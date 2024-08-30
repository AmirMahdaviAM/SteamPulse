import os
from sys import platform
from enum import Enum
from subprocess import Popen

from PyQt5.QtCore import Qt, QObject, pyqtSignal


from qfluentwidgets import (
    InfoBarPosition,
    FluentIconBase,
    PushButton,
    InfoBar,
    Theme,
    getIconColor,
)


class SteamPulseIcon(FluentIconBase, Enum):

    LOGO = "logo"

    STEAM = "steam"
    STEAMDB = "steamdb"
    PCGW = "pcgw"
    KEY_IRT = "key_irt"

    NOTFOUND = "notfound"

    def path(self, theme=Theme.AUTO):
        return f":/vector/{self.value}_{getIconColor(theme)}.svg"


class SteamPulseSignalBus(QObject):

    window_width = pyqtSignal(int)
    mica_enabled = pyqtSignal(bool)
    shimmer_color = pyqtSignal(bool)
    switch_interface = pyqtSignal(str)

    game_database = pyqtSignal(bool)
    search_mode = pyqtSignal(str)
    search_emit = pyqtSignal(str)
    region_change = pyqtSignal()
    key_updated = pyqtSignal(bool)


signal_bus = SteamPulseSignalBus()


def steampulse_infobar(parent, type: str, msg: str, open: str = ""):

    match type:

        case "success":
            InfoBar.success(
                title=parent.tr("Success"),
                content=msg,
                orient=Qt.Horizontal,
                isClosable=True,
                duration=1500,
                position=InfoBarPosition.TOP_RIGHT,
                parent=parent,
            )

        case "success_btn":
            success = InfoBar.success(
                title=parent.tr("Success"),
                content=msg,
                orient=Qt.Vertical,
                isClosable=True,
                duration=1500,
                position=InfoBarPosition.TOP_RIGHT,
                parent=parent,
            )
            if platform == "win32":
                button = PushButton("Open Folder")
                button.clicked.connect(lambda: Popen(f"explorer.exe {open}"))
                success.addWidget(button)

        case "error":
            InfoBar.error(
                title=parent.tr("Error"),
                content=msg,
                orient=Qt.Horizontal,
                isClosable=True,
                duration=1500,
                position=InfoBarPosition.TOP_RIGHT,
                parent=parent,
            )

        case "error_btn":
            error = InfoBar.error(
                title=parent.tr("Error"),
                content=msg,
                orient=Qt.Vertical,
                isClosable=True,
                duration=1500,
                position=InfoBarPosition.TOP_RIGHT,
                parent=parent,
            )
            if platform == "win32":
                button = PushButton("Open Log")
                button.clicked.connect(lambda: Popen(f"explorer.exe {open}"))
                error.addWidget(button)

        case "warn":
            InfoBar.warning(
                title=parent.tr("Warning"),
                content=msg,
                orient=Qt.Horizontal,
                isClosable=True,
                duration=1500,
                position=InfoBarPosition.TOP_RIGHT,
                parent=parent,
            )

        case "warn_btn":
            warn = InfoBar.warning(
                title=parent.tr("Warning"),
                content=msg,
                orient=Qt.Vertical,
                isClosable=True,
                duration=1500,
                position=InfoBarPosition.TOP_RIGHT,
                parent=parent,
            )
            if platform == "win32":
                button = PushButton("Open Folder")
                button.clicked.connect(lambda: Popen(f"explorer.exe {open}"))
                warn.addWidget(button)

        case "info":
            InfoBar.info(
                title=parent.tr("Info"),
                content=msg,
                orient=Qt.Horizontal,
                isClosable=True,
                duration=2000,
                position=InfoBarPosition.TOP_RIGHT,
                parent=parent,
            )


def steampulse_file_remover(file: str):

    if os.path.isfile(file):
        os.remove(file)
