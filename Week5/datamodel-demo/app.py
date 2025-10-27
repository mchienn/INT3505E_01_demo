from flask import Flask, request, jsonify
from database import init_db, db
from models import Book, User, Borrowing, Author, BookAuthor
from datetime import date, timedelta

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///library.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
init_db(app)

# --- Tạo dữ liệu mẫu ---
def seed_data():
    # Xóa dữ liệu cũ
    Borrowing.query.delete()
    BookAuthor.query.delete()
    Book.query.delete()
    Author.query.delete()
    User.query.delete()
    db.session.commit()

    # --- Fake AUTHORS ---
    authors = [
        Author(name="J.K Rowling", address="London, UK", phone="123456789", email="jkrowling@example.com"),
        Author(name="Robert C. Martin", address="Chicago, USA", phone="987654321", email="unclebob@example.com"),
        Author(name="Andrew Ng", address="Stanford, USA", phone="567890123", email="andrewng@example.com"),
        Author(name="Donald Knuth", address="California, USA", phone="102938475", email="knuth@example.com"),
        Author(name="Joshua Bloch", address="New York, USA", phone="192837465", email="bloch@example.com"),
        Author(name="Luciano Ramalho", address="São Paulo, Brazil", phone="384756192", email="luciano@example.com"),
        Author(name="Stuart Russell", address="Berkeley, USA", phone="293847561", email="russell@example.com"),
        Author(name="Craig Walls", address="Texas, USA", phone="948372615", email="craig@example.com"),
    ]
    db.session.add_all(authors)
    db.session.commit()

    # --- Fake BOOKS ---
    books = [
        Book(title="NAVER AI Hackathon", author="Tran B", category="Programming", year=2021, available=True),
        Book(title="Harry Potter", author="J.K Rowling", category="Fiction", year=2003, available=True),
        Book(title="Lord of the Rings", author="J.R.R. Tolkien", category="Fantasy", year=2015, available=True),
        Book(title="Clean Code", author="Robert C. Martin", category="Software Engineering", year=2008, available=True),
        Book(title="Deep Learning with Python", author="François Chollet", category="AI", year=2021, available=True),
        Book(title="Artificial Intelligence: A Modern Approach", author="Stuart Russell", category="AI", year=2020, available=True),
        Book(title="Effective Java", author="Joshua Bloch", category="Programming", year=2018, available=True),
        Book(title="Fluent Python", author="Luciano Ramalho", category="Programming", year=2022, available=True),
        Book(title="Spring in Action", author="Craig Walls", category="Programming", year=2022, available=True),
        Book(title="The Art of Computer Programming", author="Donald Knuth", category="Computer Science", year=2011, available=True),
    ]
    db.session.add_all(books)
    db.session.commit()

    # --- Fake USERS ---
    users = [
        User(name="Minh Chien", email="chien@example.com", phone="0123456789"),
        User(name="Nguyen Nhat Anh", email="anh@example.com", phone="0987654321"),
        User(name="Tran Le Bao Minh", email="minhtran@example.com", phone="0112233445"),
        User(name="Le Ha Anh Tuan", email="hale@example.com", phone="0998877665"),
    ]
    db.session.add_all(users)
    db.session.commit()

    # --- BookAuthor: mapping nhiều-nhiều giữa Book và Author ---
    pairs = [
        (1, 3),  # NAVER AI Hackathon - Andrew Ng
        (2, 1),  # Harry Potter - J.K Rowling
        (3, 4),  # Lord of the Rings - Donald Knuth
        (4, 2),  # Clean Code - Robert Martin
        (5, 3),  # Deep Learning with Python - Andrew Ng
        (6, 7),  # AIMA - Stuart Russell
        (7, 5),  # Effective Java - Joshua Bloch
        (8, 6),  # Fluent Python - Luciano Ramalho
        (9, 8),  # Spring in Action - Craig Walls
        (10, 4), # TAOCP - Donald Knuth
    ]
    book_authors = [BookAuthor(book_id=b, author_id=a) for b, a in pairs]
    db.session.add_all(book_authors)
    db.session.commit()

    # --- Borrowing (giả lập mượn sách) ---
    today = date.today()
    borrow_samples = [
        Borrowing(user_id=1, book_id=2, borrow_date=today - timedelta(days=10),
                     due_date=today - timedelta(days=2), return_date=None, fine_amount=0),
        Borrowing(user_id=2, book_id=3, borrow_date=today - timedelta(days=5),
                     due_date=today + timedelta(days=5), return_date=None, fine_amount=0),
        Borrowing(user_id=3, book_id=6, borrow_date=today - timedelta(days=20),
                     due_date=today - timedelta(days=10), return_date=today - timedelta(days=8), fine_amount=0),
        Borrowing(user_id=4, book_id=1, borrow_date=today - timedelta(days=2),
                     due_date=today + timedelta(days=8), return_date=None, fine_amount=0),
    ]
    db.session.add_all(borrow_samples)
    db.session.commit()
    
    print(f"✅ Seeded {len(books)} books, {len(authors)} authors, {len(users)} users, {len(borrow_samples)} borrowings")

# ========== BOOK CRUD ==========

# GET all books + search + pagination
@app.route("/books", methods=["GET"])
def get_books():
    search = request.args.get("search", "")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 5))
    cursor = request.args.get("cursor")
    offset_raw = request.args.get("offset")
    offset = None
    if offset_raw is not None:
        try:
            offset = max(int(offset_raw), 0)
        except ValueError:
            return jsonify({
                "error": "INVALID_OFFSET",
                "message": "Offset must be a non-negative integer",
            }), 400
    query = Book.query.filter(
        (Book.title.like(f"%{search}%")) |
        (Book.author.like(f"%{search}%")) |
        (Book.category.like(f"%{search}%"))
    )
    query = query.order_by(Book.id.asc())

    if cursor is not None:
        try:
            last_id = int(cursor)
        except ValueError:
            return jsonify({
                "error": "INVALID_CURSOR",
                "message": "Cursor must be a numeric book id",
            }), 400

        window = query.filter(Book.id > last_id).limit(limit + 1).all()
        items = window[:limit]
        next_cursor = window[-1].id if len(window) > limit else None
        return jsonify({
            "mode": "cursor",
            "limit": limit,
            "count": len(items),
            "next_cursor": next_cursor,
            "books": [b.to_dict() for b in items],
        })

    start = offset if offset is not None else (page - 1) * limit
    total = query.count()
    books = query.offset(start).limit(limit).all()
    return jsonify({
        "mode": "page",
        "total": total,
        "page": page,
        "limit": limit,
        "offset": start,
        "books": [b.to_dict() for b in books],
    })

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


@app.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])


@app.route("/authors", methods=["GET"])
def get_authors():
    authors = Author.query.all()
    return jsonify([a.to_dict() for a in authors])

@app.route("/borrowings", methods=["GET"])
def get_borrowings():
    borrowings = Borrowing.query.all()
    return jsonify([b.to_dict() for b in borrowings])

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True)