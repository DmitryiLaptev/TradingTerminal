class Model:
    def __init__(self):
        self.tickets = ["BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOGE", "DOT", "AVAX",
                        "TRX", "MATIC", "LTC", "NEAR", "BCH", "XLM", "ALGO", "ATOM", "FLOW", "ETC"]

        self.money = 100000

        self.prices = []

        self.records = {}

        self.history = []

        self.stopLosts = {}

        self.takeProfits = {}
