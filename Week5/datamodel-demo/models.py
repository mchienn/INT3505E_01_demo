from database import db
from datetime import date

class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    year = db.Column(db.Integer)
    available = db.Column(db.Boolean, default=True)
    
    # Relationships
    book_authors = db.relationship("BookAuthor", back_populates="book", cascade="all, delete-orphan")
    borrowings = db.relationship("Borrowing", back_populates="book", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "category": self.category,
            "year": self.year,
            "available": self.available
        }

class Author(db.Model):
    __tablename__ = "authors"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    
    # Relationships
    book_authors = db.relationship("BookAuthor", back_populates="author", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "phone": self.phone,
            "email": self.email
        }

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    
    # Relationships
    borrowings = db.relationship("Borrowing", back_populates="user", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone
        }

class BookAuthor(db.Model):
    __tablename__ = "book_authors"
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("authors.id"), nullable=False)
    
    # Relationships
    book = db.relationship("Book", back_populates="book_authors")
    author = db.relationship("Author", back_populates="book_authors")
    
    def to_dict(self):
        return {
            "id": self.id,
            "book_id": self.book_id,
            "author_id": self.author_id
        }

class Borrowing(db.Model):
    __tablename__ = "borrowings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    borrow_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)
    fine_amount = db.Column(db.Float, default=0.0)
    
    # Relationships
    user = db.relationship("User", back_populates="borrowings")
    book = db.relationship("Book", back_populates="borrowings")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "book_id": self.book_id,
            "borrow_date": self.borrow_date.isoformat() if self.borrow_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "return_date": self.return_date.isoformat() if self.return_date else None,
            "fine_amount": self.fine_amount
        }