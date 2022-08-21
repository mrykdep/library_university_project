import hashlib
from datetime import date , timedelta
from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_httpauth import HTTPBasicAuth
from card_gen.gen import cardgen
from flask_cors import CORS
import os
from pathlib import Path

#future: books without category or author should be handeled in frontend

#IMPORTANT MUST READ: database should be created manually
#config values
DEFAULT_BORROW_DAYS = 30
DEFAULT_MEMBERSHIP_YEARS = 1
DATABASE_USERNAME = 'pedram'
DATABASE_PASSWORD = 'Project.4003'
DATABASE_NAME = 'library'
MAX_BORROW = 5
ADMIN_NAME = 'Pedram Akbari'
ADMIN_PASSWORD = 'Project.4003'
ADMIN_PHONE = '+989015155598'

app = Flask(__name__)
CORS(app, support_credentials=True)
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
        return False
    else:
        return True

#error handler config
app.config['TRAP_HTTP_EXCEPTIONS']=True
@app.errorhandler(Exception)
def handle_error(e):
    try:
        if isinstance(e, HTTPException):
            if e.code == 404:
                return jsonify({'status': 'ERROR: Page Not Found'}),404
            elif e.code == 405:
                return jsonify({'status': 'ERROR: Method not available'}),405
            else:
                return jsonify({'status': f'ERROR: Unknow error. report to admin. error:{e}'}),500
        else:
            return jsonify({'status': f'ERROR: Unknow error. report to admin. error:{e}'}),500
    except:
        return jsonify({'status': f'ERROR: Unknow error. report to admin. error:{e}'}),500

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
    borrowed_books = db.Column(db.SmallInteger, nullable=False)
    operator_id = db.Column(db.BigInteger)

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
        self.borrowed_books = 0

    def is_valid(member_id,member_password):
        if len(Member.query.filter_by(member_id = member_id).all())==0:
            return False
        current_date = date.today()
        if Member.query.get(member_id).member_password == member_password and Member.query.get(member_id).member_type == 'admin':
            return True
        if Member.query.get(member_id).member_password == member_password and current_date <= Member.query.get(member_id).member_expire_date:
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
    
    def borrowed_number(member_id):
        return Member.query.get(member_id).borrow_book

class Author(db.Model):
    author_name = db.Column(db.String(200), primary_key=True)
    
    def __init__(self, author_name):
        self.author_name = author_name
    
    def author_available(author_name):
        if Author.query.get(author_name):
            return True
        else:
            return False

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

    def category_available(category_name):
        if Category.query.get(category_name):
            return True
        else:
            return False

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
    def borrow_id_available(borrow_id):
        if Borrowed.query.get(borrow_id):
            return True
        else:
            return False

class BorrowedSchema(ma.Schema):
    class Meta:
        fields = ('borrow_id','isbn', 'member_id', 'borrow_date')

borrowed_schema = BorrowedSchema()
borrowedes_schema = BorrowedSchema(many=True)

class Returned(db.Model):
    return_id = db.Column(db.BigInteger, primary_key=True)
    isbn = db.Column(db.String(13), db.ForeignKey('book.isbn'), nullable=False)
    operator_id = db.Column(db.BigInteger, db.ForeignKey('member.member_id'), nullable=False)
    operator_id_return = db.Column(db.BigInteger, db.ForeignKey('member.member_id'), nullable=False)
    member_id = db.Column(db.BigInteger, db.ForeignKey('member.member_id'), nullable=False)
    return_date = db.Column(db.Date, nullable=False)
    penalty_days = db.Column(db.Integer, nullable=False)

    def __init__(self, borrow_id, operator_id_return):
        current_date = date.today()
        delta = current_date - (Borrowed.query.get(borrow_id).borrow_date) - (timedelta(days=DEFAULT_BORROW_DAYS))
        self.isbn = Borrowed.query.get(borrow_id).isbn
        self.operator_id = Borrowed.query.get(borrow_id).operator_id
        self.operator_id_return = operator_id_return
        self.member_id = Borrowed.query.get(borrow_id).member_id
        self.return_date = current_date
        self.penalty_days = 0 if (delta.days <= 0) else delta.days

class Book(db.Model):
    isbn = db.Column(db.String(13), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    publish_year = db.Column(db.SmallInteger, nullable=False)
    edition = db.Column(db.SmallInteger, nullable=False)
    publisher_name = db.Column(db.String(200), db.ForeignKey('publisher.publisher_name'), nullable = False)
    quantity = db.Column(db.SmallInteger, nullable=False)
    remaining = db.Column(db.SmallInteger, nullable=False)
    adding_date = db.Column(db.Date, nullable=False)
    operator_id = db.Column(db.BigInteger, db.ForeignKey('member.member_id'), nullable = False)

    def __init__(self, isbn,name, publish_year, edition, publisher_name, quantity, adding_date):
        self.isbn = isbn
        self.name = name
        self.publish_year = publish_year
        self.edition = edition
        self.publisher_name = publisher_name
        self.quantity = quantity
        self.remaining = quantity
        self.adding_date = adding_date

    def available(isbn):
        if Book.query.get(isbn).quantity != 0:
            return True
        else:
            return False
    def is_available(isbn):
        if Book.query.get(isbn):
            return True
        else:
            return False


class BookSchema(ma.Schema):
    class Meta:
        fields = ('isbn', 'name', 'publish_year', 'edition', 'publisher_name', 'quantity', 'remaining')

book_schema = BookSchema()
books_schema = BookSchema(many=True)

class AuthorBook(db.Model):
    author_book_id = db.Column(db.BigInteger, primary_key=True)
    author_name = db.Column(db.String(200), db.ForeignKey('author.author_name'), nullable=False)
    isbn = db.Column(db.String(13), db.ForeignKey('book.isbn'), nullable=False)
    num = db.Column(db.SmallInteger, nullable=False)

    def __init__(self, author_name, isbn, num):
        self.author_name = author_name
        self.isbn = isbn
        self.num = num

class TranslatorBook(db.Model):
    translator_book_id = db.Column(db.BigInteger, primary_key=True)
    author_name = db.Column(db.String(200), db.ForeignKey('author.author_name'), nullable=False)
    isbn = db.Column(db.String(13), db.ForeignKey('book.isbn'), nullable=False)
    num = db.Column(db.SmallInteger, nullable=False)

    def __init__(self, author_name, isbn, num):
        self.author_name = author_name
        self.isbn = isbn
        self.num = num

class CategoryBook(db.Model):
    category_book_id = db.Column(db.BigInteger, primary_key=True)
    category_name = db.Column(db.String(200), db.ForeignKey('category.category_name'), nullable=False)
    isbn = db.Column(db.String(13), db.ForeignKey('book.isbn'), nullable=False)
    num = db.Column(db.SmallInteger, nullable=False)

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
    current_date = date.today()
    current_id = TempID.query.get(1)
    if(str(current_id.next_id)[0:2] == str(current_date.year)[2:]):
        current_id.next_id += 1
    else:
        current_id.next_id = int(str(date.today().year)[2:] + '0000000')
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
#err: needs testing of operator added most member
@app.route('/api/admin/report', methods=['GET'])
@auth.login_required(role='admin')
def report():
    returned_dic = {}
    returned_operator_dic = {}
    returned = Returned.query.order_by(Returned.isbn).all()
    for check in returned:
        if check.isbn in returned_dic:
            returned_dic[check.isbn] += 1
        else:
            returned_dic[check.isbn] = 1
        if check.operator_id_return in returned_operator_dic:
            returned_operator_dic[check.operator_id_return] +=1
        else:
            returned_operator_dic[check.operator_id_return] =1
    
    borrowed = Borrowed.query.order_by(Borrowed.isbn).all()
    for check in borrowed:
        if check.isbn in returned_dic:
            returned_dic[check.isbn] += 1
        else:
            returned_dic[check.isbn] = 1
        if check.operator_id in returned_operator_dic:
            returned_operator_dic[check.operator_id] +=1
        else:
            returned_operator_dic[check.operator_id] =1

    if len(returned_dic) == 0:
        max_book = [0,0]
    else:
        max_book = max(returned_dic, key=returned_dic.get)
        max_book = [max_book, returned_dic.get(max_book)]
    if len(returned_operator_dic) == 0:
        max_returned = [0,0]
    else:
        max_returned = max(returned_operator_dic, key=returned_operator_dic.get)
        max_returned = [max_returned, returned_operator_dic.get(max_returned)]

    member_dic = {}
    members = Returned.query.order_by(Returned.isbn).all()
    for check in members:
        if check.operator_id in member_dic:
            member_dic[check.operator_id] += 1
        else:
            member_dic[check.operator_id] = 1
    if len(member_dic) == 0:
        max_member = [0,0]
    else:
        max_member = max(member_dic, key=member_dic.get)
        max_member = [max_member, member_dic.get(max_member)]
    
    report = f"""Operator {max_member[0]} added most members: {max_member[1]}
Operator {max_returned[0]} added most borrows and returns: {max_returned[1]}
Book {max_book[0]} is the most borrowed book: {max_book[1]}"""
    return jsonify({'status': 'ok', 'msg': report})
    
@app.route('/api/admin/view_borrowed_books', methods=['GET'])
@auth.login_required(role='admin')
def view_borrowed_books():
    borrowed = Borrowed.query.order_by(Borrowed.borrow_id).all()
    result = borrowedes_schema.dump(borrowed)
    return jsonify(result)

@app.route('/api/admin/signup_admin', methods=['POST'])
@auth.login_required(role='admin')
def signup_admin():
    member_name = request.json['member_name']
    member_phone = request.json['member_phone']
    member_password = request.json['member_password']
    member_type = request.json['member_type']
    if(not(check_phone(member_phone))):
        return jsonify({'status': 'wrong phone number'}),400
    if member_type != 'operator' and member_type!= 'admin':
        return jsonify({'status': 'type is not an operator or admin'}),400
    new_member = Member(member_name, member_phone, member_password)
    new_member.member_type = member_type
    if member_type == 'admin':
        new_member.member_id += 2000000000
    else:
        new_member.member_id += 1000000000
    db.session.add(new_member)
    #config next_id for next user creation
    current_date = date.today()
    current_id = TempID.query.get(1)
    if(str(current_id.next_id)[0:2] == str(current_date.year)[2:]):
        current_id.next_id += 1
    else:
        current_id.next_id = int(str(date.today().year)[2:] + '0000000')
    db.session.commit()
    print(new_member.member_id)
    return jsonify({'status': 'ok', 'msg': f'member id: {new_member.member_id}'})

@app.route('/api/admin/operator_renewal', methods=['POST'])
@auth.login_required(role='admin')
def operator_renewal():
    current_date = date.today()
    member_id = request.json['member_id']
    if not Member.member_available(member_id):
        return jsonify({'status': 'operator not found'}),400
    if Member.get_role(member_id)!= 'operator':
        return jsonify({'status': 'member is not an operator'}),400
    renewal = Member.query.get(member_id)
    renewal.member_expire_date = renewal.member_expire_date.replace(year = renewal.member_expire_date.year + DEFAULT_MEMBERSHIP_YEARS)
    renewal.operator_id = auth.current_user()
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/admin/cardpdfadmin', methods=['POST'])
@auth.login_required(role='admin')
def cardpdfadmin():
    member_id = request.json['member_id']
    if (not Member.member_available(member_id)):
        return jsonify({'status': 'member is not available'}),400
    member = Member.query.get(member_id)
    cardgen(member_id, member.member_name, member.member_type, member.member_expire_date)
    print(f'{Path().absolute()}/card_gen/res/card.pdf')
    return send_file(f'{Path().absolute()}/card_gen/res/card.pdf', mimetype='application/pdf')

#operator routes
@app.route('/api/operator/signup', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def signup():
    member_name = request.json['member_name']
    member_phone = request.json['member_phone']
    member_password = request.json['member_password']
    if(not(check_phone(member_phone))):
        return jsonify({'status': 'wrong phone number'}),400
    new_member = Member(member_name, member_phone, member_password)
    new_member.operator_id = auth.current_user()
    db.session.add(new_member)
    #config next_id for next user creation
    current_date = date.today()
    current_id = TempID.query.get(1)
    if(str(current_id.next_id)[0:2] == str(current_date.year)[2:]):
        current_id.next_id += 1
    else:
        current_id.next_id = int(str(date.today().year)[2:] + '0000000')
    db.session.commit()
    return jsonify({'status': 'ok', 'msg': f'member id: {new_member.member_id}'})

@app.route('/api/operator/member_renewal', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def member_renewal():
    current_date = date.today()
    member_id = request.json['member_id']
    if not Member.member_available(member_id):
        return jsonify({'status': 'member not found'}),400
    if Member.get_role(member_id)== 'operator':
        return jsonify({'status': 'member is an operator'}),400
    if Member.get_role(member_id)== 'admin':
        return jsonify({'status': 'member is an admin'}),400
    renewal = Member.query.get(member_id)
    renewal.member_expire_date = renewal.member_expire_date.replace(year = renewal.member_expire_date.year + DEFAULT_MEMBERSHIP_YEARS)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/operator/add_book', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def add_book():
    current_date = date.today()
    isbn = request.json['isbn']
    name = request.json['name']
    publish_year = request.json['publish_year']
    edition = request.json['edition']
    publisher_name = request.json['publisher_name']
    quantity = request.json['quantity']
    isbn = fix_isbn(isbn)
    if not bool(isbn[0]):
        return jsonify({'status': f'{isbn[1]}'}),400
    isbn = isbn[0]
    if not Publisher.publisher_available(publisher_name):
        return jsonify({'status': 'publisher not found'}),400
    if Book.is_available(isbn):
        return jsonify({'status': 'book already added'}),400
    new_book = Book(isbn,name,publish_year,edition,publisher_name,quantity,current_date)
    new_book.operator_id = auth.current_user()
    db.session.add(new_book)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/operator/add_quantity', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def add_quantity():
    isbn = request.json['isbn']
    added_quantity = request.json['added_quantity']
    isbn = fix_isbn(isbn)
    if not bool(isbn[0]):
        return jsonify({'status': f'{isbn[1]}'}),400
    isbn = isbn[0]
    if not Book.available(isbn):
        return jsonify({'status': 'book not in library'}),400
    book = Book.query.get(isbn)
    book.quantity = int(book.quantity) + (int(added_quantity))
    book.remaining = int(book.remaining) + (int(added_quantity))
    book.operator_id = auth.current_user()
    db.session.commit()
    return jsonify({'status': 'ok'})

#err: check book is valid
@app.route('/api/operator/borrow_book', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def borrow_book():
    isbn = request.json['isbn']
    member_id = request.json['member_id']
    operator_id = auth.current_user()
    isbn = fix_isbn(isbn)
    if not bool(isbn[0]):
        return jsonify({'status': f'{isbn[1]}'})
    if Member.member_available(operator_id) and not Member.is_valid(member_id, Member.query.get(operator_id).member_password):
        return jsonify({'status': 'operator expired'}),401
    if not Member.member_available(member_id):
        return jsonify({'status': 'member not found'}),400
    if not Member.is_valid(member_id, Member.query.get(member_id).member_password):
        return jsonify({'status': 'member expired'}),400
    isbn = isbn[0]
    if not Book.is_available(isbn):
        return jsonify({'status': 'this isbn is not valid'}),400
    if not Book.available(isbn):
        return jsonify({'status': 'all books of this isbn are borrowed'}),400
    if Member.query.get(member_id).borrowed_books >= MAX_BORROW:
        return jsonify({'status': 'user borrowed max possible books'}),400
    new_borrow = Borrowed(isbn, operator_id, member_id)
    db.session.add(new_borrow)
    book = Book.query.get(isbn)
    book.remaining -= 1
    member = Member.query.get(member_id)
    member.borrowed_books += 1
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/operator/return_book', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def return_book():
    operator_id = auth.current_user()
    borrow_id = request.json['borrow_id']
    if not Borrowed.borrow_id_available(borrow_id):
        return jsonify({'status': 'borrow id not found'}),400
    if not Member.member_available(operator_id):
        return jsonify({'status': 'operator not found'}),401
    new_return = Returned(borrow_id, operator_id)
    old_borrow = Borrowed.query.get(borrow_id)
    db.session.delete(old_borrow)
    db.session.add(new_return)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/operator/add_category', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def add_category():
    category_name = request.json['category_name']
    if Category.category_available(category_name):
        return jsonify({'status': 'category already added'}),400
    new_category = Category(category_name)
    db.session.add(new_category)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/operator/add_author', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def add_author():
    author_name = request.json['author_name']
    if Author.author_available(author_name):
        return jsonify({'status': 'author already added'}),400
    new_author = Author(author_name)
    db.session.add(new_author)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/operator/add_publisher', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def add_publisher():
    publisher_name = request.json['publisher_name']
    if Publisher.publisher_available(publisher_name):
        return jsonify({'status': 'publisher already added'}),400
    new_publisher = Publisher(publisher_name)
    db.session.add(new_publisher)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/operator/author_book', methods=['POST'])
def author_book():
    author_name = request.json['author_name']
    isbn = request.json['isbn']
    isbn = str(isbn)
    isbn = fix_isbn(isbn)
    if not bool(isbn[0]):
        return jsonify({'status': f'{isbn[1]}'}),400
    if not Author.author_available(author_name):
        return jsonify({'status': 'author not found'}),400
    isbn = isbn[0]
    num = request.json['num']
    new_author_book = AuthorBook(author_name, isbn, num)
    db.session.add(new_author_book)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/operator/translator_book', methods=['POST'])
def translator_book():
    translator_name = request.json['translator_name']
    isbn = request.json['isbn']
    num = request.json['num']
    isbn = fix_isbn(isbn)
    if not bool(isbn[0]):
        return jsonify({'status': f'{isbn[1]}'}),400
    if not Author.author_available(translator_name):
        return jsonify({'status': 'translator not found'}),400
    isbn = isbn[0]
    new_translator_book = TranslatorBook(translator_name, isbn, num)
    db.session.add(new_translator_book)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/operator/category_book', methods=['POST'])
def category_book():
    category_name = request.json['category_name']
    isbn = request.json['isbn']
    isbn = fix_isbn(isbn)
    if not bool(isbn[0]):
        return jsonify({'status': f'{isbn[1]}'}),400
    if not Category.category_available(category_name):
        return jsonify({'status': 'category not found'}),400
    isbn = isbn[0]
    num = request.json['num']
    new_category_book = CategoryBook(category_name, isbn, num)
    db.session.add(new_category_book)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/operator/cardpdf', methods=['POST'])
@auth.login_required(role=['admin', 'operator'])
def cardpdf():
    member_id = request.json['member_id']
    if not Member.member_available(member_id):
        return jsonify({'status': 'member is not available'}),400
    if Member.query.get(member_id).member_type != 'user':
        return jsonify({'status': 'member is not user'}),400
    member = Member.query.get(member_id)
    cardgen(member_id, member.member_name, member.member_type, member.member_expire_date)
    return send_file(f'{Path().absolute()}/card_gen/res/card.pdf')

#user routes
@app.route('/api/user/change_password', methods=['POST'])
@auth.login_required(role=['admin', 'operator', 'user'])
def change_password():
    member_password = request.json['member_password']
    member_id = auth.current_user()
    member = Member.query.get(member_id)
    member.member_password = hashlib.sha256(member_password.encode('ascii')).hexdigest()
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/user/change_phone', methods=['POST'])
@auth.login_required(role=['admin', 'operator', 'user'])
def change_phone():
    member_phone = request.json['member_phone']
    member_id = auth.current_user()
    member = Member.query.get(member_id)
    if check_phone(member_phone):
        member.member_phone = member_phone
        db.session.commit()
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'phone number incorrect'}),400

@app.route('/api/user/borrowed_books', methods=['GET'])
@auth.login_required(role=['admin', 'operator', 'user'])
def borrowed_books():
    borrowed = Borrowed.query.filter_by(member_id=f'{auth.current_user()}')
    result = borrowedes_schema.dump(borrowed)
    return jsonify(result)

@app.route('/api/user/search_book', methods=['POST'])
@auth.login_required(role=['admin', 'operator', 'user'])
def search_book():
    valid_keys = ['isbn','name','publish_year','edition','publisher_name']
    checker = {}
    valid_keys2 = ['author','translator','category']
    checker2 = {}
    isbn = request.json['isbn']
    name = request.json['name']
    publish_year = request.json['publish_year']
    edition = request.json['edition']
    publisher_name = request.json['publisher_name']
    author = request.json['author']
    translator = request.json['translator']
    category = request.json['translator']
    if(isbn == ''):
        valid_keys.remove('isbn')
    if(name == ''):
        valid_keys.remove('name')
    if(publish_year == ''):
        valid_keys.remove('publish_year')
    if(edition == ''):
        valid_keys.remove('edition')
    if(publisher_name == ''):
        valid_keys.remove('publisher_name')
    if(author == ''):
        valid_keys2.remove('author')
    if(translator == ''):
        valid_keys2.remove('translator')
    if(category == ''):
        valid_keys2.remove('category')

    for key in valid_keys:
        checker[key] = request.json[key]
    for key in valid_keys2:
        checker2[key] = request.json[key]

    books = Book.query.filter_by(**checker).all()

    if 'author' in checker2:
        for book in books:
            authors = AuthorBook.query.filter_by(isbn = book.isbn)
            for a in authors:
                if(a.author_name == checker2['author']):
                    break
            else:
                books.remove(book)
    if 'category' in checker2:
        for book in books:
            categorys = CategoryBook.query.filter_by(isbn = book.isbn)
            for a in categorys:
                if(a.category_name == checker2['category']):
                    break
            else:
                books.remove(book)
    if 'translator' in checker2:
        for book in books:
            translators = TranslatorBookquery.filter_by(isbn = book.isbn)
            for a in translators:
                if(a.translator_name == checker2['translator']):
                    break
            else:
                books.remove(book)

    return books_schema.dump(books)

#everyone routes
@app.route('/api/login', methods=['POST'])
def login():
    member_id = request.json['member_id']
    member_password = request.json['member_password']
    if verify_password(member_id, member_password):
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'incorrect username or password'}),401

@app.route('/api/login_operator', methods=['POST'])
def login_operator():
    member_id = request.json['member_id']
    member_password = request.json['member_password']
    if not verify_password(member_id, member_password):
        return jsonify({'status': 'incorrect username or password'}),401
    member = Member.query.get(member_id)
    if member.member_type == 'user':
        return jsonify({'status': 'this member is not an operator'}),403
    return jsonify({'status': 'ok'})

@app.route('/api/login_admin', methods=['POST'])
def login_admin():
    member_id = request.json['member_id']
    member_password = request.json['member_password']
    if not verify_password(member_id, member_password):
        return jsonify({'status': 'incorrect username or password'}),401
    member = Member.query.get(member_id)
    if member.member_type != 'admin':
        return jsonify({'status': 'this member is not an admin'}),403
    return jsonify({'status': 'ok'})
    
if __name__ == '__main__':
    app.run(debug=False)