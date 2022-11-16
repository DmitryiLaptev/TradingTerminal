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
        f.write(json.dumps(model.stopLosts) + "\n")
        f.write(json.dumps(model.takeProfits) + "\n")
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
            line = f.readline()
            if not line:
                return
            model.stopLosts = json.loads(line)
            line = f.readline()
            if not line:
                return
            model.takeProfits = json.loads(line)
            f.close()
        except Exception as ex:
            print("load data failure -", ex)
            pass

        for t in model.tickets:
            if t not in model.records:
                model.records[t] = 0.0
