import sys
from PySide6.QtWidgets import QApplication
from app.database.repository import Repository
from app.ui.main_window import MainWindow
from app.ui.styles import STYLESHEET
def main():
    app=QApplication(sys.argv);app.setApplicationName("JASS ECHO");app.setStyle("Fusion");app.setStyleSheet(STYLESHEET)
    repo=Repository();window=MainWindow(repo);window.show()
    result=app.exec();repo.close();return result
