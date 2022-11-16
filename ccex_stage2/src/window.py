from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QWidget, QPushButton, QInputDialog
import pyqtgraph as pg
from model import Model
from dbadapter import DBAdapter
import time
from datetime import datetime
import json

dbAdapter = DBAdapter()


class HistoryhWidget(QTableWidget):
    def __init__(self, parent):
        super().__init__(parent)

    def update(self, model):
        self.setColumnCount(5)
        self.setRowCount(len(model.history))
        self.setHorizontalHeaderLabels(
            ["Dir", "Ticket", "Volume", "Price", "Time"])

        idx = 0
        for h in model.history:
            dt = datetime.fromtimestamp(
                h['timestamp']).isoformat().replace('T', ' ')
            self.setItem(idx, 0, QTableWidgetItem(h['direction']))
            self.setItem(idx, 1, QTableWidgetItem(h['ticket']))
            self.setItem(idx, 2, QTableWidgetItem(str(h['count'])))
            self.setItem(idx, 3, QTableWidgetItem(str(h['price'])))
            self.setItem(idx, 4, QTableWidgetItem(dt))
            idx += 1

        self.resizeColumnsToContents()


class PricesTable(QTableWidget):
    def __init__(self, parent):
        super().__init__(parent)

    def update(self, model):
        self.setColumnCount(2)
        self.setRowCount(len(model.tickets))
        self.setHorizontalHeaderLabels(["Ticket", "Price"])

        idx = 0
        for k in model.tickets:
            self.setItem(idx, 0, QTableWidgetItem(k))
            self.setItem(idx, 1, QTableWidgetItem(
                str(model.prices[-1]['prices'][k])))
            idx += 1

        self.resizeColumnsToContents()


class PortfolioTable(QTableWidget):
    def __init__(self, parent, model, historyWidget, graphWidget):
        super().__init__(parent)
        self.model = model
        self.historyWidget = historyWidget
        self.graphWidget = graphWidget
        self.graphTicket = None

    def update(self):
        self.setColumnCount(5)
        self.setRowCount(1+len(self.model.tickets))
        self.setHorizontalHeaderLabels(
            ["Ticket", "Volume", "Buy", "Sell", "Graph"])

        self.setItem(0, 0, QTableWidgetItem("USD"))
        self.setItem(0, 1, QTableWidgetItem(str(self.model.money)))

        idx = 1
        for ticket in self.model.tickets:
            buyButton = QPushButton("Buy")
            buyButton.clicked.connect(self.closure(self.execBuy, ticket))
            sellButton = QPushButton("Sell")
            sellButton.clicked.connect(self.closure(self.execSell, ticket))
            graphButton = QPushButton("Graph")
            graphButton.clicked.connect(self.closure(self.execGraph, ticket))

            self.setItem(idx, 0, QTableWidgetItem(ticket))
            self.setItem(idx, 1, QTableWidgetItem(
                str(self.model.records[ticket])))
            self.setCellWidget(idx, 2, buyButton)
            self.setCellWidget(idx, 3, sellButton)
            self.setCellWidget(idx, 4, graphButton)
            idx += 1

        self.resizeColumnsToContents()

        self.historyWidget.update(self.model)
        if self.graphTicket is not None:
            self.execGraph(self.graphTicket)

    def closure(self, method, ticket):
        return lambda: method(ticket)

    def execBuy(self, ticket):
        price = self.model.prices[-1]['prices'][ticket]
        maxValue = self.model.money / price
        value, ok = QInputDialog.getDouble(
            self, "Amount", "Enter amount", 0, 0, maxValue, 4)
        if not ok:
            return
        value = min(value, maxValue)
        if value == 0:
            return
        self.model.records[ticket] += value
        self.model.money -= value * price
        self.model.history.insert(
            0, {'direction': 'Buy', 'ticket': ticket, 'price': price, 'count': value, 'timestamp': int(time.time())})
        dbAdapter.save(self.model)
        self.update()

    def execSell(self, ticket):
        price = self.model.prices[-1]['prices'][ticket]
        maxValue = self.model.records[ticket]
        value, ok = QInputDialog.getDouble(
            self, "Amount", "Enter amount", 0, 0, maxValue, 4)
        if not ok:
            return
        value = min(value, maxValue)
        if value == 0:
            return
        self.model.records[ticket] -= value
        self.model.money += value * price
        self.model.history.insert(
            0, {'direction': 'Sell', 'ticket': ticket, 'price': price, 'count': value, 'timestamp': int(time.time())})
        dbAdapter.save(self.model)
        self.update()

    def execGraph(self, ticket):
        self.graphTicket = ticket

        ts = []
        ps = []
        for p in self.model.prices:
            ts.append(p['time'])
            ps.append(p['prices'][ticket])
        self.graphWidget.clear()
        self.graphWidget.setTitle(ticket)
        self.graphWidget.plot(ts, ps)

        pen = pg.mkPen(color=(255, 0, 0), width=15)
        for h in self.model.history:
            if h['ticket'] != ticket:
                continue
            if h['direction'] == 'Buy':
                self.graphWidget.plot(
                    [h['timestamp']], [h['price']], pen=pen, symbol='+', symbolSize=30)
            else:
                self.graphWidget.plot(
                    [h['timestamp']], [h['price']], pen=pen, symbol='+', symbolSize=30)


class MainWindow(QMainWindow):

    model = Model()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CryptoCurrencies Exchange")
        self.resize(1280, 800)
        self.makeLayout()
        self.show()

        dbAdapter.load(self.model)

    def makeLayout(self):
        widget = QWidget()
        hbox = QHBoxLayout(widget)

        leftVBox = QVBoxLayout()
        rightVBox = QVBoxLayout()

        self.graphWidget = pg.PlotWidget()
        self.graphWidget.setBackground("w")

        self.historyWidget = HistoryhWidget(self)

        self.pricesTable = PricesTable(self)

        self.portfolioTable = PortfolioTable(
            self, self.model, self.historyWidget, self.graphWidget)

        leftVBox.addWidget(QLabel("Portfolio"))
        leftVBox.addWidget(self.portfolioTable)
        leftVBox.addWidget(QLabel("Prices"))
        leftVBox.addWidget(self.pricesTable)

        rightVBox.addWidget(QLabel("Graph"))
        rightVBox.addWidget(self.graphWidget)
        rightVBox.addWidget(QLabel("History"))
        rightVBox.addWidget(self.historyWidget)

        hbox.addLayout(leftVBox)
        hbox.addLayout(rightVBox)

        self.setCentralWidget(widget)

    def pricesUpdated(self, prices):
        now = int(time.time())
        slice = {'time': now, 'prices': {}}
        for k in prices.values:
            if k in self.model.tickets:
                slice['prices'][k] = prices.values[k]
        self.model.prices.append(slice)

        dbAdapter.save(self.model)

        self.pricesTable.update(self.model)
        self.portfolioTable.update()
