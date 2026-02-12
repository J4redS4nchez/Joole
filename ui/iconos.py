from PySide6.QtCore import Qt, QSize, QEvent, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QWidget, QToolButton, QGridLayout
from PySide6.QtGui import QIcon

from config import PANEL_ANCHO, PANEL_ALTO, BOTON_ALTO
from PySide6.QtCore import QTimer, QPoint
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPainter, QPainterPath, QColor




class AppIconButton(QToolButton):
    def __init__(self, parent=None, base_icon=QSize(45,45), hover_icon=QSize(52,52),
                 tip_text: str = "", is_disabled_tip: bool = False, tip: "HoverTip" = None):
        super().__init__(parent)
        self.base_icon = base_icon
        self.hover_icon = hover_icon

        # --- tooltip custom ---
        self._tip_text = tip_text
        self._is_disabled_tip = is_disabled_tip
        self._tip = tip  # instancia compartida

        self.setMouseTracking(True)

    def enterEvent(self, event):
        # tu animación de hover (si ya la tenías) se queda
        try:
            self.setIconSize(self.hover_icon)
        except Exception:
            pass

        # tooltip custom
        if self._tip and self._tip_text:
            global_pos = self.mapToGlobal(self.rect().center())
            self._tip.show_text(self._tip_text, global_pos, is_disabled=self._is_disabled_tip)

        super().enterEvent(event)

    def leaveEvent(self, event):
        try:
            self.setIconSize(self.base_icon)
        except Exception:
            pass

        if self._tip:
            self._tip.hide()

        super().leaveEvent(event)



class HoverTip(QLabel):
    """Tooltip flotante custom, pintado manualmente para evitar transparencia en Windows."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setWindowFlag(Qt.WindowTransparentForInput, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._bg = QColor(0, 0, 0, 220)
        self._fg = QColor(255, 213, 74)  # amarillo
        self._radius = 12
        self._pad_x = 10
        self._pad_y = 6

        self.setAlignment(Qt.AlignCenter)
        self.hide()

    def set_colors(self, bg: QColor, fg: QColor):
        self._bg = bg
        self._fg = fg
        self.update()

    def show_text(self, text: str, global_pos: QPoint, is_disabled: bool = False):
        # Colores según estado
        if is_disabled:
            self.set_colors(QColor(0, 0, 0, 220), QColor(4, 217, 255))  # rojo
        else:
            self.set_colors(QColor(0, 0, 0, 220), QColor(255, 213, 74))  # amarillo

        self.setText(text)
        self.adjustSize()

        # Ajuste extra por padding (porque QLabel no sabe de nuestro padding pintado)
        self.resize(self.width() + self._pad_x * 2, self.height() + self._pad_y * 2)

        # Posición: arriba del cursor
        x = global_pos.x() + 18
        y = global_pos.y() - self.height() - 26
        self.move(x, y)

        self.show()
        self.raise_()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Fondo redondeado
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(rect, self._radius, self._radius)
        painter.fillPath(path, self._bg)

        # Texto
        painter.setPen(self._fg)
        painter.drawText(
            rect.adjusted(self._pad_x, self._pad_y, -self._pad_x, -self._pad_y),
            Qt.AlignCenter,
            self.text()
        )




def crear_area_iconos(panel_frame: QWidget):
    """
    Crea la zona usable de iconos (apps_area) y el grid layout.
    NO conecta lógica de abrir apps: eso se hace afuera.
    Devuelve: apps_area, grid
    """
    apps_area = QWidget(panel_frame)
    GAP = 10  # px de separación para que el botón no tape iconos
    apps_area.setGeometry(0, 0, PANEL_ANCHO, PANEL_ALTO - BOTON_ALTO - GAP)

    apps_area.setAttribute(Qt.WA_TranslucentBackground, True)

    grid = QGridLayout(apps_area)
    grid.setContentsMargins(14, 14, 14, 14)
    grid.setHorizontalSpacing(12)
    grid.setVerticalSpacing(12)

    grid.setAlignment(Qt.AlignTop | Qt.AlignHCenter)



    apps_area.hover_tip = HoverTip(apps_area)

    return apps_area, grid


def poblar_grid_iconos(apps_area: QWidget, grid: QGridLayout, apps: list, abrir_callback, cols: int = 3,
                      rellenar_hasta_lleno: bool = True, placeholder_icon: str = "assets/squid.png"):
    """
    Crea y agrega botones al grid.
    apps = [(nombre, icono_path, target_path), ...]
    abrir_callback = función(path) que abre la app.

    - NO deja que se salgan del 3er cuarto (apps_area ya mide PANEL_ALTO - BOTON_ALTO)
    - Mantiene 3 iconos por fila (cols=3)
    - Si faltan, rellena visualmente hasta llenar el espacio (placeholders deshabilitados)
    """

    # ---- Capacidad máxima según el tamaño real del área (3/4 del panel) ----
    # NOTA: estos valores deben coincidir con los que usas en tu botón
    BTN_W = 62
    BTN_H = 62

    m = grid.contentsMargins()
    top = m.top()
    bottom = m.bottom()
    left = m.left()
    right = m.right()

    v_spacing = grid.verticalSpacing()
    h_spacing = grid.horizontalSpacing()

    usable_h = apps_area.height() - (top + bottom)
    usable_w = apps_area.width() - (left + right)

    # Cuántas columnas CABEN (pero tú quieres fijo en 3; esto solo protege)
    max_cols_fit = max(1, (usable_w + h_spacing) // (BTN_W + h_spacing))
    cols = min(cols, int(max_cols_fit))

    # Cuántas filas CABEN
    max_rows_fit = max(1, (usable_h + v_spacing) // (BTN_H + v_spacing))

    capacidad = int(max_rows_fit * cols)

    # ---- Lista final: recorta si sobran, o rellena si faltan ----
    apps_final = list(apps[:capacidad])

    if rellenar_hasta_lleno and len(apps_final) < capacidad:
        faltan = capacidad - len(apps_final)
        for i in range(faltan):
            apps_final.append((f"Slot {len(apps_final)+1}", placeholder_icon, None))

        # ---- Poblado del grid ----
    row = 0
    for i, (nombre, icono, target) in enumerate(apps_final):

        is_placeholder = (target is None)
        tip_text = "Desabilitado" if is_placeholder else nombre

        btn_app = AppIconButton(
            apps_area,
            base_icon=QSize(45,45),
            hover_icon=QSize(52,52),
            tip_text=tip_text,
            is_disabled_tip=is_placeholder,
            tip=apps_area.hover_tip
        )

        btn_app.setFocusPolicy(Qt.NoFocus)
        btn_app.setIcon(QIcon(icono))
        btn_app.setIconSize(QSize(45, 45))
        btn_app.setFixedSize(BTN_W, BTN_H)

        btn_app.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QToolButton:hover {
                background: transparent;
                border: none;
            }
            QToolButton:pressed {
                background: transparent;
                border: none;
            }
        """)

        # Si es placeholder, lo deshabilitamos (se verá gris)
        if is_placeholder:
            btn_app.setEnabled(False)
            btn_app.setCursor(Qt.ArrowCursor)
            btn_app.setStyleSheet(btn_app.styleSheet() + """
                QToolButton:disabled {
                    opacity: 0.35;
                }
            """)
        else:
            btn_app.setEnabled(True)
            btn_app.setCursor(Qt.PointingHandCursor)
            btn_app.clicked.connect(lambda checked=False, p=target: abrir_callback(p))

        row = i // cols
        col = i % cols
        grid.addWidget(btn_app, row, col, Qt.AlignCenter)
