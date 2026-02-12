from PySide6.QtCore import Qt, QEvent, QPoint, QTimer, QRect, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QWidget, QToolButton, QVBoxLayout, QFrame, QGraphicsOpacityEffect
from PySide6.QtGui import QGuiApplication, QRegion, QPolygon

from config import (
    MARGEN_DERECHA,
    MARGEN_ARRIBA,
    PANEL_ANCHO,
    PANEL_ALTO,
    BOTON_ALTO,
    DIAGONAL,
    VELOCIDAD,
    DURACION_OPACIDAD
)

from launcher import abrir_app

from ui.botones import crear_boton_superior, crear_boton_regresar
from ui.panel import crear_panel_flotante
from ui.iconos import crear_area_iconos, poblar_grid_iconos


class CalamarDesplegable(QWidget):
    def __init__(self):
        super().__init__()

        # Ventana flotante sin bordes
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # ===== Botón superior (modular) =====
        self.btn = crear_boton_superior(self)

        #ACTIVAR ANIMACIÓN DE ZOOM EN BOTON 
        #self.btn.installEventFilter(self)  

        # ===== Fade (opacidad) para el widget principal =====
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self.opacity_effect)

        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(DURACION_OPACIDAD)
        self.fade_anim.setEasingCurve(QEasingCurve.OutCubic)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.btn)

        # Tamaño exacto de la ventana = tamaño del botón superior
        self.setFixedSize(PANEL_ANCHO, BOTON_ALTO)

        # Pegarlo arriba-derecha
        self._pegar_arriba_derecha()

        # Cerrar fácil (ESC / click derecho)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        # ===== Panel flotante (modular) =====
        self.panel, self.panel_frame, self.panel_img, pix_panel = crear_panel_flotante()

        # ===== Area de iconos + grid (modular) =====
        self.apps_area, self.grid = crear_area_iconos(self.panel_frame)

        # ===== Lista inicial (MVP) =====
        apps = [
            ("VS Code", "assets/squid.png", r"C:\Users\TU_USUARIO\Desktop\Visual Studio Code.lnk"),
            ("Premiere", "assets/squid.png", r"C:\Users\TU_USUARIO\Desktop\Adobe Premiere Pro.lnk"),
            ("OBS", "assets/squid.png", r"C:\Users\TU_USUARIO\Desktop\OBS Studio.lnk"),
            ("Roblox", "assets/squid.png", r"C:\Users\TU_USUARIO\Desktop\Roblox Player.lnk"),
        ]

        poblar_grid_iconos(
            self.apps_area,
            self.grid,
            apps,
            abrir_callback=abrir_app,
            cols=3,
            rellenar_hasta_lleno=True,
            placeholder_icon="assets/squid.png"
        )


        # ===== Botón regresar dentro del panel (modular) =====
        alto_real = self.panel_img.height()
        ancho_real = self.panel_img.width()

        self.btn_regresar = crear_boton_regresar(
            self.panel_frame,
            pix_panel,
            alto_real,
            ancho_real
        )
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

        # Click del botón superior -> mostrar/ocultar panel
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
            # CERRAR
            self.btn_regresar.hide()

            self.show()
            self._pegar_arriba_derecha()

            # Fade-in del widget principal
            self.fade_anim.stop()
            self.opacity_effect.setOpacity(0.0)
            self.fade_anim.setStartValue(0.0)
            self.fade_anim.setEndValue(1.0)
            self.fade_anim.start()

            # Cerrar: progress 1 -> 0
            self.anim.setStartValue(1.0)
            self.anim.setEndValue(0.0)
            self.anim.start()

            def _ocultar_al_terminar():
                self.panel.hide()
                try:
                    self.anim.finished.disconnect(_ocultar_al_terminar)
                except Exception:
                    pass

            self.anim.finished.connect(_ocultar_al_terminar)

        else:
            # ABRIR
            self.panel.show()
            self.panel.raise_()
            self.btn_regresar.hide()

            # Fade-out del widget principal
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

            # Abrir: progress 0 -> 1
            self.anim.setStartValue(0.0)
            self.anim.setEndValue(1.0)

            # Limpia estado antes de abrir (evita parpadeo del primer frame)
            self.apps_area.hide()
            self.apps_area.setMask(QRegion())
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
        # Posicionar el panel (mismo comportamiento que tenías)
        btn_top_left_global = self.mapToGlobal(QPoint(0, 0))
        btn_w = self.btn.width()

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
