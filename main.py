import os


def preload_ml_runtime() -> None:
    """
    Work around Windows DLL init conflicts between Qt and torch:
    import torch/ultralytics before creating QApplication.
    """
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    try:
        import torch  # noqa: F401
        from ultralytics import YOLO  # noqa: F401
    except Exception:
        # Keep UI launchable; model load will surface detailed error in-app.
        pass


def main():
    preload_ml_runtime()
    from PyQt5 import QtCore, QtGui, QtWidgets
    from app.main_window import MainWindow

    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")
    font_db = QtGui.QFontDatabase()
    font_family = "Microsoft YaHei" if "Microsoft YaHei" in font_db.families() else "Segoe UI"
    app_font = QtGui.QFont(font_family, 10)
    if hasattr(QtGui.QFont, "PreferFullHinting"):
        app_font.setHintingPreference(QtGui.QFont.PreferFullHinting)
    if hasattr(QtGui.QFont, "PreferQuality"):
        app_font.setStyleStrategy(QtGui.QFont.PreferQuality)
    app.setFont(app_font)
    window = MainWindow()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
