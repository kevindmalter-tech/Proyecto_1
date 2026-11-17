SERVER_URL = "http://localhost:80"

APP_STYLESHEET = """
QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: #1e293b;
    background-color: #f8fafc;
}
QMainWindow, QDialog {
    background-color: #f8fafc;
}
QLabel#TitleLabel {
    font-size: 20px;
    font-weight: bold;
    color: #0f172a;
}
QLabel#SubtitleLabel {
    font-size: 13px;
    color: #64748b;
}
QLabel#SectionHeader {
    font-size: 14px;
    font-weight: bold;
    color: #1e40af;
    padding-top: 4px;
    padding-bottom: 4px;
}
QLineEdit, QComboBox {
    min-height: 28px;
    padding: 4px 10px;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    background-color: #ffffff;
    color: #0f172a;
    font-size: 13px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1.5px solid #2563eb;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0f172a;
    selection-background-color: #dbeafe;
    selection-color: #1e3a8a;
}
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    min-height: 34px;
    padding: 6px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton:pressed {
    background-color: #1e40af;
}
QPushButton#SuccessButton {
    background-color: #16a34a;
}
QPushButton#SuccessButton:hover {
    background-color: #15803d;
}
QPushButton#DangerButton {
    background-color: #dc2626;
}
QPushButton#DangerButton:hover {
    background-color: #b91c1c;
}
QPushButton#SecondaryButton {
    background-color: #475569;
}
QPushButton#SecondaryButton:hover {
    background-color: #334155;
}
QListWidget {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px;
}
QListWidget::item {
    padding: 8px;
    border-bottom: 1px solid #f1f5f9;
}
QListWidget::item:selected {
    background-color: #dbeafe;
    color: #1e3a8a;
    font-weight: bold;
    border-radius: 4px;
}
QTextEdit, QPlainTextEdit {
    background-color: #0f172a;
    color: #e2e8f0;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    border-radius: 6px;
    padding: 8px;
}
QTabWidget::pane {
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    background: #ffffff;
    padding: 12px;
}
QTabBar::tab {
    background: #e2e8f0;
    padding: 8px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
    font-weight: bold;
    color: #475569;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #2563eb;
}
"""