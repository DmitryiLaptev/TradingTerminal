from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QWidget, QPushButton, QInputDialog, QLineEdit
from PyQt5 import QtCore
import pyqtgraph as pg
from model import Model
from dbadapter import DBAdapter
import time
from datetime import datetime
import datetimeaxis

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

            item = QTableWidgetItem(h['direction'])
            #значит что ячейка нередактируемая
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.setItem(idx, 0, item)

            item = QTableWidgetItem(h['ticket'])
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.setItem(idx, 1, item)

            item = QTableWidgetItem(str(h['count']))
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.setItem(idx, 2, item)

            item = QTableWidgetItem(str(h['price']))
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.setItem(idx, 3, item)

            item = QTableWidgetItem(dt)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.setItem(idx, 4, item)

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
            item = QTableWidgetItem(k)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.setItem(idx, 0, item)
            item = QTableWidgetItem(str(model.prices[-1]['prices'][k]))
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.setItem(idx, 1, item)
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
        self.setColumnCount(7)
        #+1 т.к в первой строчке показываем баланс
        self.setRowCount(1+len(self.model.tickets))
        self.setHorizontalHeaderLabels(
            ["Ticket", "Volume", "Buy", "Sell", "Graph", "Stop loss", "Take profit"])

        self.setItem(0, 0, QTableWidgetItem("USD"))
        self.setItem(0, 1, QTableWidgetItem(str(self.model.money)))

        idx = 1

        for ticket in self.model.tickets:
            buyButton = QPushButton("Buy")
            buyButton.clicked.connect(self.closureTicket(self.execBuy, ticket))
            sellButton = QPushButton("Sell")
            sellButton.clicked.connect(
                self.closureTicket(self.execSell, ticket))
            graphButton = QPushButton("Graph")
            graphButton.clicked.connect(
                self.closureTicket(self.execGraph, ticket))

            count = self.model.records[ticket]

            item = QTableWidgetItem(ticket)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.setItem(idx, 0, item)

            item = QTableWidgetItem(str(count))
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.setItem(idx, 1, item)

            self.setCellWidget(idx, 2, buyButton)
            self.setCellWidget(idx, 3, sellButton)
            self.setCellWidget(idx, 4, graphButton)

            text = ""
            if ticket in self.model.stopLosts and self.model.stopLosts[ticket] != None:
                text = self.model.stopLosts[ticket]
            item = QLineEdit(str(text))
            item.returnPressed.connect(
                self.closureTicketWithArg(self.stopLostUpdated, ticket, item))
            self.setCellWidget(idx, 5, item)

            text = ""
            if ticket in self.model.takeProfits and self.model.takeProfits[ticket] != None:
                text = self.model.takeProfits[ticket]
            item = QLineEdit(str(text))
            item.returnPressed.connect(
                self.closureTicketWithArg(self.takeProfitUpdated, ticket, item))
            self.setCellWidget(idx, 6, item)

            idx += 1

        self.resizeColumnsToContents()

        self.historyWidget.update(self.model)
        if self.graphTicket is not None:
            self.execGraph(self.graphTicket)

    def closureTicket(self, method, ticket):
        return lambda: method(ticket)

    def closureTicketWithArg(self, method, ticket, item):
        return lambda: method(ticket, item)

    def execBuy(self, ticket):
        price = self.model.prices[-1]['prices'][ticket]
        #Вычисляем максимально доступное значение
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
        processLimits(self.model)
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
        processLimits(self.model)
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
        axis = datetimeaxis.DateAxisItem(orientation='bottom')
        axis.attachToPlotItem(self.graphWidget.getPlotItem())

        pen = pg.mkPen(color=(255, 0, 0), width=15)
        for h in self.model.history:
            if h['ticket'] != ticket:
                continue
            self.graphWidget.plot(
                [h['timestamp']], [h['price']], pen=pen, symbol='+', symbolSize=30)

    def stopLostUpdated(self, ticket, item):
        text = item.text()
        value = None
        if text != '':
            try:
                value = float(text)
            except:
                pass
        self.model.stopLosts[ticket] = value
        processLimits(self.model)
        dbAdapter.save(self.model)
        self.update()

    def takeProfitUpdated(self, ticket, item):
        text = item.text()
        value = None
        if text != '':
            try:
                value = float(text)
            except:
                pass
        self.model.takeProfits[ticket] = value
        processLimits(self.model)
        dbAdapter.save(self.model)
        self.update()


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

        processLimits(self.model)

        dbAdapter.save(self.model)

        self.pricesTable.update(self.model)
        self.portfolioTable.update()


def processLimits(model):
    for ticket in model.tickets:
        if ticket in model.stopLosts and model.stopLosts[ticket] != None:
            processStopLost(model, ticket)
        if ticket in model.takeProfits and model.takeProfits[ticket] != None:
            processTakeProfit(model, ticket)


def processStopLost(model, ticket):
    limit = model.stopLosts[ticket]
    price = model.prices[-1]['prices'][ticket]
    if price <= limit:
        value = model.records[ticket]
        if value == 0:
            return
        model.records[ticket] = 0
        model.money += value * price
        model.history.insert(
            0, {'direction': 'Stop lost', 'ticket': ticket, 'price': price, 'count': value, 'timestamp': int(time.time())})


def processTakeProfit(model, ticket):
    limit = model.takeProfits[ticket]
    price = model.prices[-1]['prices'][ticket]
    if price >= limit:
        value = model.records[ticket]
        if value == 0:
            return
        model.records[ticket] = 0
        model.money += value * price
        model.history.insert(
            0, {'direction': 'Take profit', 'ticket': ticket, 'price': price, 'count': value, 'timestamp': int(time.time())})
