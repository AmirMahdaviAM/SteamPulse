import os
import sys

from PyQt5.QtCore import Qt, QTranslator
from PyQt5.QtWidgets import QApplication

from qfluentwidgets import FluentTranslator

from steampulse.common.config import cfg
from steampulse.view.main_window import MainWindow

if cfg.get(cfg.dpi_scale) == "Auto":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
else:
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpi_scale))

QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

app = QApplication(sys.argv)
app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

locale = cfg.get(cfg.language).value
fluent_translator = FluentTranslator(locale)
# steampulse_translator = QTranslator()
# steampulse_translator.load(locale, "steampulse", ".", ":/locale")

app.installTranslator(fluent_translator)
# app.installTranslator(steampulse_translator)

w = MainWindow()
w.show()

app.exec_()
