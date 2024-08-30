import json
import logging
from math import ceil
from datetime import datetime
from dateutil.relativedelta import relativedelta

from PyQt5.QtCore import Qt, QThread, QUrl, QTimer
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QWidget

from qfluentwidgets import (
    IndeterminateProgressRing,
    InfoBarPosition,
    ProgressRing,
    InfoBarIcon,
    FluentIcon,
    InfoBar,
    setCustomStyleSheet,
)

from ..ui.game_ui import GameUi
from ...common.config import cfg
from ...common.info import CURRENCY_KEY_PRICE, MAIN_LOG, currency
from ...common.tool import SteamPulseIcon, signal_bus, steampulse_infobar
from ...common.component import Dialog, ImageCard, ShimmerEffect
from ...common.steam_api import SteamApi


logger = logging.getLogger("SteamPulse")


class GameWidget(QWidget, GameUi):

    def __init__(self, infobar_pos):
        super().__init__()

        self.INFOBAR_POS = infobar_pos

        self.app_id = ""
        self.first_run = True
        self.qthread = None

        self.setupUi(self)
        self.init_ui()
        self.signal_bus()

    def init_ui(self):

        self.image_card = ImageCard()
        self.image_card.package_changed.connect(self.package_process)

        self.info_crd_lyt.insertWidget(0, self.image_card)
        self.info_crd_lyt.setAlignment(Qt.AlignLeft)

        self.info_lyt.setAlignment(Qt.AlignTop)
        self.label_lyt.setAlignment(Qt.AlignLeft)

        self.steam_btn.setIcon(SteamPulseIcon.STEAM)
        self.steam_btn.setDisabled(True)

        self.steamdb_btn.setIcon(SteamPulseIcon.STEAMDB)
        self.steamdb_btn.setDisabled(True)

        self.pcgw_btn.setIcon(SteamPulseIcon.PCGW)
        self.pcgw_btn.setDisabled(True)

        self.website_btn.setIcon(FluentIcon.GLOBE)
        self.website_btn.setDisabled(True)

        self.shimmer_effect = ShimmerEffect()
        self.shimmer_effect.hide()
        self.shimmer_effect.setSpacing(20)
        self.shimmer_effect.addShape(230)
        self.shimmer_effect.addShape(70)
        self.shimmer_effect.addShape(50)
        self.shimmer_effect.addShape(50)
        self.shimmer_effect.addShape(200)
        self.shimmer_effect.addShape(40)
        self.shimmer_effect.addShape(180)

        self.lbl_lyt.insertWidget(0, self.shimmer_effect)

        style = "PlainTextEdit, PushButton {border-radius: 16px}"
        widgets = [
            self.steam_btn,
            self.steamdb_btn,
            self.pcgw_btn,
            self.website_btn,
        ]
        for widget in widgets:
            setCustomStyleSheet(widget, style, style)

    def game_process(self):

        if self.app_id.isdigit():

            if self.first_run:
                self.key_process()

            else:
                if self.qthread == None:
                    self.qthread = QThread()

                    self.steam_api = SteamApi(
                        app_id=self.app_id, last_app_id=self.image_card.get_last_appid()
                    )
                    self.steam_api.moveToThread(self.qthread)
                    self.steam_api.state.connect(self.game_states)
                    self.steam_api.result.connect(self.game_result)
                    self.steam_api.image.connect(self.image_card.set_image)

                    self.qthread.started.connect(self.steam_api.game_data)
                    self.qthread.finished.connect(self.process_finish)
                    self.qthread.start()
        else:
            steampulse_infobar(self.INFOBAR_POS, "error", self.tr("AppID not provided or wrong"))

    def game_states(self, state: str):

        if state == "started":
            self.working_infobar = InfoBar.new(
                InfoBarIcon.INFORMATION,
                self.tr("Working"),
                "",
                Qt.Horizontal,
                False,
                -1,
                InfoBarPosition.TOP,
                self.INFOBAR_POS,
            )
            ring_wgt = IndeterminateProgressRing(self)
            ring_wgt.setFixedSize(22, 22)
            ring_wgt.setStrokeWidth(4)
            self.working_infobar.addWidget(ring_wgt)

            self.image_card.show_shimmer()

            if self.image_card.get_last_appid() != self.app_id:
                self.image_card.clear()

            self.shimmer_effect.show()

            self.release_lbl.hide()
            self.player_lbl.hide()
            self.dlc_lbl.hide()
            self.achievement_lbl.hide()
            self.genre_lbl.hide()
            self.package_lbl.hide()
            self.platform_lbl.hide()

            self.steam_btn.setDisabled(True)
            self.steamdb_btn.setDisabled(True)
            self.pcgw_btn.setDisabled(True)
            self.website_btn.setDisabled(True)

        elif "finished":
            self.working_infobar.close()
            self.working_infobar.deleteLater()

            self.qthread.quit()

            self.shimmer_effect.hide()

            self.release_lbl.show()
            self.player_lbl.show()
            self.dlc_lbl.show()
            self.achievement_lbl.show()
            self.genre_lbl.show()
            self.package_lbl.show()
            self.platform_lbl.show()

            self.steam_btn.setEnabled(True)
            self.steamdb_btn.setEnabled(True)
            self.pcgw_btn.setEnabled(True)
            self.website_btn.setEnabled(True)

    def game_result(self, result: dict):

        if result:
            result = json.dumps(result, indent=4)
            jsonify = json.loads(result)

            # ========== Image Card ==========
            # developers
            if "developers" in jsonify.keys():
                developers = ""
                for item in jsonify["developers"]:
                    developers += f", {item}"
            else:
                developers = ""

            # publishers
            if "publishers" in jsonify.keys():
                publishers = ""
                for item in jsonify["publishers"]:
                    publishers += f", {item}"
            else:
                publishers = ""

            # metacritic
            if "metacritic" in jsonify.keys():
                metacritic = str(jsonify["metacritic"]["score"])
            else:
                metacritic = ""

            # packages
            if "packages" in jsonify.keys():
                packages = [str(item) for item in jsonify["packages"]]
            else:
                packages = [""]

            # prices
            if "price_overview" in jsonify.keys():
                # base price
                base_price = float(f"{jsonify['price_overview']['initial'] / 100:.2f}")

                # discount
                discount = jsonify["price_overview"]["discount_percent"]

                # final price
                final_price = float(f"{jsonify['price_overview']['final'] / 100:.2f}")

                if base_price == final_price:
                    base_price = 0
            else:
                base_price = 0
                discount = 0
                final_price = -1

            if jsonify["is_free"]:
                final_price = 0

            if final_price > 1:
                key_calculate = self.calculate_key(final_price)
                key_count = key_calculate["key_count"]
                key_price = key_calculate["key_price"]
            else:
                key_count = 0
                key_price = 0

            # set value
            self.image_card.set_text_game(
                jsonify["steam_appid"],
                jsonify["type"],
                jsonify["name"],
                developers[2:],
                publishers[2:],
                metacritic,
                packages,
                base_price,
                discount,
                final_price,
                key_count,
                key_price,
            )

            # ========== Label ==========
            # release
            if "release_date" in jsonify.keys():
                if jsonify["release_date"]["date"] != "Coming soon":
                    # convert to date object
                    try:
                        date_rel = datetime.strptime(jsonify["release_date"]["date"], "%d %b, %Y")
                    except:
                        date_rel = datetime.strptime(jsonify["release_date"]["date"], "%b %d, %Y")
                    # calculate diff from now date
                    date_diff = relativedelta(datetime.now(), date_rel)

                    date_rel_formatted = date_rel.strftime("%d %b %Y")
                    date_years = date_diff.years
                    date_months = date_diff.months
                    date_days = date_diff.days

                    if date_years != 0:
                        text = f"{date_rel_formatted} ({date_years} {self.tr('years')}"
                        if date_months != 0:
                            text += f", {date_months}  {self.tr('months')}"
                        text += f" {self.tr('ago')})"
                        self.release_lbl.setText(text)
                    elif date_months != 0:
                        text = f"{date_rel_formatted} ({date_months}"
                        if date_days != 0:
                            text += f", {date_days} {self.tr('days')}"
                        text += f" {self.tr('ago')})"
                        self.release_lbl.setText(text)
                    else:
                        self.release_lbl.setText(
                            f"{date_rel_formatted} ({date_days} {self.tr('days ago')})"
                        )
                else:
                    self.release_lbl.setText(self.tr("Coming soon"))

            # players
            if jsonify["player_count"] != 0:
                self.player_lbl.setText(str(jsonify["player_count"]))
            else:
                self.player_lbl.setText("N\A")

            # dlc
            if "dlc" in jsonify.keys():
                self.dlc_lbl.setText(str(len(jsonify["dlc"])))
            else:
                self.dlc_lbl.setText("N\A")

            # achievements
            if "achievements" in jsonify.keys():
                self.achievement_lbl.setText(str(jsonify["achievements"]["total"]))
            else:
                self.achievement_lbl.setText("N\A")

            # packages
            if "packages" in jsonify.keys():
                self.package_lbl.setText(str(len(jsonify["packages"])))
            else:
                self.package_lbl.setText("N\A")

            # genres
            if "genres" in jsonify.keys():
                genres = ""
                for item in jsonify["genres"]:
                    genres += f', {item["description"]}'
                self.genre_lbl.setText(genres[2:])
            else:
                self.genre_lbl.setText("N\A")

            # platforms
            if "platforms" in jsonify.keys():
                platforms = ""
                for key, value in jsonify["platforms"].items():
                    if value == True:
                        platforms += f", {key.capitalize()}"
                self.platform_lbl.setText(platforms[2:])
            else:
                self.platform_lbl.setText("N\A")

            # steam
            self.steam_btn.clicked.connect(
                lambda: QDesktopServices.openUrl(
                    QUrl(f'https://store.steampowered.com/app/{jsonify["steam_appid"]}')
                )
            )

            # steamdb
            self.steamdb_btn.clicked.connect(
                lambda: QDesktopServices.openUrl(
                    QUrl(f'https://steamdb.info/app/{jsonify["steam_appid"]}')
                )
            )

            # pcgw
            self.pcgw_btn.clicked.connect(
                lambda: QDesktopServices.openUrl(
                    QUrl(f'https://pcgamingwiki.com/api/appid.php?appid={jsonify["steam_appid"]}')
                )
            )

            # website
            if jsonify["website"] != None:
                self.website_btn.clicked.connect(
                    lambda: QDesktopServices.openUrl(QUrl(jsonify["website"]))
                )
                self.website_btn.setEnabled(True)
            elif jsonify["support_info"]["url"] != None:
                self.website_btn.clicked.connect(
                    lambda: QDesktopServices.openUrl(QUrl(jsonify["support_info"]["url"]))
                )
                self.website_btn.setEnabled(True)

            steampulse_infobar(self.INFOBAR_POS, "success", self.tr("Game data loaded"))

        else:
            self.image_card.clear()

            self.release_lbl.hide()
            self.player_lbl.hide()
            self.dlc_lbl.hide()
            self.achievement_lbl.hide()
            self.genre_lbl.hide()
            self.package_lbl.hide()
            self.platform_lbl.hide()

            self.release_lbl.clear()
            self.player_lbl.clear()
            self.dlc_lbl.clear()
            self.achievement_lbl.clear()
            self.genre_lbl.clear()
            self.package_lbl.clear()
            self.platform_lbl.clear()

            self.steam_btn.setDisabled(True)
            self.steamdb_btn.setDisabled(True)
            self.pcgw_btn.setDisabled(True)
            self.website_btn.setDisabled(True)

            steampulse_infobar(
                self.INFOBAR_POS, "error_btn", self.tr("Failed to get game data"), MAIN_LOG
            )

    def package_process(self, package_id: str):

        if self.qthread == None:
            self.qthread = QThread()

            self.steam_api = SteamApi(package_id=package_id)
            self.steam_api.moveToThread(self.qthread)
            self.steam_api.state.connect(self.game_states)
            self.steam_api.result.connect(self.package_result)
            self.steam_api.image.connect(self.image_card.set_image)

            self.qthread.started.connect(self.steam_api.package_data)
            self.qthread.finished.connect(self.process_finish)
            self.qthread.start()

    def package_result(self, result: dict):

        if result:
            result = json.dumps(result, indent=4)
            jsonify = json.loads(result)

            # prices
            if "price" in jsonify.keys():
                # base price
                base_price = float(f"{jsonify['price']['initial'] / 100:.2f}")

                # discount
                discount = jsonify["price"]["discount_percent"]

                # final price
                final_price = float(f"{jsonify['price']['final'] / 100:.2f}")

                if base_price == final_price:
                    base_price = 0
            else:
                base_price = 0
                discount = 0
                final_price = -1

            if final_price > 1:
                key_calculate = self.calculate_key(final_price)
                key_count = key_calculate["key_count"]
                key_price = key_calculate["key_price"]
            else:
                key_count = 0
                key_price = 0

            # set value
            self.image_card.set_text_package(
                jsonify["name"],
                base_price,
                discount,
                final_price,
                key_count,
                key_price,
            )

            self.calculate_key(final_price)

            steampulse_infobar(self.INFOBAR_POS, "success", self.tr("Package data loaded"))

        else:
            steampulse_infobar(
                self.INFOBAR_POS, "error_btn", self.tr("Failed to get package data"), MAIN_LOG
            )

    def key_process(self):

        if self.qthread == None:
            self.ring_wgt = ProgressRing(self)

            self.qthread = QThread()

            self.steam_api = SteamApi()
            self.steam_api.moveToThread(self.qthread)
            self.steam_api.state.connect(self.key_states)
            self.steam_api.result.connect(self.key_result)
            self.steam_api.key_progress.connect(self.ring_wgt.setVal)

            self.qthread.started.connect(self.steam_api.key_info)
            self.qthread.finished.connect(self.process_finish)
            if self.app_id and self.first_run == False:
                self.qthread.finished.connect(self.game_process)
            self.qthread.start()

    def key_states(self, state: str):

        if state == "started":
            self.working_infobar = InfoBar.new(
                InfoBarIcon.INFORMATION,
                self.tr("Get key data"),
                "",
                Qt.Horizontal,
                False,
                -1,
                InfoBarPosition.TOP,
                self.INFOBAR_POS,
            )
            self.ring_wgt.setRange(0, 11)
            self.ring_wgt.setFixedSize(22, 22)
            self.ring_wgt.setStrokeWidth(4)
            self.working_infobar.addWidget(self.ring_wgt)

        elif "finished":
            self.working_infobar.close()
            self.working_infobar.deleteLater()

            self.qthread.quit()

    def key_result(self, result: dict):

        if result:
            self.first_run = False

        else:
            self.first_run = True
            steampulse_infobar(
                self.INFOBAR_POS, "error_btn", self.tr("Failed to get key data"), MAIN_LOG
            )

    def database_proccess(self):

        if self.qthread == None:

            self.qthread = QThread()

            self.steam_api = SteamApi()
            self.steam_api.moveToThread(self.qthread)
            self.steam_api.state.connect(self.database_states)
            self.steam_api.result.connect(self.database_result)

            self.qthread.started.connect(self.steam_api.build_database)
            self.qthread.finished.connect(self.process_finish)
            self.qthread.start()

    def database_states(self, state: str):

        if state == "started":
            self.working_infobar = InfoBar.new(
                InfoBarIcon.INFORMATION,
                self.tr("Downloading"),
                "",
                Qt.Horizontal,
                False,
                -1,
                InfoBarPosition.TOP,
                self.INFOBAR_POS,
            )
            ring_wgt = IndeterminateProgressRing(self)
            ring_wgt.setFixedSize(22, 22)
            ring_wgt.setStrokeWidth(4)
            self.working_infobar.addWidget(ring_wgt)

        elif "finished":
            self.working_infobar.close()
            self.working_infobar.deleteLater()

            self.qthread.quit()

    def database_result(self, result: dict):

        if result:
            signal_bus.game_database.emit(True)

            steampulse_infobar(self.INFOBAR_POS, "success", self.tr("Games database loaded"))

        else:
            signal_bus.game_database.emit(False)

            steampulse_infobar(
                self.INFOBAR_POS, "error_btn", self.tr("Failed to get games database"), MAIN_LOG
            )

    def calculate_key(self, app_price: float):

        locale = currency(cfg.region.value)

        # if locale["name"] == ("India", "Russia", "Ukraine", "Kazakhstan"):
        #     app_price = int(app_price)

        key_price = CURRENCY_KEY_PRICE[locale["name"]]
        irt_price = CURRENCY_KEY_PRICE["Tooman"]
        key_count = ceil(app_price / key_price)
        key_price = key_count * irt_price

        return {
            "key_count": f"{key_count}",
            "key_price": f"{key_price:,}",
        }

    def set_appid(self, app_id: str):

        if "|" in app_id:
            self.app_id = app_id.split("|")[1].strip()
        elif app_id.isdigit():
            self.app_id = app_id
        else:
            steampulse_infobar(self.INFOBAR_POS, "error", self.tr("AppID is not provided or wrong"))

    def process_finish(self):

        self.qthread = None

    def database_exist(self, exist: bool):

        if exist:
            self.steam_btn.setEnabled(True)
            self.steamdb_btn.setEnabled(True)
            self.pcgw_btn.setEnabled(True)
            self.website_btn.setEnabled(True)

        else:
            QTimer.singleShot(1, self.download_dialog)

            self.steam_btn.setDisabled(True)
            self.steamdb_btn.setDisabled(True)
            self.pcgw_btn.setDisabled(True)
            self.website_btn.setDisabled(True)

    def download_dialog(self):

        dialog = Dialog(
            self.tr("Download database"),
            self.tr(
                "Steam games database not found, Do you want to download it?\n(App will not work without this!)"
            ),
            self.window(),
        )
        dialog.yesButton.setText(self.tr("Yes"))
        dialog.cancelButton.setText(self.tr("No"))

        if dialog.exec_():
            self.database_proccess()

    def signal_bus(self):

        signal_bus.search_emit.connect(self.set_appid)
        signal_bus.search_emit.connect(self.game_process)
        signal_bus.region_change.connect(self.game_process)
        signal_bus.game_database.connect(self.database_exist)
