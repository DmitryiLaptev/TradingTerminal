import json


class DBAdapter:
    def __init__(self):
        self.databaseName = "ccex.db"

    def save(self, model):
        f = open(self.databaseName, "w")
        f.write(json.dumps(model.money) + "\n")
        f.write(json.dumps(model.prices) + "\n")
        f.write(json.dumps(model.records) + "\n")
        f.write(json.dumps(model.history) + "\n")
        f.close()

    def load(self, model):
        try:
            f = open(self.databaseName, "r")
            line = f.readline()
            if not line:
                return
            model.money = json.loads(line)
            line = f.readline()
            if not line:
                return
            model.prices = json.loads(line)
            line = f.readline()
            if not line:
                return
            model.records = json.loads(line)
            line = f.readline()
            if not line:
                return
            model.history = json.loads(line)
            f.close()
        except:
            pass
