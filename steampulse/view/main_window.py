import os
import logging

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, QEventLoop, QTimer
from PyQt5.QtWidgets import QApplication

from qfluentwidgets import (
    SplitFluentWindow,
    SplashScreen,
    FluentIcon,
)

from .interface.game_interface import GameInterface
from .interface.setting_interface import SettingInterface

from ..common.info import GAMES_DATABASE, MAIN_LOG
from ..common.component import SearchTitleBar
from ..common.tool import signal_bus
from ..common.config import cfg
from ..common import resource


logging.basicConfig(
    level=logging.INFO,
    filename=MAIN_LOG,
    filemode="w",
    encoding="utf-8",
    format="%(levelname)s (%(asctime)s): %(message)s",
    datefmt="%Y/%m/%d|%H:%M:%S",
)

logger = logging.getLogger("SteamPulse")


class MainWindow(SplitFluentWindow):

    def __init__(self):
        super().__init__()

        logger.info("App Started")
        logger.info(f'Current working directory: "{os.getcwd()}"')

        self.init_window()
        self.init_navigation()
        self.tools_exist()
        self.signal_bus()

    def init_window(self):

        # self.resize(1143, 650)
        self.setTitleBar(SearchTitleBar(self))
        self.resize(1150, 760)
        self.setMinimumSize(1150, 450)
        self.setWindowIcon(QIcon(":/vector/logo_color.svg"))
        self.setWindowTitle("SteamPulse")
        self.setMicaEffectEnabled(cfg.get(cfg.mica_effect))

        # center window
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        # splash screen
        self.splash_screen = SplashScreen(":/vector/logo_splash.svg", self)
        self.splash_screen.setIconSize(QSize(300, 300))
        self.splash_screen.raise_()
        self.show()
        loop = QEventLoop(self)
        QTimer.singleShot(350, loop.quit)
        loop.exec()
        self.splash_screen.finish()

    def init_navigation(self):

        self.widgetLayout.setContentsMargins(0, 50, 0, 0)
        self.navigationInterface.hide()

        self.game_interface = GameInterface()
        self.setting_interface = SettingInterface()

        self.addSubInterface(
            interface=self.game_interface,
            icon=FluentIcon.UNIT,
            text="Game",
        )

        self.addSubInterface(
            interface=self.setting_interface,
            icon=FluentIcon.SETTING,
            text="Settings",
        )

        self.navigationInterface.setCurrentItem(self.game_interface.objectName())

    def switch_interface(self, route_key):

        match route_key:
            case "game_interface":
                self.navigationInterface.panel.history.pop()
            case "setting_interface":
                self.stackedWidget.setCurrentWidget(self.setting_interface, popOut=False)

    def tools_exist(self):

        if os.path.isfile(GAMES_DATABASE):
            signal_bus.game_database.emit(True)

            logger.info(f"Games Database exist")

        else:
            signal_bus.game_database.emit(False)

            logger.info(f"Games Database not exist")

    def resizeEvent(self, e):
        super().resizeEvent(e)

        self.titleBar.move(0, 0)
        self.titleBar.resize(self.width(), self.titleBar.height())

        signal_bus.window_width.emit(e.size().width())

    def signal_bus(self):

        signal_bus.mica_enabled.connect(self.setMicaEffectEnabled)
        signal_bus.switch_interface.connect(self.switch_interface)
