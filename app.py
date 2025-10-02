from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    available = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'available': self.available
        }

class BorrowRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    borrower_name = db.Column(db.String(100), nullable=False)
    borrow_date = db.Column(db.Date, default=date.today)
    is_returned = db.Column(db.Boolean, default=False)
    
    book = db.relationship('Book', backref='borrow_records')
    
    def to_dict(self):
        return {
            'id': self.id,
            'book_id': self.book_id,
            'book_title': self.book.title,
            'borrower_name': self.borrower_name,
            'borrow_date': self.borrow_date.isoformat(),
            'is_returned': self.is_returned
        }

@app.route('/')
def index():
    books = Book.query.all()
    records = BorrowRecord.query.filter_by(is_returned=False).all()
    return render_template('index.html', books=books, records=records)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        
        new_book = Book(title=title, author=author)
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('add_book.html')

@app.route('/delete_book/<int:book_id>')
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/borrow_book/<int:book_id>', methods=['GET', 'POST'])
def borrow_book(book_id):
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        borrower_name = request.form['borrower_name']
        
        new_record = BorrowRecord(book_id=book_id, borrower_name=borrower_name)
        book.available = False
        
        db.session.add(new_record)
        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('borrow_book.html', book=book)

@app.route('/api-demo')
def api_demo():
    """Web page to demonstrate REST API"""
    return render_template('api_demo.html')

@app.route('/return_book/<int:record_id>')
def return_book(record_id):
    record = BorrowRecord.query.get_or_404(record_id)
    record.is_returned = True
    record.book.available = True
    
    db.session.commit()
    return redirect(url_for('index'))

# ============= RESTful API Routes =============
# Demonstrate 6 REST principles:
# 1. Client-Server Architecture
# 2. Stateless
# 3. Cacheable
# 4. Uniform Interface
# 5. Layered System
# 6. Code on Demand (optional)

# Books API
@app.route('/api/books', methods=['GET'])
def get_books():
    """GET /api/books - Retrieve all books (Uniform Interface)"""
    books = Book.query.all()
    return jsonify({
        'books': [book.to_dict() for book in books],
        'count': len(books)
    })

@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """GET /api/books/{id} - Retrieve specific book (Uniform Interface)"""
    book = Book.query.get_or_404(book_id)
    return jsonify(book.to_dict())

@app.route('/api/books', methods=['POST'])
def create_book():
    """POST /api/books - Create new book (Stateless)"""
    data = request.get_json()
    if not data or 'title' not in data or 'author' not in data:
        return jsonify({'error': 'Title and author are required'}), 400
    
    book = Book(title=data['title'], author=data['author'])
    db.session.add(book)
    db.session.commit()
    
    return jsonify(book.to_dict()), 201

@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    """PUT /api/books/{id} - Update book (Idempotent)"""
    book = Book.query.get_or_404(book_id)
    data = request.get_json()
    
    if 'title' in data:
        book.title = data['title']
    if 'author' in data:
        book.author = data['author']
    if 'available' in data:
        book.available = data['available']
    
    db.session.commit()
    return jsonify(book.to_dict())

@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book_api(book_id):
    """DELETE /api/books/{id} - Delete book (Idempotent)"""
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return '', 204

# Borrow Records API
@app.route('/api/borrow-records', methods=['GET'])
def get_borrow_records():
    """GET /api/borrow-records - Retrieve all borrow records"""
    records = BorrowRecord.query.all()
    return jsonify({
        'records': [record.to_dict() for record in records],
        'count': len(records)
    })

@app.route('/api/borrow-records', methods=['POST'])
def create_borrow_record():
    """POST /api/borrow-records - Create new borrow record"""
    data = request.get_json()
    if not data or 'book_id' not in data or 'borrower_name' not in data:
        return jsonify({'error': 'book_id and borrower_name are required'}), 400
    
    book = Book.query.get_or_404(data['book_id'])
    if not book.available:
        return jsonify({'error': 'Book is not available'}), 400
    
    record = BorrowRecord(book_id=data['book_id'], borrower_name=data['borrower_name'])
    book.available = False
    
    db.session.add(record)
    db.session.commit()
    
    return jsonify(record.to_dict()), 201

@app.route('/api/borrow-records/<int:record_id>/return', methods=['PATCH'])
def return_book_api(record_id):
    """PATCH /api/borrow-records/{id}/return - Return a book"""
    record = BorrowRecord.query.get_or_404(record_id)
    
    if record.is_returned:
        return jsonify({'error': 'Book already returned'}), 400
    
    record.is_returned = True
    record.book.available = True
    
    db.session.commit()
    return jsonify(record.to_dict())

# API Documentation endpoint
@app.route('/api')
def api_docs():
    """API Documentation demonstrating REST principles"""
    docs = {
        "title": "Library Management REST API",
        "description": "Demonstrating 6 REST principles",
        "principles": {
            "1. Client-Server": "Clear separation between client and server",
            "2. Stateless": "Each request contains all information needed",
            "3. Cacheable": "Responses are cacheable (GET requests)",
            "4. Uniform Interface": "Standard HTTP methods and URIs",
            "5. Layered System": "Can add proxy, gateway layers",
            "6. Code on Demand": "Optional - can send executable code"
        },
        "endpoints": {
            "Books": {
                "GET /api/books": "Get all books",
                "GET /api/books/{id}": "Get specific book",
                "POST /api/books": "Create new book",
                "PUT /api/books/{id}": "Update book",
                "DELETE /api/books/{id}": "Delete book"
            },
            "Borrow Records": {
                "GET /api/borrow-records": "Get all borrow records",
                "POST /api/borrow-records": "Create borrow record",
                "PATCH /api/borrow-records/{id}/return": "Return book"
            }
        }
    }
    return jsonify(docs)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)