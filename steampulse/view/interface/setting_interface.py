import logging

from PyQt5.QtCore import Qt, QUrl, QThread
from PyQt5.QtGui import QDesktopServices, QFont
from PyQt5.QtWidgets import QWidget, QSizePolicy, QHBoxLayout, QVBoxLayout

from qfluentwidgets import (
    IndeterminateProgressRing,
    PrimaryPushSettingCard,
    ComboBoxSettingCard,
    OptionsSettingCard,
    SwitchSettingCard,
    SimpleCardWidget,
    SettingCardGroup,
    ColorSettingCard,
    PushSettingCard,
    StrongBodyLabel,
    InfoBarPosition,
    HyperlinkLabel,
    AvatarWidget,
    InfoBarIcon,
    SettingCard,
    ScrollArea,
    FluentIcon,
    BodyLabel,
    InfoBar,
    setFont,
    setTheme,
    setThemeColor,
)


from ...common.component import Dialog
from ...common.steam_api import SteamApi
from ...common.config import cfg, is_win11
from ...common.tool import (
    signal_bus,
    steampulse_infobar,
    steampulse_file_remover,
)
from ...common.info import (
    REGION,
    GAMES_DATABASE,
    STEAMPULSE_FEEDBACK_URL,
    STEAMPULSE_ORIGINAL_URL,
    INSTAGRAM,
    TELEGRAM,
    VERSION,
    GITHUB,
    YEAR,
)


logger = logging.getLogger("SteamPulse")


class SettingInterface(ScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setObjectName("setting_interface")

        self.main_widget = QWidget()
        self.main_widget.setStyleSheet("background-color: transparent;")

        self.main_lyt = QVBoxLayout(self.main_widget)
        self.main_lyt.setContentsMargins(0, 0, 0, 0)
        self.main_lyt.setSpacing(30)

        self.setting_label = BodyLabel(self.tr("Settings"), self.main_widget)
        self.setting_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        setFont(self.setting_label, 33, QFont.Light)

        self.setViewportMargins(36, 36, 36, 36)
        self.setWidget(self.main_widget)
        self.setWidgetResizable(True)
        self.setStyleSheet("border: none; background-color: transparent;")

        self.cards()
        self.profile()
        self.signal_bus()

        # app
        self.app_group.addSettingCard(self.currency_card)
        self.app_group.addSettingCard(self.search_card)
        self.app_group.addSettingCard(self.update_card)
        self.app_group.addSettingCard(self.reset_card)

        # personalization
        self.personal_group.addSettingCard(self.theme_card)
        self.personal_group.addSettingCard(self.theme_color_card)
        self.personal_group.addSettingCard(self.mica_card)
        self.personal_group.addSettingCard(self.shimmer_color)
        self.personal_group.addSettingCard(self.zoom_card)
        self.personal_group.addSettingCard(self.language_card)

        # about
        self.about_group.addSettingCard(self.profile_card)
        self.about_group.addSettingCard(self.credit_card)
        self.about_group.addSettingCard(self.feedback_card)
        self.about_group.addSettingCard(self.about_card)

        self.main_lyt.addWidget(self.setting_label, alignment=Qt.AlignCenter)
        self.main_lyt.addWidget(self.app_group)
        self.main_lyt.addWidget(self.personal_group)
        self.main_lyt.addWidget(self.about_group)
        self.main_lyt.addStretch(1)

    def cards(self):

        self.app_group = SettingCardGroup(self.tr("App"), self.main_widget)

        self.currency_card = ComboBoxSettingCard(
            cfg.region,
            FluentIcon.GLOBE,
            self.tr("Currency region"),
            self.tr("Change region and set country currency in key calculation"),
            texts=REGION,
            parent=self.app_group,
        )

        self.search_card = ComboBoxSettingCard(
            cfg.search_mode,
            FluentIcon.SEARCH,
            self.tr("Search mode"),
            self.tr("Change mode between search in whole game name or exactly"),
            texts=["Contains", "Exactly"],
            parent=self.app_group,
        )

        self.update_card = PrimaryPushSettingCard(
            self.tr("Update database"),
            FluentIcon.UPDATE,
            self.tr("Update database"),
            self.tr("Re-download games database and update it"),
            self.app_group,
        )

        self.reset_card = PushSettingCard(
            self.tr("Reset app"),
            FluentIcon.BROOM,
            self.tr("Reset app"),
            self.tr("Delete all tools files and app config"),
            self.app_group,
        )

        # personalization
        self.personal_group = SettingCardGroup(self.tr("Personalization"), self.main_widget)

        self.theme_card = OptionsSettingCard(
            cfg.themeMode,
            FluentIcon.BRUSH,
            self.tr("Application theme"),
            self.tr("Change the theme appearance"),
            texts=[self.tr("Light"), self.tr("Dark"), self.tr("Use system setting")],
            parent=self.personal_group,
        )

        self.theme_color_card = ColorSettingCard(
            cfg.themeColor,
            FluentIcon.PALETTE,
            self.tr("Theme color"),
            self.tr("Change the theme color"),
            self.personal_group,
        )
        self.theme_color_card.colorPicker.setFixedWidth(78)

        self.mica_card = SwitchSettingCard(
            FluentIcon.TRANSPARENT,
            self.tr("Mica effect"),
            self.tr("Apply semi-transparent to windows and surfaces (Win11)"),
            cfg.mica_effect,
            self.personal_group,
        )
        self.mica_card.setEnabled(is_win11())

        self.shimmer_color = SwitchSettingCard(
            FluentIcon.BACKGROUND_FILL,
            self.tr("Colorize shimmer effect"),
            self.tr("Theme color for shimmer effect"),
            cfg.shimmer_color,
            self.personal_group,
        )

        self.zoom_card = ComboBoxSettingCard(
            cfg.dpi_scale,
            FluentIcon.ZOOM,
            self.tr("Interface zoom"),
            self.tr("Change the size of widgets and fonts"),
            texts=["100%", "125%", "150%", "175%", "200%", self.tr("Use system setting")],
            parent=self.personal_group,
        )

        self.language_card = ComboBoxSettingCard(
            cfg.language,
            FluentIcon.LANGUAGE,
            self.tr("Language"),
            self.tr("Set preferred language for UI"),
            texts=["English", self.tr("Use system setting")],
            parent=self.personal_group,
        )

        # about
        self.about_group = SettingCardGroup(self.tr("About"), self.main_widget)

        self.feedback_card = PrimaryPushSettingCard(
            self.tr("Provide feedback"),
            FluentIcon.FEEDBACK,
            self.tr("Provide feedback"),
            self.tr("Help us improve SteamPulse by providing feedback"),
            self.about_group,
        )

        self.credit_card = PushSettingCard(
            "Github",
            FluentIcon.PEOPLE,
            self.tr("SteamPulse (Original)"),
            "Amirhosein Davatgari",
            self.about_group,
        )

        self.about_card = SettingCard(
            FluentIcon.INFO,
            self.tr("About"),
            "© "
            + self.tr("Copyright")
            + f" {YEAR}, AmirMahdavi. "
            + self.tr("Version")
            + " "
            + VERSION,
            self.about_group,
        )

    def profile(self):

        self.profile_card = SimpleCardWidget(self.main_widget)
        self.profile_card.setFixedHeight(120)

        self.profile_lyt = QHBoxLayout(self.profile_card)
        self.profile_lyt.setContentsMargins(16, 0, 0, 0)
        self.profile_lyt.setSpacing(16)
        self.profile_lyt.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # avatar
        self.avatar = AvatarWidget(self.profile_card)
        self.avatar.setObjectName("avatar")
        self.avatar.setImage(":/image/avatar.png")
        self.avatar.setRadius(40)

        # text
        self.profile_text_lyt = QVBoxLayout()
        self.profile_text_lyt.setSpacing(0)
        self.profile_text_lyt.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.profile_name_label = StrongBodyLabel(self.profile_card)
        self.profile_name_label.setText("Amir Mahdavi")
        self.profile_name_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.profile_email_label = BodyLabel(self.profile_card)
        self.profile_email_label.setText("mahdaviamir33@gmail.com")
        self.profile_email_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        # link
        self.profile_link_lyt = QHBoxLayout()
        self.profile_link_lyt.setSpacing(10)

        self.profile_github_link = HyperlinkLabel("GitHub", self.profile_card)
        self.profile_github_link.setUrl(GITHUB)

        self.profile_telegram_link = HyperlinkLabel("Telegram", self.profile_card)
        self.profile_telegram_link.setUrl(TELEGRAM)

        self.profile_instagram_ink = HyperlinkLabel("Instagram", self.profile_card)
        self.profile_instagram_ink.setUrl(INSTAGRAM)

        self.profile_link_lyt.addWidget(self.profile_github_link)
        self.profile_link_lyt.addWidget(self.profile_telegram_link)
        self.profile_link_lyt.addWidget(self.profile_instagram_ink)

        self.profile_text_lyt.addWidget(self.profile_name_label)
        self.profile_text_lyt.addWidget(self.profile_email_label)
        self.profile_text_lyt.addSpacing(5)
        self.profile_text_lyt.addLayout(self.profile_link_lyt)

        self.profile_lyt.addWidget(self.avatar)
        self.profile_lyt.addLayout(self.profile_text_lyt)

    def reset_app(self):

        dialog = Dialog(
            self.tr("Reset app"),
            self.tr(
                "Are you sure want to reset app and delete all data?\nThis action is Irreversible!"
            ),
            self.window(),
        )

        if dialog.exec_():
            steampulse_file_remover("config.json")
            steampulse_file_remover(GAMES_DATABASE)
            signal_bus.game_database.emit(False)

            steampulse_infobar(self, "success", self.tr("Configuration takes effect after restart"))
            logger.info("All tools and app config deleted")

    def update_db_process(self):

        steampulse_file_remover(GAMES_DATABASE)
        signal_bus.game_database.emit(False)

        self.qthread = QThread()

        self.steam_api = SteamApi()
        self.steam_api.moveToThread(self.qthread)
        self.steam_api.state.connect(self.update_db_states)
        self.steam_api.result.connect(self.update_db_result)

        self.qthread.started.connect(self.steam_api.build_database)
        self.qthread.start()

    def update_db_states(self, state: str):

        if state == "started":
            self.working_infobar = InfoBar.new(
                InfoBarIcon.INFORMATION,
                self.tr("Working"),
                "",
                Qt.Horizontal,
                False,
                -1,
                InfoBarPosition.TOP,
                self,
            )
            ring_wgt = IndeterminateProgressRing(self)
            ring_wgt.setFixedSize(22, 22)
            ring_wgt.setStrokeWidth(4)
            self.working_infobar.addWidget(ring_wgt)

            self.currency_card.setDisabled(True)
            self.search_card.setDisabled(True)
            self.update_card.setDisabled(True)
            self.reset_card.setDisabled(True)

        elif "finished":
            self.working_infobar.close()
            self.working_infobar.deleteLater()

            self.currency_card.setEnabled(True)
            self.search_card.setEnabled(True)
            self.update_card.setEnabled(True)
            self.reset_card.setEnabled(True)

            self.qthread.quit()

    def update_db_result(self, result: dict):

        if result:
            signal_bus.game_database.emit(True)

            steampulse_infobar(self, "success", "SHOMBOL DOMBOL MOMBOL")

        else:
            signal_bus.game_database.emit(False)

            steampulse_infobar(self, "error", "SHOMBOL DOMBOL MOMBOL")

    def edge_spacer(self, width):

        spacer_width = int((width - 1070) / 2)
        self.setViewportMargins(spacer_width, 36, spacer_width, 36)

    def signal_bus(self):

        signal_bus.window_width.connect(self.edge_spacer)

        cfg.appRestartSig.connect(
            lambda: steampulse_infobar(self, "success", "Configuration takes effect after restart")
        )

        # app
        self.search_card.comboBox.currentTextChanged.connect(signal_bus.search_mode)
        self.currency_card.comboBox.currentTextChanged.connect(signal_bus.region_change)
        self.currency_card.comboBox.currentTextChanged.connect(
            lambda: signal_bus.switch_interface.emit("game_interface")
        )
        self.update_card.clicked.connect(self.update_db_process)
        self.reset_card.clicked.connect(self.reset_app)

        # personalization
        self.mica_card.checkedChanged.connect(signal_bus.mica_enabled)
        self.shimmer_color.checkedChanged.connect(signal_bus.shimmer_color)
        self.theme_color_card.colorChanged.connect(lambda c: setThemeColor(c, lazy=True))
        self.theme_card.optionChanged.connect(lambda ci: setTheme(cfg.get(ci), lazy=True))

        # about
        self.feedback_card.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(STEAMPULSE_FEEDBACK_URL))
        )
        self.credit_card.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(STEAMPULSE_ORIGINAL_URL))
        )
