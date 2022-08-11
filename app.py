import hashlib
from datetime import date , timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_httpauth import HTTPBasicAuth
import os

#future: printing an identifier for books
#future: printing membership card
#future: books without category or author should be handeled in frontend
#err: add id card generator
#err: borrow and return related routes and db model needs refactoring
#err: need to implent maximum number of borrowed books per user
#err: one person should not be able to borrow more than 1 book of same isbn
#err: should add expire date check for members
#err: need to change return mesages and add status codes

#IMPORTANT MUST READ: database should be created manually
#config values
DEFAULT_BORROW_DAYS = 30
DEFAULT_MEMBERSHIP_YEARS = 1
DATABASE_USERNAME = 'pedram'
DATABASE_PASSWORD = 'Project.4003'
DATABASE_NAME = 'library'
ADMIN_NAME = 'Pedram Akbari'
ADMIN_PASSWORD = 'Project.4003'
ADMIN_PHONE = '+989015155598'

app = Flask(__name__)
url = f'mysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@localhost/{DATABASE_NAME}'

#mysql databse config
app.config['SQLALCHEMY_DATABASE_URI'] = url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#init db
db = SQLAlchemy(app)
#init ma
ma = Marshmallow(app)
#init auth
auth = HTTPBasicAuth()

#err: should add error if not 10 or 13 digits
def fix_isbn(isbn):
    if len(isbn)!=10 and len(isbn)!= 13:
        return (0, "given isbn is not 10 or 13 digits.")
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
    return (calculated_isbn, "ok")

def check_phone(phone_number):
    if(len(phone_number)>=16):
        return "wrong phone number"
    else:
        return ""

def check_type(member_type):
    if(member_type == 'admin' or member_type == 'operator'):
        return ""
    else:
        return "wrong member type"

#classes
class TempID(db.Model):
    master_key = db.Column(db.SmallInteger, primary_key=True)
    next_id = db.Column(db.BigInteger, nullable=False)
    def __init__(self):
        self.next_id = int(str(date.today().year)[2:] + '0000000')

class Member(db.Model):
    member_id = db.Column(db.BigInteger, primary_key=True)
    member_name = db.Column(db.String(200), nullable=False)
    member_phone = db.Column(db.String(20), nullable=False)
    member_password = db.Column(db.String(64), nullable=False)
    member_type = db.Column(db.String(8), nullable=False)
    member_expire_date = db.Column(db.Date, nullable=False)

    def __init__(self, member_name, member_phone, member_password):
        current_date = date.today()
        current_id = TempID.query.get(1)
        if(str(current_id.next_id)[0:2] != str(current_date.year)[2:]):
            current_id.next_id = int(str(date.today().year)[2:] + '0000000')
            db.session.commit()
        current_id = TempID.query.get(1)
        self.member_id = current_id.next_id
        self.member_name = member_name
        self.member_phone = member_phone
        self.member_password = hashlib.sha256(member_password.encode('ascii')).hexdigest()
        self.member_type = 'user'
        self.member_expire_date = current_date.replace(year = current_date.year + DEFAULT_MEMBERSHIP_YEARS)

    def is_valid(member_id,member_password):
        if Member.query.get(member_id).member_password == member_password:
            return True
        else:
            return False
    
    def member_available(member_id):
        if Member.query.get(member_id):
            return True
        else:
            return False

    def get_role(member_id):
        return Member.query.get(member_id).member_type
    
    def increment_next_id():
        current_date = date.today()
        current_id = TempID.query.get(1)
        if(str(current_id.next_id)[0:2] == str(current_date.year)[2:]):
            current_id.next_id += 1
        else:
            current_id.next_id = int(str(date.today().year)[2:] + '0000000')

class Author(db.Model):
    author_name = db.Column(db.String(200), primary_key=True)
    
    def __init__(self, author_name):
        self.author_name = author_name

class Publisher(db.Model):
    publisher_name = db.Column(db.String(200), primary_key=True)

    def __init__(self, publisher_name):
        self.publisher_name = publisher_name

    def publisher_available(publisher_name):
        if Publisher.query.get(publisher_name):
            return True
        else:
            return False

class Category(db.Model):
    category_name = db.Column(db.String(200), primary_key=True)

    def __init__(self, category_name):
        self.category_name = category_name

class Borrowed(db.Model):
    borrow_id = db.Column(db.BigInteger, primary_key=True)
    isbn = db.Column(db.String(13), db.ForeignKey('book.isbn'), nullable=False)
    operator_id = db.Column(db.BigInteger, db.ForeignKey('member.member_id'), nullable=False)
    member_id = db.Column(db.BigInteger, db.ForeignKey('member.member_id'), nullable=False)
    borrow_date = db.Column(db.Date, nullable=False)

    def __init__(self,isbn,operator_id,member_id):
        current_date = date.today()
        self.isbn = isbn
        self.operator_id = operator_id
        self.member_id = member_id
        self.borrow_date = current_date
        #err: add quantity related things(should be added in api calls)

#err: fix return history
class Returned(db.Model):
    borrow_id = db.Column(db.BigInteger, db.ForeignKey('borrowed.borrow_id'), primary_key=True)
    operator_id = db.Column(db.BigInteger, db.ForeignKey('member.member_id'), nullable=False)
    return_date = db.Column(db.Date, nullable=False)
    penalty_days = db.Column(db.Integer, nullable=False)

    def __init__(self,borrow_id,operator_id):
        current_date = date.today()
        #err: delta is not int but it's checked as an int
        delta = current_date - Borrowed.query.get(borrow_id).borrow_date - timedelta(days=DEFAULT_BORROW_DAYS)
        self.borrow_id = borrow_id
        self.operator_id = operator_id
        self.return_date = current_date
        self.penalty_days = 0 if delta <= 0 else delta

class ReturnHistory(db.Model):
    borrow_id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(13), db.ForeignKey('book.isbn'), nullable=False)
    operator_id = db.Column(db.BigInteger, db.ForeignKey('member.member_id'), nullable=False)
    member_id = db.Column(db.BigInteger, db.ForeignKey('member.member_id'), nullable=False)
    borrow_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=False)

class Book(db.Model):
    isbn = db.Column(db.String(13), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    publish_year = db.Column(db.SmallInteger, nullable=False)
    edition = db.Column(db.SmallInteger, nullable=False)
    publisher_name = db.Column(db.String(200), db.ForeignKey('publisher.publisher_name'), primary_key=True)
    quantity = db.Column(db.SmallInteger, nullable=False)
    remaining = db.Column(db.SmallInteger, nullable=False)
    adding_date = db.Column(db.Date, nullable=False)

    def __init__(self, isbn,name, publish_year, edition, publisher_name, quantity, adding_date):
        self.isbn = isbn
        self.name = name
        self.publish_year = publish_year
        self.edition = edition
        self.publisher_name = publisher_name
        self.quantity = quantity
        self.remaining = quantity
        self.adding_date = adding_date

class AuthorBook(db.Model):
    author_name = db.Column(db.String(200), db.ForeignKey('author.author_name'), primary_key=True)
    isbn = db.Column(db.String(13), db.ForeignKey('book.isbn'), nullable=False)
    num = db.Column(db.SmallInteger, nullable=False, unique = True)

    def __init__(self, author_name, isbn, num):
        self.author_name = author_name
        self.isbn = isbn
        self.num = num

class TranslatorBook(db.Model):
    author_name = db.Column(db.String(200), db.ForeignKey('author.author_name'), primary_key=True)
    isbn = db.Column(db.String(13), db.ForeignKey('book.isbn'), nullable=False)
    num = db.Column(db.SmallInteger, nullable=False, unique = True)

    def __init__(self, author_name, isbn, num):
        self.author_name = author_name
        self.isbn = isbn
        self.num = num

class CategoryBook(db.Model):
    category_name = db.Column(db.String(200), db.ForeignKey('category.category_name'), primary_key=True)
    isbn = db.Column(db.String(13), db.ForeignKey('book.isbn'), nullable=False)
    num = db.Column(db.SmallInteger, nullable=False, unique = True)

    def __init__(self, category_name, isbn, num):
        self.category_name = category_name
        self.isbn = isbn
        self.num = num
    
#configs database if configed file doesn't exist
if(not os.path.isfile('configed')):
    db.create_all()
    tempid_config = TempID()
    db.session.add(tempid_config)
    db.session.commit()
    #add admin user
    current_date = date.today()
    member_name = ADMIN_NAME
    member_password = ADMIN_PASSWORD
    new_member = Member(member_name,ADMIN_PHONE ,member_password)
    new_member.member_id += 2000000000
    new_member.member_type = 'admin'
    db.session.add(new_member)
    #config next_id for next user creation
    Member.increment_next_id()
    db.session.commit()
    fp = open('configed', 'x')
    fp.close()

#auth setup
@auth.verify_password
def verify_password(member_id, hashed_member_password):
    if Member.is_valid(member_id, hashed_member_password):
        return member_id
    else:
        return None

@auth.get_user_roles
def get_user_roles(member_id):
    return Member.get_role(member_id)
    
#admin routes
@app.route('/api/signup_admin', methods=['POST'])
@auth.login_required(role='admin')
def signup_admin():
    member_name = request.json['member_name']
    member_phone = request.json['member_phone']
    member_password = request.json['member_password']
    member_type = request.json['member_type']
    if(not(check_phone(member_phone))):
        return jsonify({'status': f'{check_phone(member_phone)}'})
    if(not(check_type(member_type))):
        return jsonify({'status': f'{check_type(member_type)}'})
    new_member = Member(member_name, member_phone, member_password)
    new_member.member_type = member_type
    if member_type == 'admin':
        new_member.member_id += 2000000000
    else:
        new_member.member_id += 1000000000
    db.session.add(new_member)
    db.session.commit()
    return jsonify({'status': 'ok'})

#operator routes
@app.route('/api/signup', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def signup():
    member_name = request.json['member_name']
    member_phone = request.json['member_phone']
    member_password = request.json['member_password']
    if(not(check_phone(member_phone))):
        return jsonify({'status': f'{check_phone(member_phone)}'})
    new_member = Member(member_name, member_phone, member_password)
    db.session.add(new_member)
    #config next_id for next user creation
    Member.increment_next_id()
    db.session.commit()
    return jsonify({'status': 'ok'})

#err:seprate renewal for operator
#err: should check for member type(only users)
@app.route('/api/member_renewal', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def member_renewal():
    current_date = date.today()
    member_id = request.json['member_id']
    if not Member.member_available(member_id):
        return jsonify({'status': 'member not found'})
    renewal = Member.query.get(member_id)
    renewal.member_expire_date = renewal.member_expire_date.replace(year = renewal.member_expire_date.year + DEFAULT_MEMBERSHIP_YEARS)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/add_book', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def add_book():
    isbn = request.json['isbn']
    name = request.json['name']
    publish_year = request.json['publish_year']
    edition = request.json['edition']
    publisher_name = request.json['publisher_name']
    quantity = request.json['quantity']
    isbn = fix_isbn(isbn)
    if not bool(isbn[0]):
        return jsonify({'status': f'{isbn[1]}'})
    if not Publisher.publisher_available(publisher_name):
        return jsonify({'status': 'publisher not found'})
    isbn = isbn[0]
    new_book = Book(isbn,name,publish_year,edition,publisher_name,quantity)
    db.session.add(new_book)
    db.session.commit()
    return jsonify({'status': 'ok'})

#err
@app.route('/api/borrow_book', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def borrow_book():
    isbn = request.json['isbn']
    isbn = fix_isbn(isbn)
    if not bool(isbn[0]):
        return jsonify({'status': f'{isbn[1]}'})
    isbn = isbn[0]
    operator_id = request.json['operator_id']
    member_id = request.json['member_id']
    new_borrow = Borrowed(isbn, operator_id, member_id)
    db.session.add(new_borrow)
    db.session.commit()
    return jsonify({'status': 'ok'})

#err
@app.route('/api/return_book', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def return_book():
    borrow_id = request.json['borrow_id']
    operator_id = request.json['operator_id']
    new_return = Returned(borrow_id, operator_id)
    db.session.add(new_return)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/add_category', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def add_category():
    category_name = request.json['category_name']
    new_category = Category(category_name)
    db.session.add(new_category)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/add_author', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def add_author():
    author_name = request.json['author_name']
    new_author = Author(author_name)
    db.session.add(new_author)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/add_publisher', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def add_publisher():
    publisher_name = request.json['publisher_name']
    new_publisher = Publisher(publisher_name)
    db.session.add(new_publisher)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/author_book', methods=['POST'])
def author_book():
    #err
    author_name = request.json['author_name']
    isbn = request.json['isbn']
    isbn = fix_isbn(isbn)
    if not bool(isbn[0]):
        return jsonify({'status': f'{isbn[1]}'})
    isbn = isbn[0]
    num = request.json['num']
    new_author_book = AuthorBook(author_name, isbn, num)
    db.session.add(new_author_book)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/translator_book', methods=['POST'])
def translator_book():
    #err
    translator_book = request.json['translator_book']
    isbn = request.json['isbn']
    isbn = fix_isbn(isbn)
    if not bool(isbn[0]):
        return jsonify({'status': f'{isbn[1]}'})
    isbn = isbn[0]
    num = request.json['num']
    new_translator_book = TranslatorBook(translator_book, isbn, num)
    db.session.add(new_translator_book)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/category_book', methods=['POST'])
def category_book():
    #err
    category_name = request.json['category_name']
    isbn = request.json['isbn']
    isbn = fix_isbn(isbn)
    if not bool(isbn[0]):
        return jsonify({'status': f'{isbn[1]}'})
    isbn = isbn[0]
    num = request.json['num']
    new_category_book = CategoryBook(category_name, isbn, num)
    db.session.add(new_category_book)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/login', methods=['POST'])
def login():
    member_id = request.json['member_id']
    member_password = request.json['member_password']
    if verify_password(member_id, member_password):
        return jsonify({'status': 'ok'})
    else:
        return jsonify({'status': 'incorrect username or password'})

if __name__ == '__main__':
    app.run(debug=True)