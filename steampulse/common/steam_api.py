import json
import logging
import time
import requests
import xml.etree.ElementTree as ET
from PyQt5.QtCore import pyqtSignal, QObject
from io import BytesIO

from .info import CURRENCY_KEY_REGION, CURRENCY_KEY_PRICE, currency, GAMES_DATABASE
from .tool import signal_bus
from .config import cfg


logger = logging.getLogger("SteamPulse")

# Process.Start("steam://openurl/https://store.steampowered.com/app/{app_id});


class SteamApi(QObject):

    state = pyqtSignal(str)
    result = pyqtSignal(dict)
    image = pyqtSignal(bytes)
    key_progress = pyqtSignal(int)

    def __init__(self, app_id: str = "", package_id: str = "", last_app_id: str = ""):
        super().__init__()

        self.app_id = app_id
        self.package_id = package_id
        self.last_app_id = last_app_id

        self.progress = 0

        self.headers = {"User-Agent": "Chrome/126.0.0.0"}

    def sale_info(self):

        self.state.emit("started")

        try:
            url = "https://api.codemage.ir/Projects/SteamPulse/Data.xml"
            logger.info(f"SaleData: Requesting to {url}")

            data = requests.get(url, headers=self.headers)

            if data.ok:
                xml_element = ET.XML(data.text)
                xml_tree = ET.ElementTree(xml_element)
                xml_root = xml_tree.getroot()[0]
                jsonify = {}

                for item in xml_root:
                    if item.tag.startswith(("Salebanner", "Saleend", "Saleurl")):
                        jsonify.update({item.tag: item.text})

                sale_timer = int(int(jsonify["Saleend"]) - time.time())

                cfg.set(cfg.sale_end, int(jsonify["Saleend"]))
                cfg.set(cfg.sale_url, jsonify["Saleurl"])

                if sale_timer > 5:
                    # image request
                    img = requests.get(jsonify["Salebanner"], headers=self.headers)

                    # send image data
                    if img.ok:
                        self.image.emit(BytesIO(img.content).getvalue())
                    else:
                        self.image.emit(b"")

                    # send data for ui
                    self.result.emit({"success": 1})

                    logger.info("SaleData: SUCCESS, sale info loaded!")

                else:
                    self.result.emit({})
                    logger.info("SaleData: SUCCESS, sale info loaded but sale is ended!")

        except Exception as e:
            self.result.emit({})
            logger.error("SaleData: FAILED, maybe connection problem, check your internet!")

        self.state.emit("finished")

    def key_info(self):

        self.state.emit("started")

        try:
            # codemage key
            url = "https://api.codemage.ir/Projects/SteamPulse/ShopData"
            logger.info(f"KeyData: Requesting to {url}")

            self.key_progress.emit(self.progress)
            self.progress += 1

            data = requests.get(url, headers=self.headers)

            if data.ok:
                jsonify = data.json()

                CURRENCY_KEY_PRICE.update({"Tooman": jsonify["Key"]})

            else:
                CURRENCY_KEY_PRICE.update({"Tooman": 100000})

            # steam key
            for key, value in CURRENCY_KEY_REGION.items():
                url = f"https://steamcommunity.com/market/priceoverview/?appid=440&market_hash_name=Mann%20Co.%20Supply%20Crate%20Key&currency={value}"
                logger.info(f"KeyData: Requesting to {url}")

                self.key_progress.emit(self.progress)

                data = requests.get(url)

                if data.ok:
                    jsonify = data.json()

                    if jsonify["success"]:
                        # convert string to digit and take fee from it
                        key_price = int("".join(filter(str.isdigit, jsonify["lowest_price"])))
                        if "--" in jsonify["lowest_price"]:
                            key_price *= 100
                        key_price = float(f"{round(key_price / 1.15) / 100:.2f}")

                        CURRENCY_KEY_PRICE.update({key: key_price})

                        self.progress += 1

            # send data to ui
            for price in CURRENCY_KEY_PRICE.values():
                if price > 1:
                    signal_bus.key_updated.emit(True)
                    self.result.emit({"success": "1"})
                    logger.info("KeyData: SUCCESS, key price loaded!")

                else:
                    signal_bus.key_updated.emit(False)
                    self.result.emit({})
                    logger.error("KeyData: FAILED, some region price is not loaded!")
                    break

        except Exception as msg:
            print(msg)
            signal_bus.key_updated.emit(False)
            self.result.emit({})
            logger.error("KeyData: FAILED, maybe connection problem, check your internet!")

        self.state.emit("finished")

    def game_data(self):

        self.state.emit("started")

        locale = currency(cfg.region.value)

        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={self.app_id}&cc={locale['iso']}"
            logger.info(f"GameData: Requesting to {url}")

            data = requests.get(url)

            if data.ok:
                jsonify_data = data.json()

                # if app_id is correct and data collected
                if jsonify_data[self.app_id]["success"] == True:
                    # add player count to data
                    player_count = requests.get(
                        f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1?appid={self.app_id}"
                    )
                    if player_count.ok:
                        jsonify_data[self.app_id]["data"].update(
                            {"player_count": str(player_count.json()["response"]["player_count"])}
                        )

                    else:
                        jsonify_data[self.app_id]["data"].update({"player_count": "0"})

                    # image request
                    # first download and send iamge after data sent to applied in same time
                    # (because metacritic must be available before setting image)
                    if self.app_id != self.last_app_id:
                        img = requests.get(
                            f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{self.app_id}/capsule_616x353.jpg"
                        )

                    # send data for ui
                    self.result.emit(jsonify_data[self.app_id]["data"])

                    # send image for ui
                    if self.app_id != self.last_app_id:
                        if img.ok:
                            # send downloaded image if it's ok
                            self.image.emit(BytesIO(img.content).getvalue())

                        else:
                            # send empty response to set default app image
                            self.image.emit(b"")

                    else:
                        # send -1 response to set last image
                        # (because appid is't changed)
                        self.image.emit(b"-1")

                    logger.info(f"GameData: SUCCESS, game data | {self.app_id} loaded!")

                else:
                    self.image.emit(b"")
                    self.result.emit({})
                    logger.error(
                        f"GameData: FAILED, game data | {self.app_id} loaded, but maybe wrong app_id!"
                    )

        except Exception as msg:
            print(msg)
            self.image.emit(b"")
            self.result.emit({})
            logger.error("GameData: FAILED, maybe connection problem, check your internet!")

        self.state.emit("finished")

    def package_data(self):

        self.state.emit("started")

        locale = currency(cfg.region.value)

        try:
            url = f"https://store.steampowered.com/api/packagedetails/?packageids={self.package_id}&cc={locale['iso']}"
            logger.info(f"PackageData: Requesting to {url}")

            data = requests.get(url)

            if data.ok:
                jsonify_data = data.json()

                # if package_id is correct and data collected
                if jsonify_data[self.package_id]["success"] == True:
                    # send -1 response to set last image
                    # (because appid is't changed)
                    self.image.emit(b"-1")

                    # send data for ui
                    self.result.emit(jsonify_data[self.package_id]["data"])
                    logger.info(f"PackageData: SUCCESS, package data | {self.package_id} loaded!")

                else:
                    # send empty response to set default app image
                    self.image.emit(b"")

                    self.result.emit({})
                    logger.error(
                        f"PackageData: FAILED, package data | {self.package_id} loaded, but maybe wrong package_id!"
                    )

        except Exception as msg:
            print(msg)
            self.result.emit({})
            logger.error("PackageData: FAILED, maybe connection problem, check your internet!")

        self.state.emit("finished")

    def build_database(self):

        self.state.emit("started")

        try:
            url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
            logger.info(f"GamesDatabase: Requesting to {url}")

            data = requests.get(url)

            if data.ok:
                jsonify_data = data.json()["applist"]["apps"]

                games_dict = {}

                for game in jsonify_data:
                    for key, value in game.items():
                        if key == "appid":
                            temp_key = str(value)

                        elif key == "name":
                            if value != "":
                                games_dict.update({temp_key: value.strip()})

                sorted_value = sorted(games_dict.values())

                order_index = {value: index for index, value in enumerate(sorted_value)}
                sorted_items = dict(
                    sorted(
                        games_dict.items(),
                        key=lambda item: order_index.get(item[1], len(sorted_value)),
                    )
                )

                jsonify_sorted = json.dumps(sorted_items, indent=4)

                with open(GAMES_DATABASE, "w", encoding="utf-8") as f:
                    f.writelines(jsonify_sorted)

                self.result.emit({"success": "1"})
                logger.info(f"GamesDatabase: SUCCESS, save sorted database to {GAMES_DATABASE}")

            else:
                self.result.emit({})
                logger.error("GamesDatabase: FAILED, to get games database from steam")

        except Exception as msg:
            print(msg)
            self.result.emit({})
            logger.error("GamesDatabase: FAILED, to get games database from steam")

        self.state.emit("finished")
