import os
from PySide6.QtCore import QProcess

def abrir_app(path: str):
    if not path:
        return

    try:
        # Si es .lnk, abrirlo tal cual (respeta "Start in" y argumentos del acceso directo)
        if path.lower().endswith(".lnk"):
            os.startfile(path)
            return

        # Si es .exe, arrancarlo con working directory = carpeta del exe
        if path.lower().endswith(".exe"):
            workdir = os.path.dirname(path)
            QProcess.startDetached(path, [], workdir)
            return

        # Otros archivos
        os.startfile(path)

    except Exception:
        # Fallback
        try:
            os.startfile(path)
        except Exception:
            pass
