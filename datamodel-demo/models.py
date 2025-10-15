from database import db

# --- Book model ---
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    author = db.Column(db.String(100))
    category = db.Column(db.String(100))
    year = db.Column(db.Integer)
    available = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "category": self.category,
            "year": self.year,
            "available": self.available
        }

# --- User model ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "phone": self.phone}

# --- BorrowRecord model ---
class BorrowRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"))
    borrow_date = db.Column(db.String(20))
    return_date = db.Column(db.String(20))
    status = db.Column(db.String(20))  # "borrowing" | "returned"

    user = db.relationship("User", backref="borrow_records")
    book = db.relationship("Book", backref="borrow_records")

    def to_dict(self):
        return {
            "id": self.id,
            "user": self.user.to_dict() if self.user else None,
            "book": self.book.to_dict() if self.book else None,
            "borrow_date": self.borrow_date,
            "return_date": self.return_date,
            "status": self.status
        }
