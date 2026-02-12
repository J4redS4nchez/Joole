from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolButton, QWidget
from PySide6.QtGui import QIcon, QPixmap

from config import PANEL_ANCHO, PANEL_ALTO, BOTON_ALTO, AJUSTE_RECORTE_ARRIBA


def crear_boton_superior(parent: QWidget):
    """
    Crea el botón superior con el recorte del último 25% del panel.
    Devuelve: btn (QToolButton)
    """
    btn = QToolButton(parent)
    btn.setFixedSize(PANEL_ANCHO, BOTON_ALTO)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setToolTip("Pintura")

    pix_panel = QPixmap("assets/pintura_sombra.png").scaled(
        PANEL_ANCHO, PANEL_ALTO,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    )

    recorte_y = int(pix_panel.height() * 0.75) - AJUSTE_RECORTE_ARRIBA
    if recorte_y < 0:
        recorte_y = 0

    recorte_h = pix_panel.height() - recorte_y
    pix_boton = pix_panel.copy(0, recorte_y, pix_panel.width(), recorte_h)

    pix_boton = pix_boton.scaled(
        PANEL_ANCHO, BOTON_ALTO,
        Qt.KeepAspectRatioByExpanding,
        Qt.SmoothTransformation
    )

    btn.setIcon(QIcon(pix_boton))
    btn.setIconSize(btn.size())

    btn.setStyleSheet("""
        QToolButton {
            background: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
        }
    """)

    return btn


def crear_boton_regresar(panel_frame: QWidget, pix_panel: QPixmap, alto_real: int, ancho_real: int):
    """
    Crea el botón regresar dentro del panel (último 25%).
    Usa pix_panel (la misma del panel) para recortar.
    Devuelve: btn_regresar
    """
    btn_regresar = QToolButton(panel_frame)
    btn_regresar.setCursor(Qt.PointingHandCursor)
    btn_regresar.setStyleSheet("""
        QToolButton { background: transparent; border: none; padding: 0px; margin: 0px; }
    """)

    recorte_y2 = int(pix_panel.height() * 0.75) - AJUSTE_RECORTE_ARRIBA
    if recorte_y2 < 0:
        recorte_y2 = 0

    recorte_h2 = pix_panel.height() - recorte_y2
    pix_boton2 = pix_panel.copy(0, recorte_y2, pix_panel.width(), recorte_h2)

    pix_boton2 = pix_boton2.scaled(
        PANEL_ANCHO, BOTON_ALTO,
        Qt.KeepAspectRatioByExpanding,
        Qt.SmoothTransformation
    )

    GAP = 10  # debe ser el mismo que en crear_area_iconos
    y_btn = alto_real - BOTON_ALTO + GAP
    btn_regresar.setGeometry(0, y_btn, ancho_real, BOTON_ALTO - GAP)

    btn_regresar.raise_()

    return btn_regresar
