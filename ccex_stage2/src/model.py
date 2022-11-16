class Model:
    def __init__(self):
        self.tickets = ['BTC', 'ETH', 'SOL', 'BNB']

        self.money = 100000

        # list of objects {timestamp, map: COIN -> price}
        self.prices = []

        # map COIN -> count
        self.records = {}

        # list of records {'B'|'S', COIN, count, timestamp}
        self.history = []

        for k in self.tickets:
            if k not in self.records:
                self.records[k] = 0
