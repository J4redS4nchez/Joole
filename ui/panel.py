from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QFrame
from PySide6.QtGui import QPixmap

from config import PANEL_ANCHO, PANEL_ALTO, resource_path
from panel_pintura import PanelPintura


def crear_panel_flotante():
    """
    Crea el panel flotante con su frame y su imagen (PanelPintura).
    Devuelve: panel, panel_frame, panel_img, pix_panel
    pix_panel se devuelve porque lo reutilizas para recortes (botón regresar).
    """
    panel = QWidget()
    panel.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
    panel.setAttribute(Qt.WA_TranslucentBackground, True)
    panel.resize(PANEL_ANCHO, PANEL_ALTO)

    panel_frame = QFrame(panel)
    panel_frame.setGeometry(0, 0, PANEL_ANCHO, PANEL_ALTO)
    panel_frame.setStyleSheet("""
        QFrame {
            background: transparent;
            border: none;
        }
    """)

    pix_panel = QPixmap(resource_path("assets/pintura_sombra.png")).scaled(
        PANEL_ANCHO, PANEL_ALTO,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    )

    panel_img = PanelPintura(pix_panel, panel_frame)
    panel_img.move(0, 0)

    return panel, panel_frame, panel_img, pix_panel
