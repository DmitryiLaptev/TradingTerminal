from PyQt5.QtWidgets import QApplication

from window import MainWindow
from marketadapter import MarketAdapter

if __name__ == '__main__':
    app = QApplication([])

    marketAdapter = MarketAdapter()
    window = MainWindow()
    marketAdapter.updated.connect(window.pricesUpdated)

    app.exec()
