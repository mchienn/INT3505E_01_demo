from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, joinedload, subqueryload

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
    session.query(Book).delete()
    session.query(Author).delete()
    session.commit()
    
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


def solution_1_joinedload(session):
    print("[Query 1] SELECT authors.*, books.* FROM authors LEFT OUTER JOIN books")
    authors = session.query(Author).options(joinedload(Author.books)).all()
    print(f"→ Load {len(authors)} tác giả + sách trong 1 query\n")
    
    for author in authors:
        books = author.books
        print(f"✓ '{author.name}' có {len(books)} sách:")
        for book in books:
            print(f"   - {book.title}")
        print()


def solution_2_subqueryload(session):
    print("[Query 1] SELECT * FROM authors")
    authors = session.query(Author).options(subqueryload(Author.books)).all()
    print(f"→ {[f'id={a.id}' for a in authors]}")
    
    print("\n[Query 2] SELECT * FROM books WHERE author_id IN (1,2,3,4,5)")
    print(f"→ Load {len(authors)} tác giả + sách trong 2 queries\n")

    for author in authors:
        books = author.books
        print(f"✓ '{author.name}' có {len(books)} sách:")
        for book in books:
            print(f"   - {book.title}")
        print()


if __name__ == "__main__":
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    session1 = Session()
    seed_data(session1)
    solution_1_joinedload(session1)
    session1.close()

    session2 = Session()
    seed_data(session2)
    solution_2_subqueryload(session2)
    session2.close()