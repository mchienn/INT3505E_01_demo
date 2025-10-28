from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

Base = declarative_base()


class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    books = relationship("Book", back_populates="author")


class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    author = relationship("Author", back_populates="books")


def seed_data(session):
    authors_data = [
        ("J.K. Rowling", ["Harry Potter 1", "Harry Potter 2", "Harry Potter 3"]),
        ("George R.R. Martin", ["Game of Thrones 1", "Game of Thrones 2", "Game of Thrones 3", "Game of Thrones 4"]),
        ("J.R.R. Tolkien", ["The Hobbit", "LOTR 1", "LOTR 2", "LOTR 3"]),
        ("Stephen King", ["The Shining", "It", "Carrie", "Misery", "The Stand"]),
        ("Agatha Christie", ["Murder on the Orient Express", "Death on the Nile", "And Then There Were None"]),
    ]

    for author_name, book_titles in authors_data:
        author = Author(name=author_name)
        session.add(author)
        session.flush()
        for title in book_titles:
            book = Book(title=title, author_id=author.id)
            session.add(book)
    session.commit()


def demonstrate_n_plus_1_problem(session):
    print("\n[Query 1] SELECT * FROM authors")
    authors = session.query(Author).all()
    print(f"→ Tìm thấy {len(authors)} tác giả\n")
    
    for i, author in enumerate(authors, start=1):
        print(f"[Query {i+1}] SELECT * FROM books WHERE author_id = {author.id}")
        books = author.books
        print(f"→ Tác giả '{author.name}' có {len(books)} sách:")
        for book in books:
            print(f"   - {book.title}")
        print()


if __name__ == "__main__":
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    seed_data(session)
    demonstrate_n_plus_1_problem(session)
    session.close()
