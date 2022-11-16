from PyQt5.QtCore import pyqtSignal, QObject, QTimer
from model import Model
import requests
import json


class Prices:
    values = dict()


class MarketAdapter(QObject):
    def __init__(self):
        super().__init__()

        self.apiKeyHeader = 'X-CMC_PRO_API_KEY'
        self.apiKey = 'ecdba74a-4e91-41e7-a40a-fa47ed75007a'

        self.timer = QTimer(self)
        self.timer.start(100)  # fast initial trigger
        self.timer.timeout.connect(self.tick)

    updated = pyqtSignal(Prices)

    def tick(self):
        self.timer.stop()  # stop to restart after price updating

        p = Prices()
        try:
            r = requests.get("https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?cryptocurrency_type=coins&convert=USD&limit=5000",
                             headers={self.apiKeyHeader: self.apiKey})
            docs = json.loads(r.content)
            for doc in docs['data']:
                symbol = doc['symbol']
                price = doc['quote']['USD']['price']
                p.values[symbol] = price
            self.updated.emit(p)
        except:
            print("cannot load market data")

        self.timer.start(5 * 60 * 1000)  # 5 minutes
