import os
import time
import logging

from PyQt5.QtCore import Qt, QThread
from PyQt5.QtWidgets import QWidget, QVBoxLayout


from ...common.config import cfg
from ...common.info import SALE_IMG
from ...common.tool import steampulse_infobar
from ...common.component import BannerCard
from ...common.steam_api import SteamApi


logger = logging.getLogger("SteamPulse")


class BannerWidget(QWidget):

    def __init__(self, infobar_pos):
        super().__init__()

        self.INFOBAR_POS = infobar_pos

        self.qthread = None

        self.init_ui()

        self.banner_card.set_gif()
        
        self.sale_process()

    def init_ui(self):

        self.main_lyt = QVBoxLayout(self)
        self.main_lyt.setContentsMargins(0, 0, 0, 0)
        self.main_lyt.setAlignment(Qt.AlignCenter)

        self.banner_card = BannerCard()

        self.main_lyt.addWidget(self.banner_card)

    def sale_process(self):

        if self.qthread == None:
            self.qthread = QThread()

            self.steam_api = SteamApi()
            self.steam_api.moveToThread(self.qthread)
            self.steam_api.state.connect(self.sale_states)
            self.steam_api.result.connect(self.sale_result)
            self.steam_api.image.connect(self.banner_card.set_image)

            self.qthread.started.connect(self.steam_api.sale_info)
            self.qthread.finished.connect(self.process_finish)
            self.qthread.start()

    def sale_states(self, state: str):

        if state == "finished":
            self.qthread.quit()

    def sale_result(self, result: dict):

        if result:
            self.banner_card.set_data(cfg.sale_end.value, cfg.sale_url.value)

            steampulse_infobar(self.INFOBAR_POS, "success", "Steam Sale ongoing!")

    def process_finish(self):

        self.qthread = None
