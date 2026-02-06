import sys
from PySide6.QtCore import Qt, QEvent, QPoint, QSize
from PySide6.QtWidgets import QApplication, QWidget, QToolButton, QVBoxLayout, QFrame, QLabel
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtGui import QGuiApplication, QIcon, QPixmap
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtCore import Property
from PySide6.QtGui import QPainter, QPainterPath
from PySide6.QtCore import Qt, QEvent, QPoint, QTimer
from PySide6.QtWidgets import QGraphicsOpacityEffect
import os
from PySide6.QtWidgets import QGridLayout
from PySide6.QtCore import QProcess
from PySide6.QtGui import QRegion
from PySide6.QtGui import QPolygon






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


#========= OPACIDAD ==================
DURACION_OPACIDAD = 1200



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
        # ===== Fade (opacidad) para el widget principal =====
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self.opacity_effect)

        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(DURACION_OPACIDAD)  # ajusta velocidad (ms)
        self.fade_anim.setEasingCurve(QEasingCurve.OutCubic)

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



        # ===== Contenedor de iconos (zona usable del panel) =====
        # Dejamos libre el último 25% para el botón regresar
        self.apps_area = QWidget(self.panel_frame)
        self.apps_area.setGeometry(0, 0, PANEL_ANCHO, PANEL_ALTO - BOTON_ALTO)
        self.apps_area.setAttribute(Qt.WA_TranslucentBackground, True)

        self.grid = QGridLayout(self.apps_area)
        self.grid.setContentsMargins(14, 14, 14, 14)
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(12)


        # ===== Lista inicial (MVP) =====
        # NOTA: cambia los paths por los tuyos (pueden ser .lnk o .exe)
        apps = [
            # ("Nombre", "ruta_icono_png", "ruta_app_lnk_o_exe")
            ("VS Code", "assets/squid.png", r"C:\Users\TU_USUARIO\Desktop\Visual Studio Code.lnk"),
            ("Premiere", "assets/squid.png", r"C:\Users\TU_USUARIO\Desktop\Adobe Premiere Pro.lnk"),
            ("OBS", "assets/squid.png", r"C:\Users\TU_USUARIO\Desktop\OBS Studio.lnk"),
            ("Roblox", "assets/squid.png", r"C:\Users\TU_USUARIO\Desktop\Roblox Player.lnk"),
        ]

        cols = 3  # 3 iconos por fila (puedes cambiar a 3 si quieres)

        for i, (nombre, icono, target) in enumerate(apps):
            btn_app = QToolButton(self.apps_area)
            btn_app.setCursor(Qt.PointingHandCursor)
            btn_app.setToolTip(nombre)

            btn_app.setIcon(QIcon(icono))
            btn_app.setIconSize(QSize(45, 45))
            btn_app.setFixedSize(62, 62)

            btn_app.setStyleSheet("""
                QToolButton {
                    background: rgba(0,0,0,0);
                    border: none;
                    padding: 0px;
                    margin: 0px;
                }
                QToolButton:hover {
                    background: rgba(255,255,255,25);
                    border-radius: 12px;
                }
            """)

            # Conectar click -> abrir app
            btn_app.clicked.connect(lambda checked=False, p=target: self._abrir_app(p))

            row = i // cols
            col = i % cols
            self.grid.addWidget(btn_app, row, col, Qt.AlignCenter)
        # al terminar el for (usa la variable row que ya calculas)
        self.grid.setRowStretch(row + 1, 1)





        # ===== Botón de regreso dentro del panel (último 25%) =====
        self.btn_regresar = QToolButton(self.panel_frame)
        self.btn_regresar.setCursor(Qt.PointingHandCursor)
        self.btn_regresar.setStyleSheet("""
            QToolButton { background: transparent; border: none; padding: 0px; margin: 0px; }
        """)

        # Recorte del último 25% usando EL MISMO pix del panel
        recorte_y2 = int(pix.height() * 0.75) - AJUSTE_RECORTE_ARRIBA
        if recorte_y2 < 0:
            recorte_y2 = 0
        recorte_h2 = pix.height() - recorte_y2
        pix_boton2 = pix.copy(0, recorte_y2, pix.width(), recorte_h2)

        # Ajustar al tamaño exacto del botón (igual que el de arriba)
        pix_boton2 = pix_boton2.scaled(
            PANEL_ANCHO, BOTON_ALTO,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )


        # Posición: último 25% del panel

        alto_real = self.panel_img.height()
        ancho_real = self.panel_img.width()
        y_btn = alto_real - BOTON_ALTO

        self.btn_regresar.setGeometry(0, y_btn, ancho_real, BOTON_ALTO)
        self.btn_regresar.raise_()

        self.btn_regresar.raise_()

        # Al presionar: cerrar el panel (usa tu misma función)
        self.btn_regresar.clicked.connect(self._toggle_panel)



        self.panel.hide()

        # ===== Animación del panel (despliegue tipo "pintura cae") =====
        self.anim = QPropertyAnimation(self.panel_img, b"progress")
        self.anim.setDuration(VELOCIDAD)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.valueChanged.connect(self._sync_apps_mask)




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


    def _abrir_app(self, path):
        try:
            # Esto abre .lnk, .exe, carpetas, etc. en Windows
            os.startfile(path)
        except Exception:
            # Fallback (por si algo falla)
            QProcess.startDetached(path)


    def _sync_apps_mask(self, value):
        p = float(value)

        # --- SNAP para evitar valores "casi 0" o "casi 1" que causan rastros ---
        if p <= 0.01:
            p = 0.0
        elif p >= 0.99:
            p = 1.0

        if p == 0.0:
            # Oculta y limpia máscara (evita parpadeos al final)
            self.apps_area.setMask(QRegion())  # máscara vacía
            self.apps_area.hide()
            self.apps_area.setEnabled(False)
            return
        else:
            # Asegura visible mientras hay contenido recortado
            if not self.apps_area.isVisible():
                self.apps_area.show()
            self.apps_area.setEnabled(True)

        w = self.apps_area.width()
        h = self.apps_area.height()

        visible_h = int(h * p)

        max_diagonal = int(w * DIAGONAL)
        diagonal_offset = int(max_diagonal * (1.0 - p))

        poly = QPolygon([
            QPoint(0, 0),
            QPoint(w, 0),
            QPoint(w, max(0, visible_h - diagonal_offset)),
            QPoint(max(0, w - diagonal_offset), visible_h),
            QPoint(0, visible_h),
        ])

        self.apps_area.setMask(QRegion(poly))





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

            # Fade-out de iconos (1 -> 0) mientras se cierra el panel
            self.apps_area.show()  # por si acaso



            self.btn_regresar.hide()

            self.show()
            self._pegar_arriba_derecha()

            # Fade-in del widget principal
            self.fade_anim.stop()
            self.opacity_effect.setOpacity(0.0)
            self.fade_anim.setStartValue(0.0)
            self.fade_anim.setEndValue(1.0)
            self.fade_anim.start()



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
            self.btn_regresar.hide()


            
            # Fade-out del widget principal (para que no desaparezca de golpe)
            self.fade_anim.stop()
            self.opacity_effect.setOpacity(1.0)
            self.fade_anim.setStartValue(1.0)
            self.fade_anim.setEndValue(0.0)

            def _ocultar_widget_al_terminar_fade():
                self.hide()
                try:
                    self.fade_anim.finished.disconnect(_ocultar_widget_al_terminar_fade)
                except Exception:
                    pass

            self.fade_anim.finished.connect(_ocultar_widget_al_terminar_fade)
            self.fade_anim.start()


            self.anim.setStartValue(0.0)
            self.anim.setEndValue(1.0)


            # Limpia estado antes de abrir (evita parpadeo del primer frame)
            self.apps_area.hide()
            self.apps_area.setMask(QRegion())
            # Asegura un primer frame estable ANTES de animar
            self.panel_img.progress = 0.0

            # Arrancar en el siguiente ciclo del event loop (evita parpadeo)
            QTimer.singleShot(0, self.anim.start)


            def _mostrar_boton_al_terminar():
                self.btn_regresar.show()
                self.btn_regresar.raise_()
                try:
                    self.anim.finished.disconnect(_mostrar_boton_al_terminar)
                except Exception:
                    pass

            self.anim.finished.connect(_mostrar_boton_al_terminar)



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
