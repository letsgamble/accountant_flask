from flask import Flask
from flask import render_template
import json
import collections
import functools
import operator

app = Flask(__name__)


class Manager:
    def __init__(self):
        self.file_path = 'in.json'
        self.save_path = ''
        self.stan_konta = 0
        self.actions = {}
        self.data = []
        self._dict = {}
        self.magazyn = []
        self.new_magazyn = []

    def json_file_loader(self):
        with open(self.file_path, 'r') as f:
            self.data = json.load(f)

    def json_file_handler(self):
        for line in self.data:
            for key, keyval in line.items():
                if keyval == "saldo":
                    self.stan_konta += line["value"]
                if keyval == "zakup":
                    self.stan_konta -= line["price"] * line["qty"]
                    zakup_dict = {line["item"]: line["qty"]}
                    self.magazyn.append(zakup_dict)
                    self.new_magazyn = dict(functools.reduce(operator.add, map(collections.Counter, self.magazyn)))
                if keyval == "sprzedaz":
                    if line['item'] in self.new_magazyn:
                        self.stan_konta += line["price"] * line["qty"]
                        sprzedaz_dict = {line["item"]: -line["qty"]}
                        self.magazyn.append(sprzedaz_dict)
                        self.new_magazyn = dict(functools.reduce(operator.add, map(collections.Counter, self.magazyn)))
                    else:
                        print('Cannot sell the product, which does not exist in the warehouse')


@app.route('/')
def main():
    stan_konta = manager.stan_konta
    magazyn = manager.new_magazyn
    return render_template('index.html', content=stan_konta, content2=magazyn)


manager = Manager()
manager.json_file_loader()
manager.json_file_handler()
