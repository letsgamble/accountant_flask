from flask import Flask, render_template, request, redirect, url_for, flash
import json
import collections
import functools
import operator

app = Flask(__name__)
app.secret_key = 'many random bytes'


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


@app.route('/zakup/', methods=['GET', 'POST'])
def zakup():
    if request.method == 'POST':
        stan_konta = manager.stan_konta
        item = request.form.get('nazwa')
        price = request.form.get('cena')
        qty = request.form.get('liczba')
        if not item == '' and not price == '' and not qty == '':
            price = int(price)
            qty = int(qty)
            if price*qty <= stan_konta:
                manager.data.append({'action': 'zakup', 'item': item, 'price': price, 'qty': qty})
                manager.json_file_saver()
                manager.reset_handler()
                manager.json_file_loader()
                manager.json_file_handler()
                flash(f'{qty} {item} bought for {qty*price}')
                return redirect(url_for('main'))
            else:
                flash('Not enough money')
                return redirect(url_for('main'))
        else:
            flash(f'Fill all the fields in {saldo.__name__}')
            return redirect(url_for('main'))


@app.route('/sprzedaz/', methods=['GET', 'POST'])
def sprzedaz():
    if request.method == 'POST':
        item = request.form.get('nazwa')
        price = request.form.get('cena')
        qty = request.form.get('liczba')
        if not item == '' and not price == '' and not qty == '':
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
                flash(f'{qty} {item} sold for {qty*price}')
                return redirect(url_for('main'))
            else:
                flash('Item does not exist or not enough of it')
                return redirect(url_for('main'))
        else:
            flash(f'Fill all the fields in {saldo.__name__}')
            return redirect(url_for('main'))


@app.route('/saldo/', methods=['GET', 'POST'])
def saldo():
    if request.method == 'POST':
        stan_konta = manager.stan_konta
        value = request.form.get('saldo')
        comment = request.form.get('komentarz')
        if not value == '' and not comment == '':
            value = int(value)
            if stan_konta + value >= 0:
                manager.data.append({'action': 'saldo', 'value': value, 'comment': comment})
                manager.json_file_saver()
                manager.reset_handler()
                manager.json_file_loader()
                manager.json_file_handler()
                flash(f'{comment} changed balance for {value}')
                return redirect(url_for('main'))
            else:
                flash('Not enough money')
                return redirect(url_for('main'))
        else:
            flash(f'Fill all the fields in {saldo.__name__}')
            return redirect(url_for('main'))


@app.route('/historia/')
def historia():
    stan_konta = manager.stan_konta
    magazyn = manager.new_magazyn
    data = manager.data
    return render_template('history.html', content=data, content2=stan_konta, content3=magazyn)


@app.route('/historia/<line_from>/<line_to>/')
def historia_lines(line_from, line_to):
    stan_konta = manager.stan_konta
    magazyn = manager.new_magazyn
    if int(line_from) >= 1 and not int(line_from) > int(line_to):
        line_from = int(line_from) - int(1)
        data = manager.data[line_from:int(line_to)]
        return render_template('history.html', content=data, content2=stan_konta, content3=magazyn)
    else:
        return render_template('history.html', content2=stan_konta, content3=magazyn,
                               content4='1) Line number must be positive',
                               content5='2) Line_to must be higher or equal to line_from',
                               content6='3) Values cannot be 0')