import os
import json
import time
import statistics
from io import BytesIO
from PIL import Image, ImageFilter, ImageEnhance

from colorthief import ColorThief

from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import (
    QVariantAnimation,
    QEasingCurve,
    pyqtSignal,
    QEvent,
    QTimer,
    QRectF,
    QSize,
    QUrl,
    Qt,
)
from PyQt5.QtGui import (
    QDesktopServices,
    QLinearGradient,
    QFontDatabase,
    QPainterPath,
    QResizeEvent,
    QFontMetrics,
    QPainter,
    QImage,
    QBrush,
    QColor,
    QMovie,
    QIcon,
    QFont,
    QPen,
)
from PyQt5.QtWidgets import (
    QGraphicsDropShadowEffect,
    QGraphicsProxyWidget,
    QGraphicsScene,
    QGraphicsView,
    QVBoxLayout,
    QHBoxLayout,
    QCompleter,
    QWidget,
    QLabel,
    QFrame,
)

from qfluentwidgets import (
    MSFluentTitleBar,
    SearchLineEdit,
    MessageBoxBase,
    SubtitleLabel,
    ToolTipFilter,
    IconWidget,
    FluentIcon,
    ImageLabel,
    ToolButton,
    BodyLabel,
    InfoLevel,
    InfoBadge,
    ComboBox,
    Theme,
    setFont,
    themeColor,
    setCustomStyleSheet,
)

from .tool import signal_bus
from .info import SALE_IMG, currency, GAMES_DATABASE
from .config import cfg


class SearchTitleBar(MSFluentTitleBar):

    def __init__(self, parent):
        super().__init__(parent)

        self._init_ui()
        self._toggle_setting("game_interface")
        self._signal_bus()

    def _init_ui(self):

        self.setFixedHeight(52)

        self.search_line = SearchLineEdit(self)
        self.search_line.setFixedWidth(600)
        self.search_line.setToolTip(
            "Search with game name or it's appid\nyou can change search behavior in settings"
        )
        self.search_line.setPlaceholderText(self.tr("Search through games ..."))
        self.search_line.setClearButtonEnabled(True)
        self.search_line.installEventFilter(ToolTipFilter(self.search_line))
        self.search_line.searchSignal.connect(signal_bus.search_emit.emit)
        self.search_line.returnPressed.connect(
            lambda: QTimer.singleShot(
                1, lambda: signal_bus.search_emit.emit(self.search_line.text())
            )
        )

        self.setting_btn = ToolButton(self)
        self.setting_btn.setFixedSize(34, 34)
        self.setting_btn.setIcon(FluentIcon.SETTING)
        self.setting_btn.installEventFilter(ToolTipFilter(self.setting_btn))
        self.setting_btn.setToolTip(self.tr("Settings"))
        self.setting_btn.clicked.connect(
            lambda: signal_bus.switch_interface.emit("setting_interface")
        )

        self.back_btn = ToolButton(self)
        self.back_btn.setFixedSize(34, 34)
        self.back_btn.setIcon(FluentIcon.LEFT_ARROW)
        self.back_btn.installEventFilter(ToolTipFilter(self.back_btn))
        self.back_btn.setToolTip(self.tr("Back"))
        self.back_btn.clicked.connect(lambda: signal_bus.switch_interface.emit("game_interface"))

        style = "ToolButton {border-radius: 17px;}"
        setCustomStyleSheet(self.setting_btn, style, style)
        setCustomStyleSheet(self.back_btn, style, style)

        self.hBoxLayout.insertWidget(5, self.setting_btn)
        self.hBoxLayout.insertWidget(6, self.back_btn)
        self.hBoxLayout.insertSpacing(7, 50)

    def _database_exist(self, exist: bool):

        if exist:
            self.search_line.setEnabled(True)
            self._load_database(cfg.search_mode.value)

        else:
            self.search_line.setDisabled(True)

    def _load_database(self, mode: str):

        if os.path.isfile(GAMES_DATABASE):
            with open(GAMES_DATABASE, "r", encoding="utf-8") as f:
                database = json.loads(f.read())

        finded = []

        for key, value in database.items():
            finded.append(f"{value} | {key}")

        completer = QCompleter(finded, self.search_line)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setMaxVisibleItems(10)

        if mode == "Contains":
            completer.setFilterMode(Qt.MatchContains)
        elif "Exactly":
            completer.setFilterMode(Qt.MatchExactly)

        self.search_line.setCompleter(completer)

        database = ""

    def _toggle_setting(self, interface: str):

        if interface == "game_interface":
            self.search_line.show()
            self.setting_btn.show()
            self.back_btn.hide()

        elif "setting_interface":
            self.search_line.hide()
            self.setting_btn.hide()
            self.back_btn.show()

    def _signal_bus(self):

        signal_bus.game_database.connect(self._database_exist)
        signal_bus.search_mode.connect(self._load_database)
        signal_bus.switch_interface.connect(self._toggle_setting)

    def setTitle(self, title):

        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()

    def setIcon(self, icon):

        self.iconLabel.setPixmap(QIcon(icon).pixmap(26, 26))
        self.iconLabel.setFixedSize(26, 26)

    def resizeEvent(self, e):

        self.search_line.move(
            (self.width() - self.search_line.width()) // 2,
            9,
        )


class Dialog(MessageBoxBase):

    def __init__(self, title, contet, parent=None):
        super().__init__(parent)

        self.titleLabel = SubtitleLabel(title, self)

        self.text = BodyLabel(self)
        self.text.setText(contet)
        setFont(self.text, 16)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(12)
        self.viewLayout.addWidget(self.text)

        # self.widget.setMinimumWidth(400)


class BannerCard(QWidget):

    def __init__(self):
        super().__init__()

        self.w = 1067
        self.h = 170

        self.setFixedSize(self.w, self.h)
        self.setCursor(Qt.PointingHandCursor)

        self.seconds = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self._countdown)

        self._init_ui()
        self._show_time()

    def _init_ui(self):

        self.banner_img = ImageLabel(self)
        self.banner_img.setBorderRadius(16, 16, 16, 16)
        self.banner_img.hide()

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 1)

        self.timer_lbl = InfoBadge(self)
        self.timer_lbl.hide()
        self.timer_lbl.resize(115, 30)
        self.timer_lbl.move(947, 132)
        self.timer_lbl.setAlignment(Qt.AlignCenter)
        setFont(self.timer_lbl, 18, QFont.DemiBold)
        self.timer_lbl.setCustomBackgroundColor(QColor(255, 255, 255), QColor(255, 255, 255))
        style = "InfoBadge {color : black;}"
        setCustomStyleSheet(self.timer_lbl, style, style)
        self.timer_lbl.setGraphicsEffect(shadow)

        self.copyright = InfoBadge(self)
        self.copyright.setText("  by Pixel Jeff  ")
        self.copyright.hide()
        self.copyright.move(980, 142)
        self.copyright.setAlignment(Qt.AlignCenter)
        self.copyright.setCustomBackgroundColor(QColor(255, 255, 255), QColor(255, 255, 255))
        style = "InfoBadge {color : black;}"
        setCustomStyleSheet(self.copyright, style, style)
        self.copyright.setGraphicsEffect(shadow)

    def _countdown(self):

        if self.seconds:
            self.seconds -= 1
        else:
            self.timer.stop()

        self._show_time()

    def _show_time(self):

        if self.seconds:
            day = self.seconds // 86400
            hour = (self.seconds - (day * 86400)) // 3600
            minutes = (self.seconds - (day * 86400) - (hour * 3600)) // 60
            seconds = self.seconds - (day * 86400) - (hour * 3600) - (minutes * 60)
        else:
            day = 0
            hour = 0
            minutes = 0
            seconds = 0

        self.timer_lbl.setText(
            "{:02}:{:02}:{:02}:{:02}".format(int(day), int(hour), int(minutes), int(seconds))
        )

    def set_gif(self):

        self.gif = QMovie(":/image/gif.gif")
        self.gif.setScaledSize(QSize(self.w, self.h))

        self.banner_img.setMovie(self.gif)
        self.banner_img.show()
        self.copyright.show()
        self.timer_lbl.hide()

    def set_image(self, image: bytes | str):

        if image:
            self.gif.stop()

            if isinstance(image, str):
                self.banner_img.setImage(image)

            else:
                qimage = QImage()
                qimage.loadFromData(image)
                qimage = qimage.scaled(1070, 200)
                qimage = qimage.copy(0, 10, 1070, 180)
                qimage = qimage.scaled(self.w, self.h)

                self.banner_img.setImage(qimage)

            self.banner_img.show()
            self.timer_lbl.show()
            self.copyright.hide()

    def set_data(self, second: int, url: str):

        if url:
            self.banner_img.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))

        if second:
            timer = second - time.time()
            self.seconds = min(timer, 8553600)

            self._show_time()
            self.timer.start(1000)


class ShimmerEffect(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.spacing = 6
        self.roundness = 0
        self.gradient_speed = 8
        self.gradient_width = 200
        self.gradient_alpha = 150
        self.gradient_color = QColor(255, 255, 255)
        self.background_speed = 20
        self.background_color = QColor(170, 170, 170)

        self._widgets = []
        self._offset = 0
        self._alpha_factor = 125
        self._alpha_direction = True

        self._gradient_timer = QTimer(self)
        self._gradient_timer.timeout.connect(self._updateOffset)
        self._gradient_timer.start(self.gradient_speed)

        self._background_timer = QTimer(self)
        self._background_timer.timeout.connect(self._updateColor)
        self._background_timer.start(self.background_speed)

        self._path = QPainterPath()
        self._path.setFillRule(Qt.WindingFill)

        self._main_lyt = QVBoxLayout(self)
        self._main_lyt.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._main_lyt)

        self._signal_bus()

    def _getObjectRect(self):

        self._path.clear()

        for item in self._widgets:
            qrect = QRectF(item.geometry())

            if self.roundness == 0:
                roundness = item.height() / 2
            else:
                roundness = self.roundness

            self._path.addRoundedRect(
                qrect,
                roundness,
                roundness,
            )

        self._path.simplified()

    def _updateOffset(self):

        self._offset += 5

        if self._offset > self.width() + self.gradient_width:
            self._offset = -self.gradient_width

        self.update()

    def _updateColor(self):

        if self._alpha_direction == True:
            self._alpha_factor += 5
            self.background_color.setAlpha(self._alpha_factor)

            if self._alpha_factor == 250:
                self._alpha_direction = False

        else:
            self._alpha_factor -= 5
            self.background_color.setAlpha(self._alpha_factor)

            if self._alpha_factor == 125:
                self._alpha_direction = True

    def _signal_bus(self):

        signal_bus.shimmer_color.connect(
            lambda bool: (
                self.setGradientColor(themeColor())
                if bool
                else self.setGradientColor(QColor(255, 255, 255))
            )
        )

        if cfg.shimmer_color.value:
            self.gradient_color = themeColor()
        else:
            self.gradient_color = QColor(255, 255, 255)

    def setGradientSpeed(self, speed: int):

        self._gradient_timer.start(speed)

    def setGradientWidth(self, width: int):

        self.gradient_width = width

    def setGradientColor(self, color: QColor):

        self.gradient_color = color

    def setGradientAlpha(self, alpha: int):

        self.gradient_alpha = alpha

    def setBackgroundSpeed(self, speed: int):

        self._background_timer.start(speed)

    def setSpacing(self, space: int):

        self._main_lyt.setSpacing(space)

    def setRoundness(self, radius: int):

        self.roundness = radius

    def addShape(self, width: int, height: int = 18):

        shape = QLabel()
        shape.setFixedSize(width, height)

        self._main_lyt.addWidget(shape)
        self._widgets.append(shape)

    def resizeEvent(self, a0: QResizeEvent):
        super().resizeEvent(a0)

        self._getObjectRect()

    def paintEvent(self, e):

        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setRenderHints(QPainter.Antialiasing)

        painter.fillPath(self._path, QBrush(self.background_color))

        self.gradient_color.setAlpha(self.gradient_alpha)

        gradient = QLinearGradient(self._offset, 0, self._offset + self.gradient_width, 0)
        gradient.setColorAt(0, QColor(0, 0, 0, 0))
        gradient.setColorAt(0.5, self.gradient_color)
        gradient.setColorAt(1, QColor(0, 0, 0, 0))

        painter.fillPath(self._path, QBrush(gradient))


class AppLogoAnim(QGraphicsView):

    def __init__(self, parent):
        super(QGraphicsView, self).__init__(parent)

        scene = QGraphicsScene(self)
        self.setScene(scene)

        app_svg = QSvgWidget(":/vector/logo_color.svg")
        app_svg.setFixedSize(24, 24)
        app_svg.setStyleSheet("background: transparent")

        self.proxy = QGraphicsProxyWidget()
        self.proxy.setWidget(app_svg)
        self.proxy.setTransformOriginPoint(self.proxy.boundingRect().center())
        self.proxy.setAutoFillBackground(False)

        scene.addItem(self.proxy)

        self.rotate_anim = QVariantAnimation(self)
        self.rotate_anim.setStartValue(0)
        self.rotate_anim.setEndValue(360)
        self.rotate_anim.setDuration(250)
        self.rotate_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.rotate_anim.valueChanged.connect(self.rotate)

        self.scale_anim = QVariantAnimation(self)
        self.scale_anim.setStartValue(1.0)
        self.scale_anim.setEndValue(1.8)
        self.scale_anim.setDuration(250)
        self.scale_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.scale_anim.valueChanged.connect(self.scale)

    def rotate(self, rotation: float):
        self.proxy.setRotation(rotation)

    def scale(self, scale: float):
        self.proxy.setScale(scale)

    def enterEvent(self, a0: QEvent):

        if self.rotate_anim.state() != QVariantAnimation.Running:
            self.rotate_anim.setStartValue(0)
            self.rotate_anim.setEndValue(360)
            self.rotate_anim.start()
            self.rotate_anim.finished.connect(lambda: self.rotate(360))

        self.scale_anim.setDirection(QVariantAnimation.Forward)
        if self.scale_anim.state() != QVariantAnimation.Running:
            self.scale_anim.start()

    def leaveEvent(self, a0: QEvent):

        if self.rotate_anim.state() != QVariantAnimation.Running:
            self.rotate_anim.setStartValue(360)
            self.rotate_anim.setEndValue(720)
            self.rotate_anim.start()
            self.rotate_anim.finished.connect(lambda: self.rotate(0))

        self.scale_anim.setDirection(QVariantAnimation.Backward)
        if self.scale_anim.state() != QVariantAnimation.Running:
            self.scale_anim.start()


class ImageCard(QWidget):

    package_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.w = 523
        self.h = 300

        self.setFixedSize(self.w, self.h)

        self.appid = 0

        self._init_ui()
        self._info_card()
        self._main_card()
        self._key_card()
        self._temp_image_theme(cfg.theme)
        self.clear()
        self.hide()

        cfg.themeChanged.connect(self._temp_image_theme)

    def _init_ui(self):

        self.logo = ImageLabel(self)
        self.logo.setBorderRadius(16, 16, 16, 16)

        self.shimmer_effect = ShimmerEffect(self)
        self.shimmer_effect.hide()
        self.shimmer_effect.setRoundness(16)
        self.shimmer_effect.addShape(self.w, self.h)

        self.img = ImageLabel(self)
        self.img.setBorderRadius(16, 16, 16, 16)

        self.img_blur = ImageLabel(self)

        self.package_cmb = ComboBox(self)
        self.package_cmb.move(409, 10)
        self.package_cmb.setFixedWidth(105)

    def _info_card(self):

        self.type_lbl = BodyLabel(self)
        self.type_lbl.move(18, 148)
        self.type_lbl.setTextColor(QColor(255, 255, 255), QColor(255, 255, 255))
        setFont(self.type_lbl, 16, QFont.DemiBold)

        self.metacritic_icon = IconWidget(self)
        self.metacritic_icon.setIcon(":/vector/metacritic.svg")
        self.metacritic_icon.setFixedSize(24, 24)
        self.metacritic_icon.move(77, 148)

        self.metacritic_lbl = BodyLabel(self)
        self.metacritic_lbl.move(107, 148)
        self.metacritic_lbl.setTextColor(QColor(255, 255, 255), QColor(255, 255, 255))
        setFont(self.metacritic_lbl, 16, QFont.DemiBold)

    def _main_card(self):

        self.main_frm = QFrame(self)
        self.main_frm.setFixedSize(333, 86)
        self.main_frm.move(18, 180)

        main_lyt = QVBoxLayout(self.main_frm)
        main_lyt.setSizeConstraint(QHBoxLayout.SetMaximumSize)
        main_lyt.setContentsMargins(0, 0, 0, 0)
        main_lyt.setSpacing(0)
        main_lyt.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.name_lbl = SubtitleLabel(self)
        self.name_lbl.setFixedWidth(333)
        self.name_lbl.installEventFilter(ToolTipFilter(self.name_lbl))
        setFont(self.name_lbl, 19, QFont.DemiBold)

        self.developers_lbl = BodyLabel(self)
        self.developers_lbl.setFixedWidth(333)
        self.developers_lbl.installEventFilter(ToolTipFilter(self.developers_lbl))

        self.publishers_lbl = BodyLabel(self)
        self.publishers_lbl.setFixedWidth(333)
        self.publishers_lbl.installEventFilter(ToolTipFilter(self.publishers_lbl))

        main_lyt.addWidget(self.name_lbl)
        main_lyt.addSpacing(3)
        main_lyt.addWidget(self.developers_lbl)
        main_lyt.addWidget(self.publishers_lbl)

        self.discount_lbl = InfoBadge(self, InfoLevel.SUCCESS)
        self.discount_lbl.resize(80, 30)
        self.discount_lbl.move(366, 213)
        self.discount_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        setFont(self.discount_lbl, 15, QFont.Medium)
        self._add_text_shadow(self.discount_lbl, 30)

        self.base_price_lbl = InfoBadge(self, InfoLevel.INFOAMTION)
        self.base_price_lbl.resize(70, 24)
        self.base_price_lbl.move(427, 186)
        self.base_price_lbl.setAlignment(Qt.AlignCenter)
        font = QFont("Segoe UI")
        font.setPixelSize(14)
        font.setStrikeOut(True)
        font.setItalic(True)
        self.base_price_lbl.setFont(font)
        self.base_price_lbl.setCustomBackgroundColor(QColor(180, 180, 180), QColor(180, 180, 180))
        style = "InfoBadge {color : white;}"
        setCustomStyleSheet(self.base_price_lbl, style, style)
        self._add_text_shadow(self.base_price_lbl, 30)

        self.final_price_lbl = InfoBadge(self)
        self.final_price_lbl.resize(90, 30)
        self.final_price_lbl.move(417, 213)
        self.final_price_lbl.setAlignment(Qt.AlignCenter)
        setFont(self.final_price_lbl, 18, QFont.DemiBold)
        self.final_price_lbl.setCustomBackgroundColor(QColor(255, 255, 255), QColor(255, 255, 255))
        style = "InfoBadge {color : black;}"
        setCustomStyleSheet(self.final_price_lbl, style, style)
        self._add_text_shadow(self.final_price_lbl, 30)

    def _key_card(self):

        QFontDatabase.addApplicationFont(":/font/vazirmatn.ttf")
        font = QFont("Vazirmatn RD FD", 18)

        self.key_bg = InfoBadge(self)
        self.key_bg.resize(506, 35)
        self.key_bg.move(9, 256)
        self.key_bg.setCustomBackgroundColor(QColor(255, 255, 255), QColor(255, 255, 255))

        self.key_frm = QFrame(self)
        self.key_frm.setFixedSize(self.w - 36, 35)
        self.key_frm.move(18, 257)

        key_lyt = QHBoxLayout(self.key_frm)
        key_lyt.setSizeConstraint(QHBoxLayout.SetMaximumSize)
        key_lyt.setContentsMargins(0, 0, 0, 0)
        key_lyt.setAlignment(Qt.AlignCenter)

        self.key_icon = IconWidget(self)
        self.key_icon.setIcon(":/vector/key.svg")
        self.key_icon.setFixedSize(32, 32)

        self.key_count_lbl = SubtitleLabel(self)
        self.key_count_lbl.setTextColor(QColor(0, 0, 0), QColor(0, 0, 0))
        self.key_count_lbl.setContentsMargins(0, 2, 0, 0)
        self.key_count_lbl.setFont(font)

        self.key_app_logo = AppLogoAnim(self)
        self.key_app_logo.setFixedSize(62, 62)
        self.key_app_logo.move(int(self.w / 2 - 31), 242)

        self.key_price_lbl = SubtitleLabel(self)
        self.key_price_lbl.setTextColor(QColor(0, 0, 0), QColor(0, 0, 0))
        self.key_price_lbl.setContentsMargins(0, 2, 0, 0)
        self.key_price_lbl.setFont(font)

        self.key_price_icon = IconWidget(self)
        self.key_price_icon.setIcon(":/vector/key_irt_black.svg")
        self.key_price_icon.setFixedSize(23, 23)

        key_lyt.addWidget(self.key_icon)
        key_lyt.addWidget(self.key_count_lbl)
        key_lyt.addStretch(1)
        key_lyt.addWidget(self.key_price_lbl)
        key_lyt.addWidget(self.key_price_icon)

    def _temp_image_theme(self, theme: Theme):

        if theme == Theme.DARK:
            self.temp_image = ":/vector/temp_image_white.svg"

        elif Theme.LIGHT:
            self.temp_image = ":/vector/temp_image_black.svg"

        self.logo.setImage(self.temp_image)
        self.logo.scaledToWidth(self.w)

    def _set_ellipsis_text(self, text: str, label: QLabel):

        label_width = label.width()

        # Use QFontMetrics to compute text size
        font_metrics = QFontMetrics(label.font())

        # Check if text fits, if not, add ellipsis
        if font_metrics.width(text) > label_width:
            truncated_text = font_metrics.elidedText(text, Qt.ElideRight, label_width)
            label.setText(truncated_text)
            label.setToolTip(text)

        else:
            label.setText(text)
            label.setToolTip("")

    def _change_text_color(self, mode: str):

        match mode:
            case "light":
                style = "ComboBox {color: white; background-color: rgba(255, 255, 255, 0.2); border-radius: 16px;}"
                setCustomStyleSheet(self.package_cmb, style, style)
                self.name_lbl.setTextColor(QColor(255, 255, 255), QColor(255, 255, 255))
                self.developers_lbl.setTextColor(QColor(255, 255, 255), QColor(255, 255, 255))
                self.publishers_lbl.setTextColor(QColor(255, 255, 255), QColor(255, 255, 255))
                self.type_lbl.setTextColor(QColor(255, 255, 255), QColor(255, 255, 255))
                self.metacritic_lbl.setTextColor(QColor(255, 255, 255), QColor(255, 255, 255))

                self._add_text_shadow(self.type_lbl)
                self._add_text_shadow(self.metacritic_lbl)
                self._add_text_shadow(self.name_lbl)
                self._add_text_shadow(self.developers_lbl, 255)
                self._add_text_shadow(self.publishers_lbl, 255)

            case "dark":
                style = "ComboBox {color: black; background-color: rgba(255, 255, 255, 0.2); border-radius: 16px;}"
                setCustomStyleSheet(self.package_cmb, style, style)
                self.name_lbl.setTextColor(QColor(0, 0, 0), QColor(0, 0, 0))
                self.developers_lbl.setTextColor(QColor(0, 0, 0), QColor(0, 0, 0))
                self.publishers_lbl.setTextColor(QColor(0, 0, 0), QColor(0, 0, 0))
                self.type_lbl.setTextColor(QColor(0, 0, 0), QColor(0, 0, 0))
                self.metacritic_lbl.setTextColor(QColor(0, 0, 0), QColor(0, 0, 0))

                self._add_text_shadow(self.type_lbl, 150)
                self._add_text_shadow(self.metacritic_lbl, 150)
                self._add_text_shadow(self.name_lbl, 150)
                self._add_text_shadow(self.developers_lbl, 180)
                self._add_text_shadow(self.publishers_lbl, 180)

    def _add_text_shadow(self, widget: QWidget, alpha: int = 180):

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setColor(QColor(0, 0, 0, alpha))
        shadow.setBlurRadius(14)
        shadow.setOffset(0, 2)

        widget.setGraphicsEffect(shadow)

    def set_image(self, image: bytes):

        img_qimage = QImage()
        blur_qimage = QImage()
        blur_buffer = BytesIO()

        # use previous image
        if image == b"-1":
            self.img.show()
            self.img_blur.show()

        # use notfound if image not exist
        elif image == b"":
            self.img.hide()
            self.img_blur.hide()

        # if image is exist
        elif image:
            # base image
            img_qimage.loadFromData(image)

            self.img.show()
            self.img.setImage(img_qimage)
            self.img.scaledToWidth(self.w)

            # blur image
            with Image.open(BytesIO(image)) as img:
                # blur and brightness change
                contrast = ImageEnhance.Contrast(img).enhance(0.6)
                brightness = ImageEnhance.Brightness(contrast).enhance(1.4)
                blur = brightness.filter(ImageFilter.GaussianBlur(15))
                blur.save(blur_buffer, "jpeg")
                blur_qimage.loadFromData(blur_buffer.getvalue())

                # check dominant color of image to change text color
                dominant_color = ColorThief(blur_buffer).get_color()
                median_color = statistics.median_high(dominant_color)

                if median_color > 120:
                    self._change_text_color("dark")
                else:
                    self._change_text_color("light")

                # clip path the blur image
                clipped_blur_image = QImage(img.width, img.height, QImage.Format_ARGB32)
                clipped_blur_image.fill(Qt.transparent)
                painter = QPainter(clipped_blur_image)
                painter.setRenderHints(QPainter.Antialiasing)
                path = QPainterPath()
                path.setFillRule(Qt.WindingFill)

                # package card
                if self.package_cmb.text():
                    path.addRoundedRect(QRectF(482, 12, 122, 37), 20, 20)

                # metacritic card
                if self.metacritic_lbl.text():
                    path.addRoundedRect(QRectF(90, 174, 70, 30), 15, 15)

                # type card
                path.addRoundedRect(QRectF(12, 174, 70, 30), 15, 15)

                # main card
                path.addRoundedRect(QRectF(12, 210, 594, 86), 20, 20)

                path.simplified()
                painter.fillPath(path, QBrush(blur_qimage))

                if median_color > 120:
                    painter.strokePath(path, QPen(QColor(255, 255, 255, 200), 1))
                else:
                    painter.strokePath(path, QPen(QColor(255, 255, 255, 80), 1))

                painter.end()

            self.img_blur.show()
            self.img_blur.setImage(clipped_blur_image)
            self.img_blur.scaledToWidth(self.w)

        self.shimmer_effect.hide()

    def set_text_game(
        self,
        app_id: int,
        app_type: str,
        name: str,
        developers: str,
        publishers: str,
        metacritic: str,
        packages: list,
        base_price: float,
        discount: int,
        final_price: float,
        key_count: str,
        key_price: str,
    ):

        self.appid = app_id

        # app type
        if app_type == "game":
            app_type = "Game"
        elif "dlc":
            app_type = " DLC"
        self.type_lbl.setText(app_type)
        self.type_lbl.show()

        # name
        if name:
            self._set_ellipsis_text(name, self.name_lbl)

        # developers
        if developers:
            self._set_ellipsis_text(developers, self.developers_lbl)

        # publishers
        if publishers:
            self._set_ellipsis_text(publishers, self.publishers_lbl)

        self.main_frm.show()

        # price
        if discount:
            if discount < 10:
                self.discount_lbl.setText(f"   {discount}%")
            elif discount <= 99:
                self.discount_lbl.setText(f"  {discount}%")
            elif discount == 100:
                self.discount_lbl.setText(f"{discount}%")
            self.discount_lbl.show()

        locale = currency(cfg.region.value)

        if base_price:
            self.base_price_lbl.setText(f" {base_price} {locale['symbol']} ")
            self.base_price_lbl.show()

        if final_price == -1:
            self.final_price_lbl.setText("N\A")
        elif final_price == 0:
            self.final_price_lbl.setText("Free")
        elif final_price:
            if not locale["float"]:
                final_price = int(final_price)

            if locale["symbol_pos"] == "prefix":
                final_price = f"{locale['symbol']} {final_price}"
            elif "suffix":
                final_price = f"{final_price} {locale['symbol']}"

            self.final_price_lbl.setText(final_price)
        self.final_price_lbl.show()

        # metacritic
        if metacritic:
            self.metacritic_lbl.setText(metacritic)
            self.metacritic_lbl.show()
            self.metacritic_icon.show()

        # packages
        self.package_cmb.clear()
        if len(packages) > 1:
            self.type_lbl.setText(" Pack")
            self.package_cmb.addItems(packages)
            self.package_cmb.show()
            self.package_cmb.currentTextChanged.connect(
                lambda: self.package_changed.emit(self.package_cmb.currentText())
            )

        # key
        if key_price:
            self.key_price_lbl.setText(key_price)
            self.key_count_lbl.setText(key_count)
            self.key_frm.show()
        else:
            self.key_frm.hide()
        self.key_bg.show()
        self.key_app_logo.show()

    def set_text_package(
        self,
        name: str,
        base_price: float,
        discount: int,
        final_price: float,
        key_count: str,
        key_price: str,
    ):

        # app type
        self.type_lbl.setText(" Pack")
        self.type_lbl.show()

        # name
        if name:
            self._set_ellipsis_text(name, self.name_lbl)
        self.main_frm.show()

        # metacritic
        if self.metacritic_lbl.text():
            self.metacritic_lbl.show()
            self.metacritic_icon.show()

        # package
        if self.package_cmb.items:
            self.package_cmb.show()

        # price
        if discount:
            if discount < 10:
                self.discount_lbl.setText(f"   {discount}%")
            elif discount <= 99:
                self.discount_lbl.setText(f"  {discount}%")
            elif discount == 100:
                self.discount_lbl.setText(f"{discount}%")
            self.discount_lbl.show()

        locale = currency(cfg.region.value)

        if base_price:
            self.base_price_lbl.setText(f" {base_price} {locale['symbol']} ")
            self.base_price_lbl.show()

        if final_price == -1:
            self.final_price_lbl.setText("N\A")
        elif final_price == 0:
            self.final_price_lbl.setText("Free")
        elif final_price:
            if not locale["float"]:
                final_price = int(final_price)

            if locale["symbol_pos"] == "prefix":
                final_price = f"{locale['symbol']} {final_price}"
            elif "suffix":
                final_price = f"{final_price} {locale['symbol']}"

            self.final_price_lbl.setText(final_price)
        self.final_price_lbl.show()

        # key
        if key_price:
            self.key_price_lbl.setText(key_price)
            self.key_count_lbl.setText(key_count)
            self.key_frm.show()
        else:
            self.key_frm.hide()

        self.key_bg.show()
        self.key_frm.show()
        self.key_app_logo.show()

    def show_shimmer(self):

        self.hide()

        self.shimmer_effect.show()

    def get_last_appid(self):

        return str(self.appid)

    def hide(self):

        self.img.hide()
        self.img_blur.hide()

        self.package_cmb.hide()
        self.type_lbl.hide()
        self.metacritic_icon.hide()
        self.metacritic_lbl.hide()
        self.main_frm.hide()
        self.discount_lbl.hide()
        self.base_price_lbl.hide()
        self.final_price_lbl.hide()
        self.key_bg.hide()
        self.key_frm.hide()
        self.key_app_logo.hide()

    def clear(self):

        self.package_cmb.clear()
        self.type_lbl.clear()
        self.metacritic_lbl.clear()
        self.name_lbl.clear()
        self.developers_lbl.clear()
        self.publishers_lbl.clear()
        self.discount_lbl.clear()
        self.base_price_lbl.clear()
        self.final_price_lbl.clear()
        self.key_count_lbl.clear()
        self.key_price_lbl.clear()
