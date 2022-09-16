from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_alembic import Alembic
import json
import collections
import functools
import operator


app = Flask(__name__)
app.secret_key = 'many random bytes'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accountant.db'
db = SQLAlchemy(app)


class Accountant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(10), nullable=False)
    value = db.Column(db.Integer, nullable=True)
    comment = db.Column(db.String(255), nullable=True)
    item = db.Column(db.String(50), nullable=True)
    price = db.Column(db.Integer, nullable=True)
    qty = db.Column(db.Integer, nullable=True)


db.create_all()


alembic = Alembic()
alembic.init_app(app)


class Manager:
    def __init__(self):
        self.file_path = 'in.json'
        self.stan_konta = 0
        self.data = []
        self._dict = {}
        self.magazyn = []
        self.new_magazyn = []

    def file_loader(self):
        # with open(self.file_path, 'r') as f:
        #     self.data = json.load(f)
        # self.data = db.session.query(Accountant).all()
        for query in db.session.query(Accountant).all():
            del query.__dict__['_sa_instance_state']
            self.data.append(query.__dict__)

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

    def file_saver(self):
        # with open(self.file_path, 'w', encoding='utf-8') as f:
        #     json.dump(self.data, f, indent=4)
        db.session.query(Accountant).delete()
        obj_list = []
        for record in self.data:
            accountant = Accountant(**record)
            obj_list.append(accountant)
            db.session.add_all(obj_list)
            db.session.commit()


manager = Manager()

manager.file_loader()
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
        if not item == '' and not price == '' and not qty == '' and int(qty) > 0 and int(price) > 0:
            price = int(price)
            qty = int(qty)
            if price*qty <= stan_konta:
                manager.data.append({'action': 'zakup', 'item': item, 'price': price, 'qty': qty})
                manager.file_saver()
                manager.reset_handler()
                manager.file_loader()
                manager.json_file_handler()
                flash(f'{qty} {item} bought for {qty*price}')
                return redirect(url_for('main'))
            else:
                flash('Not enough money')
                return redirect(url_for('main'))
        else:
            flash(f'Fix all the fields in zakup')
            return redirect(url_for('main'))


@app.route('/sprzedaz/', methods=['GET', 'POST'])
def sprzedaz():
    if request.method == 'POST':
        item = request.form.get('nazwa')
        price = request.form.get('cena')
        qty = request.form.get('liczba')
        if not item == '' and not price == '' and not qty == '' and int(qty) > 0 and int(price) > 0:
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
                manager.file_saver()
                manager.reset_handler()
                manager.file_loader()
                manager.json_file_handler()
                flash(f'{qty} {item} sold for {qty*price}')
                return redirect(url_for('main'))
            else:
                flash('Item does not exist or not enough of it')
                return redirect(url_for('main'))
        else:
            flash(f'Fix all the fields in sprzedaz')
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
                manager.file_saver()
                manager.reset_handler()
                manager.file_loader()
                manager.json_file_handler()
                flash(f'{comment} changed balance for {value}')
                return redirect(url_for('main'))
            else:
                flash('Not enough money')
                return redirect(url_for('main'))
        else:
            flash(f'Fill all the fields in saldo')
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
