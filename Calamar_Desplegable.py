import sys
from PySide6.QtCore import Qt, QEvent, QPoint
from PySide6.QtWidgets import QApplication, QWidget, QToolButton, QVBoxLayout, QFrame, QLabel
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtGui import QGuiApplication, QIcon, QPixmap
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtCore import Property
from PySide6.QtGui import QPainter, QPainterPath
from PySide6.QtCore import Qt, QEvent, QPoint, QTimer





# ===== Ajustes rápidos =====
# Margen para separarlo del borde derecho (0 = pegado)
MARGEN_DERECHA = 5
# Margen superior (0 = pegado al borde superior)
MARGEN_ARRIBA = 0

# ===== Panel (ajústalo a tu gusto) =====
PANEL_ANCHO = 250
PANEL_ALTO = 500

BOTON_ALTO = int(PANEL_ALTO * 0.25)

AJUSTE_RECORTE_ARRIBA = 18  # prueba 12, 18, 24

#========= Tamaño diagonal y velocidad===============
DIAGONAL = 0.3
VELOCIDAD = 1250

class PanelPintura(QLabel):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self._progress = 0.0
        self._pixmap = pixmap
        self.setFixedSize(pixmap.size())

    def setProgress(self, value):
        self._progress = value
        self.update()

    def getProgress(self):
        return self._progress

    progress = Property(float, getProgress, setProgress)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        visible_h = int(h * self._progress)

        max_diagonal = int(w * DIAGONAL)   # aquí puedes usar 0.1, 0.3, 0.5, etc
        diagonal_offset = int(max_diagonal * (1.0 - self._progress))


        path = QPainterPath()
        path.moveTo(0, 0)
        path.lineTo(w, 0)
        path.lineTo(w, visible_h)
        path.lineTo(diagonal_offset, visible_h)

        w = self.width()
        h = self.height()
        visible_h = int(h * self._progress)

        max_diagonal = int(w * DIAGONAL)  # aquí controlas inclinación máxima
        diagonal_offset = int(max_diagonal * (1.0 - self._progress))  # se va a 0 al final

        path = QPainterPath()
        path.moveTo(0, 0)
        path.lineTo(w, 0)

        # Borde derecho con diagonal
        path.lineTo(w, max(0, visible_h - diagonal_offset))
        path.lineTo(max(0, w - diagonal_offset), visible_h)

        # Base y lado izquierdo rectos
        path.lineTo(0, visible_h)
        path.closeSubpath()

        path.closeSubpath()

        painter.setClipPath(path)
        painter.drawPixmap(0, 0, self._pixmap)




class CalamarDesplegable(QWidget):
    def __init__(self):
        super().__init__()

        # Ventana flotante sin bordes
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Botón círculo (después será el calamar)
        self.btn = QToolButton()
        self.btn.setFixedSize(PANEL_ANCHO, BOTON_ALTO)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setToolTip("Pintura")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.btn)

        # Tamaño exacto de la ventana = tamaño del círculo
        self.setFixedSize(PANEL_ANCHO, BOTON_ALTO)

        # Usar imagen del calamar
        pix_panel = QPixmap("assets/pintura_sombra.png").scaled(
            PANEL_ANCHO, PANEL_ALTO,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        # Recortar el último 25% (parte inferior)
        recorte_y = int(pix_panel.height() * 0.75) - AJUSTE_RECORTE_ARRIBA
        if recorte_y < 0:
            recorte_y = 0

        recorte_h = pix_panel.height() - recorte_y
        pix_boton = pix_panel.copy(0, recorte_y, pix_panel.width(), recorte_h)


        # Ajustar el recorte al tamaño exacto del botón (llenando el ancho)
        pix_boton = pix_boton.scaled(
            PANEL_ANCHO, BOTON_ALTO,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )

        self.btn.setIcon(QIcon(pix_boton))


        # Tamaños para el efecto hover (zoom)
        self.icon_normal = 40
        self.icon_hover = 48  # súbelo/bájalo a tu gusto (46, 48, 50)

        self.btn.setIconSize(self.btn.size())  # inicia con el tamaño del botón
        self.btn.installEventFilter(self)      # para detectar enter/leave

        self.btn.setIconSize(self.btn.size())

        # Quitar fondo y borde del botón
        self.btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)

        # Pegarlo arriba-derecha
        self._pegar_arriba_derecha()

        # Cerrar fácil (ESC / click derecho)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        # ===== Panel flotante (debajo del calamar) =====
        self.panel = QWidget()
        self.panel.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.panel.setAttribute(Qt.WA_TranslucentBackground, True)
        self.panel.resize(PANEL_ANCHO, PANEL_ALTO)

        self.panel_frame = QFrame(self.panel)
        self.panel_frame.setGeometry(0, 0, PANEL_ANCHO, PANEL_ALTO)
        self.panel_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)

        # Imagen del panel
        pix = QPixmap("assets/pintura_sombra.png").scaled(
            PANEL_ANCHO, PANEL_ALTO,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.panel_img = PanelPintura(pix, self.panel_frame)
        self.panel_img.move(0, 0)



        self.panel.hide()

        # ===== Animación del panel (despliegue tipo "pintura cae") =====
        self.anim = QPropertyAnimation(self.panel_img, b"progress")
        self.anim.setDuration(VELOCIDAD)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)


        # Para evitar que se pueda spamear el click mientras anima
        self._animando = False
        self.anim.finished.connect(lambda: setattr(self, "_animando", False))



        # Click del calamar -> mostrar/ocultar panel
        self.btn.clicked.connect(self._toggle_panel)

    def _pegar_arriba_derecha(self):
        screen = QGuiApplication.primaryScreen()
        geo = screen.geometry()

        # Posición horizontal: 3/4 del ancho de la pantalla
        x = geo.x() + int(geo.width() * 0.85) - (self.width() // 2)

        # Posición vertical: arriba
        y = geo.y() + MARGEN_ARRIBA

        self.move(x, y)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.close()

    def eventFilter(self, obj, event):
        if obj is self.btn:
            if event.type() == QEvent.Type.Enter:
                # Zoom al pasar el mouse
                self.btn.setFixedSize(PANEL_ANCHO, BOTON_ALTO + 6)
                self.setFixedSize(PANEL_ANCHO, BOTON_ALTO + 6)
                self.btn.setIconSize(self.btn.size())
                self._pegar_arriba_derecha()
                return False

            elif event.type() == QEvent.Type.Leave:
                # Regresar al tamaño normal
                self.btn.setFixedSize(PANEL_ANCHO, BOTON_ALTO)
                self.setFixedSize(PANEL_ANCHO, BOTON_ALTO)
                self.btn.setIconSize(self.btn.size())
                self._pegar_arriba_derecha()
                return False

        return super().eventFilter(obj, event)

    # ====== NUEVO: lógica del panel ======
    def _toggle_panel(self):
        if self._animando:
            return

        self._posicionar_panel()  # asegura x/y bien antes de animar

        x = self.panel.x()
        y = self.panel.y()

        # Estado "cerrado": solo se ve el área del botón (25%)
        inicio = QRect(x, y, PANEL_ANCHO, BOTON_ALTO)
        # Estado "abierto": panel completo
        fin = QRect(x, y, PANEL_ANCHO, PANEL_ALTO)

        self._animando = True
        self.anim.stop()

        if self.panel.isVisible():


            progress_inicio = BOTON_ALTO / PANEL_ALTO

            # Cerrar: de completo -> a BOTON_ALTO
            self.anim.setStartValue(1.0)
            self.anim.setEndValue(0.0)
            self.anim.start()


            # Ocultar al final (si no, queda una tirita)
            def _ocultar_al_terminar():
                self.panel.hide()
                try:
                    self.anim.finished.disconnect(_ocultar_al_terminar)
                except Exception:
                    pass

            self.anim.finished.connect(_ocultar_al_terminar)

        else:

            progress_inicio = BOTON_ALTO / PANEL_ALTO

            # Abrir: mostrar primero en BOTON_ALTO y luego extender
            self.panel.show()
            self.panel.raise_()

            # Asegura un primer frame estable ANTES de animar
            self.panel_img.progress = 0.0
            
            # Ocultar el botón/ventana principal para que no quede detrás
            self.hide()

            self.anim.setStartValue(0.0)
            self.anim.setEndValue(1.0)

            # Arrancar en el siguiente ciclo del event loop (evita parpadeo)
            QTimer.singleShot(0, self.anim.start)



    def _posicionar_panel(self):
        # Posicionar el panel justo debajo del botón (centrado con el calamar)
        btn_top_left_global = self.mapToGlobal(QPoint(0, 0))
        btn_w = self.btn.width()
        btn_h = self.btn.height()

        x = btn_top_left_global.x() + (btn_w // 2) - (PANEL_ANCHO // 2)
        y = 0 + MARGEN_ARRIBA

        self.panel.move(x, y)

    def moveEvent(self, event):
        super().moveEvent(event)
        if self.panel.isVisible():
            self._posicionar_panel()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.panel.isVisible():
            self._posicionar_panel()

    def closeEvent(self, event):
        if self.panel.isVisible():
            self.panel.hide()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    w = CalamarDesplegable()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
