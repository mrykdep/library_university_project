import hashlib
from datetime import date , timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os

#config values
DEFAULT_BORROW_DAYS = 30
DEFAULT_MEMBERSHIP_YEARS = 1
DATABASE_USERNAME = 'pedram'
DATABASE_PASSWORD = 'Project.4003'
#database should be created manually
DATABASE_NAME = 'library'
CURRENT_PREFIX = '401'

app = Flask(__name__)
url = f'mysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@localhost/{DATABASE_NAME}'

#mysql databse config
app.config['SQLALCHEMY_DATABASE_URI'] = url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#init db
db = SQLAlchemy(app)
#init ma
ma = Marshmallow(app)

#classes
class TempID(db.Model):
    master_key = db.Column(db.SmallInteger, primary_key=True)
    next_id = db.Column(db.BigInteger, nullable=False)
    def __init__(self):
        self.next_id = int(str(date.today().year)[2:] + '0000000')

class Member(db.Model):
    member_id = db.Column(db.BigInteger, primary_key=True)
    member_name = db.Column(db.String(200), nullable=False)
    member_password = db.Column(db.String(64), nullable=False)
    member_type = db.Column(db.SmallInteger, nullable=False)
    member_expire_date = db.Column(db.Date, nullable=False)

    def __init__(self, member_name, member_password, member_type):
        current_date = date.today()
        current_id = TempID.query.get(1)
        self.member_id = current_id.next_id
        self.member_name = member_name
        self.member_password = hashlib.sha256(member_password.encode('ascii')).hexdigest()
        self.member_type = member_type
        self.member_expire_date = current_date.replace(year = current_date.year + DEFAULT_MEMBERSHIP_YEARS)

class Author(db.Model):
    author_id = db.Column(db.Integer, primary_key=True)
    author_name = db.Column(db.String(200), nullable=False)
    
    def __init__(self, author_id, author_name):
        self.author_id = author_id
        self.author_name = author_name

class Publisher(db.Model):
    publisher_id = db.Column(db.Integer, primary_key=True)
    publisher_name = db.Column(db.String(200), nullable=False)

    def __init__(self, publisher_id, publisher_name):
        self.publisher_id = publisher_id
        self.publisher_name = publisher_name

class Category(db.Model):
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(200), nullable=False)

    def __init__(self, category_id, category_name):
        self.category_id = category_id
        self.category_name = category_name

class Borrowed(db.Model):
    borrow_id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(13), db.ForeignKey('book.isbn'), nullable=False)
    operator_id = db.Column(db.BigInteger, db.ForeignKey('member.member_id'), nullable=False)
    member_id = db.Column(db.BigInteger, db.ForeignKey('member.member_id'), nullable=False)
    return_date = db.Column(db.Date, nullable=False)

    def __init__(self,isbn,operator_id,member_id):
        current_date = date.today()
        self.isbn = isbn
        self.operator_id = operator_id
        self.member_id = member_id
        self.return_date = current_date + timedelta(days=DEFAULT_BORROW_DAYS)
        #err: add quantity related things(should be added in api calls)

class Returned(db.Model):
    borrow_id = db.Column(db.Integer, db.ForeignKey('borrowed.borrow_id'), primary_key=True)
    operator_id = db.Column(db.BigInteger, db.ForeignKey('member.member_id'), nullable=False)
    return_date = db.Column(db.Date, nullable=False)
    penalty_days = db.Column(db.Integer, nullable=False)

    def __init__(self,borrow_id,operator_id,return_date):
        current_date = date.today()
        delta = current_date - Borrowed.query.get(borrow_id).return_date
        self.borrowed_id = borrowed_id
        self.operator_id = operator_id
        self.return_date = current_date
        #err: needs checking
        self.penalty_days = 0 if delta <= 0 else delta
        #err: add quantity related things(should be added in api calls)

class Book(db.Model):
    isbn = db.Column(db.String(13), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    publish_year = db.Column(db.SmallInteger, nullable=False)
    edition = db.Column(db.SmallInteger, nullable=False)
    publisher_id = db.Column(db.Integer, db.ForeignKey('publisher.publisher_id'), primary_key=True)
    quantity = db.Column(db.SmallInteger, nullable=False)
    remaining = db.Column(db.SmallInteger, nullable=False)

    def __init__(self, isbn,name, publish_year, edition, publisher_id, quantity):
        calculated_isbn = isbn
        if len(calculated_isbn)!=13:
            sum = 0
            for i in range(len(isbn)):
                c = int(isbn[i])
                if i % 2: w = 3
                else: w = 1
                sum += w * c
            r = 10 - (sum % 10)
            if r == 10 : sum = '0'
            else: sum = str(r)
            calculated_isbn = '978' + isbn[:-1] + sum
        self.isbn = calculated_isbn
        self.name = name
        self.publish_year = publish_year
        self.edition = edition
        self.publisher_id = publisher_id
        self.quantity = quantity
        self.remaining = quantity

class AuthorBook(db.Model):
    author_id = db.Column(db.Integer, db.ForeignKey('author.author_id'), primary_key=True)
    isbn = db.Column(db.String(13), db.ForeignKey('book.isbn'), nullable=False)
    num = db.Column(db.SmallInteger, nullable=False, unique = True)

    def __init__(self, author_id, isbn, num):
        self.author_id = author_id
        self.isbn = isbn
        self.num = num

class TranslatorBook(db.Model):
    author_id = db.Column(db.Integer, db.ForeignKey('author.author_id'), primary_key=True)
    isbn = db.Column(db.String(13), db.ForeignKey('book.isbn'), nullable=False)
    num = db.Column(db.SmallInteger, nullable=False, unique = True)

    def __init__(self, author_id, isbn, num):
        self.author_id = author_id
        self.isbn = isbn
        self.num = num

class CategoryBook(db.Model):
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), primary_key=True)
    isbn = db.Column(db.String(13), db.ForeignKey('book.isbn'), nullable=False)
    num = db.Column(db.SmallInteger, nullable=False, unique = True)

    def __init__(self, category_id, isbn, num):
        self.category_id = category_id
        self.isbn = isbn
        self.num = num
    
#configs database if configed file doesn't exist
if(not os.path.isfile('configed')):
    db.create_all()
    tempid_config = TempID()
    db.session.add(tempid_config)
    db.session.commit()
    fp = open('configed', 'x')
    fp.close()

#routes
@app.route('/api/member', methods=['POST'])
def add_member():
    current_date = date.today()
    member_name = request.json['member_name']
    member_password = request.json['member_password']
    member_type = request.json['member_type']
    new_member = Member(member_name, member_password, member_type)
    db.session.add(new_member)
    current_id = TempID.query.get(1)
    #config next_id for next user creation
    if(str(current_id.next_id)[0:2] == str(current_date.year)[2:]):
          current_id.next_id += 1
    else:
        current_id.next_id = int(str(date.today().year)[2:] + '0000000')
    db.session.commit()
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(debug=True)