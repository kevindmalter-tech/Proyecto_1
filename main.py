import sys
from PyQt5.QtWidgets import QApplication
from config import APP_STYLESHEET
from gui_login import LoginWindow


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)

    login_win = LoginWindow()
    login_win.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()