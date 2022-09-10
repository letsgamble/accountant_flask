from flask import Flask
from flask import render_template
from flask import request
import json
import collections
import functools
import operator

app = Flask(__name__)


class Manager:
    def __init__(self):
        self.file_path = 'in.json'
        self.stan_konta = 0
        self.data = []
        self._dict = {}
        self.magazyn = []
        self.new_magazyn = []

    def json_file_loader(self):
        with open(self.file_path, 'r') as f:
            self.data = json.load(f)

    def reset_handler(self):
        self.stan_konta = 0
        self.data = []
        self.magazyn = []
        self.new_magazyn = []

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
                        sprzedaz_dict = {line["item"]: - line["qty"]}
                        self.magazyn.append(sprzedaz_dict)
                        self.new_magazyn = dict(functools.reduce(operator.add, map(collections.Counter, self.magazyn)))

    def json_file_saver(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)


manager = Manager()

manager.json_file_loader()
manager.json_file_handler()


@app.route('/')
def main():
    stan_konta = manager.stan_konta
    magazyn = manager.new_magazyn
    return render_template('index.html', content=stan_konta, content2=magazyn)


@app.route('/zakup')
def zakup():
    stan_konta = manager.stan_konta
    magazyn = manager.new_magazyn
    item = request.args.get('nazwa')
    price = request.args.get('cena')
    qty = request.args.get('liczba')
    if not (item or price or qty) == '':
        price = int(price)
        qty = int(qty)
        if price*qty <= stan_konta:
            manager.data.append({'action': 'zakup', 'item': item, 'price': price, 'qty': qty})
            manager.json_file_saver()
            manager.reset_handler()
            manager.json_file_loader()
            manager.json_file_handler()
            stan_konta = manager.stan_konta
            magazyn = manager.new_magazyn
            return render_template('index.html', content=stan_konta, content2=magazyn)
        else:
            return render_template('index.html', content=stan_konta, content2=magazyn, content3='Not enough money')
    else:
        return render_template('index.html', content=stan_konta, content2=magazyn,
                               content3='Please fill the fields properly')


@app.route('/sprzedaz')
def sprzedaz():
    stan_konta = manager.stan_konta
    magazyn = manager.new_magazyn
    item = request.args.get('nazwa')
    price = request.args.get('cena')
    qty = request.args.get('liczba')
    if not (item or price or qty) == '':
        price = int(price)
        qty = int(qty)
        if item in manager.new_magazyn and qty <= manager.new_magazyn[item]:
            _dict = {
                "action": "sprzedaz",
                "item": item,
                "price": price,
                "qty": qty
            }
            manager.data.append(_dict)
            manager.json_file_saver()
            manager.reset_handler()
            manager.json_file_loader()
            manager.json_file_handler()
            stan_konta = manager.stan_konta
            magazyn = manager.new_magazyn
            return render_template('index.html', content=stan_konta, content2=magazyn)
        else:
            return render_template('index.html', content=stan_konta, content2=magazyn,
                                   content4='Item does not exist in the database, or there is not enough')
    else:
        return render_template('index.html', content=stan_konta, content2=magazyn,
                               content4='Please fill the fields properly')


@app.route('/saldo')
def saldo():
    stan_konta = manager.stan_konta
    magazyn = manager.new_magazyn
    value = request.args.get('saldo')
    comment = request.args.get('komentarz')
    if not (value or comment) == '':
        value = int(value)
        if stan_konta + value >= 0:
            manager.data.append({'action': 'saldo', 'value': value, 'comment': comment})
            manager.json_file_saver()
            manager.reset_handler()
            manager.json_file_loader()
            manager.json_file_handler()
            stan_konta = manager.stan_konta
            magazyn = manager.new_magazyn
            return render_template('index.html', content=stan_konta, content2=magazyn)
        else:
            return render_template('index.html', content=stan_konta, content2=magazyn, content5='Not enough money')
    else:
        return render_template('index.html', content=stan_konta, content2=magazyn,
                               content5='Please fill the fields properly')
