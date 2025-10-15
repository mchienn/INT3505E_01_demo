from flask import Flask, request, jsonify
from database import init_db, db
from models import Book, User, BorrowRecord

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///library.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
init_db(app)

# --- Tạo dữ liệu mẫu ---
def seed_data():
    Book.query.delete()
    User.query.delete()
    db.session.commit()


    sample_books = [
    Book(title="NAVER AI Hackathon", author="Tran B", category="Programming", year=2021),
    Book(title="Harry Potter", author="J.K Rowling", category="Fiction", year=2003),
    Book(title="Lord of the Rings", author="J.R.R. Tolkien", category="Fantasy", year=2015),
    Book(title="Deep Learning with Python", author="François Chollet", category="AI", year=2021),
    Book(title="Clean Code", author="Robert C. Martin", category="Software Engineering", year=2008),
    Book(title="The Pragmatic Programmer", author="Andrew Hunt", category="Software Engineering", year=1999),
    Book(title="Artificial Intelligence: A Modern Approach", author="Stuart Russell", category="AI", year=2020),
    Book(title="Python Crash Course", author="Eric Matthes", category="Programming", year=2019),
    Book(title="Fluent Python", author="Luciano Ramalho", category="Programming", year=2022),
    Book(title="Design Patterns", author="Erich Gamma", category="Software Design", year=2004),
    Book(title="Machine Learning Yearning", author="Andrew Ng", category="AI", year=2020),
    Book(title="Data Science from Scratch", author="Joel Grus", category="Data Science", year=2019),
    Book(title="Hands-On Machine Learning", author="Aurélien Géron", category="AI", year=2022),
    Book(title="Introduction to Algorithms", author="Thomas H. Cormen", category="Computer Science", year=2009),
    Book(title="Operating System Concepts", author="Abraham Silberschatz", category="Computer Science", year=2018),
    Book(title="Computer Networks", author="Andrew S. Tanenbaum", category="Networking", year=2011),
    Book(title="Modern Web Development", author="Miroslav Kubat", category="Web Development", year=2023),
    Book(title="The Clean Coder", author="Robert C. Martin", category="Software Engineering", year=2011),
    Book(title="Introduction to Deep Learning", author="Eugene Charniak", category="AI", year=2019),
    Book(title="The Art of Computer Programming", author="Donald Knuth", category="Computer Science", year=2011),
    Book(title="Learn JavaScript Quickly", author="Code Quickly", category="Web Development", year=2020),
    Book(title="Learning SQL", author="Alan Beaulieu", category="Database", year=2022),
    Book(title="Database System Concepts", author="Abraham Silberschatz", category="Database", year=2019),
    Book(title="You Don’t Know JS Yet", author="Kyle Simpson", category="Programming", year=2020),
    Book(title="React Explained", author="Zac Gordon", category="Web Development", year=2021),
    Book(title="Effective Java", author="Joshua Bloch", category="Programming", year=2018),
    Book(title="Spring in Action", author="Craig Walls", category="Programming", year=2022),
    Book(title="The Mythical Man-Month", author="Fred Brooks", category="Software Engineering", year=1995),
    Book(title="The Phoenix Project", author="Gene Kim", category="DevOps", year=2013),
    Book(title="Site Reliability Engineering", author="Betsy Beyer", category="DevOps", year=2016),
]
    sample_users = [
            User(name="Minh Chiến", email="chien@example.com", phone="0123456789"),
            User(name="Nguyen Anh", email="supafire@gmail.com", phone="0987654321"),
        ]
    db.session.add_all(sample_books + sample_users)
    db.session.commit()

# ========== BOOK CRUD ==========

# GET all books + search + pagination
@app.route("/books", methods=["GET"])
def get_books():
    search = request.args.get("search", "")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 5))
    query = Book.query.filter(
        (Book.title.like(f"%{search}%")) |
        (Book.author.like(f"%{search}%")) |
        (Book.category.like(f"%{search}%"))
    )
    total = query.count()
    books = query.offset((page - 1) * limit).limit(limit).all()
    return jsonify({"total": total, "books": [b.to_dict() for b in books]})

# GET book by id
@app.route("/books/<int:id>", methods=["GET"])
def get_book(id):
    book = Book.query.get_or_404(id)
    return jsonify(book.to_dict())

# CREATE new book
@app.route("/books", methods=["POST"])
def add_book():
    data = request.json
    book = Book(**data)
    db.session.add(book)
    db.session.commit()
    return jsonify({"message": "Book added", "book": book.to_dict()}), 201

# UPDATE book
@app.route("/books/<int:id>", methods=["PUT"])
def update_book(id):
    book = Book.query.get_or_404(id)
    data = request.json
    for key, value in data.items():
        setattr(book, key, value)
    db.session.commit()
    return jsonify({"message": "Book updated", "book": book.to_dict()})

# DELETE book
@app.route("/books/<int:id>", methods=["DELETE"])
def delete_book(id):
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    return jsonify({"message": "Book deleted"})

# ========== USER CRUD ==========
@app.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

@app.route("/users", methods=["POST"])
def add_user():
    data = request.json
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User added", "user": user.to_dict()}), 201

# ========== BORROW RECORD ==========
@app.route("/borrow", methods=["POST"])
def borrow_book():
    data = request.json
    user_id = data["user_id"]
    book_id = data["book_id"]
    record = BorrowRecord(user_id=user_id, book_id=book_id,
                          borrow_date=data.get("borrow_date"),
                          return_date=data.get("return_date"),
                          status="borrowing")
    # Mark book unavailable
    book = Book.query.get(book_id)
    book.available = False
    db.session.add(record)
    db.session.commit()
    return jsonify({"message": "Book borrowed", "record": record.to_dict()})

@app.route("/return/<int:record_id>", methods=["PUT"])
def return_book(record_id):
    record = BorrowRecord.query.get_or_404(record_id)
    record.status = "returned"
    book = Book.query.get(record.book_id)
    book.available = True
    db.session.commit()
    return jsonify({"message": "Book returned", "record": record.to_dict()})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True)