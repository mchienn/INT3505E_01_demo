import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const books = JSON.parse(
  readFileSync(join(__dirname, "../data/book.json"), "utf-8")
);

export const getBooks = (req, res) => {
  res.status(200).json({
    message: "List of all books",
    data: books,
  });
};

export const getBookById = (req, res) => {
  const book = books.find((b) => b.id === parseInt(req.params.id));
  if (!book) return res.status(404).json({ error: "Book not found" });

  res.status(200).json({
    message: "Book details",
    data: book,
  });
};

export const createBook = (req, res) => {
  const { title, author } = req.body;
  const newBook = { id: books.length + 1, title, author };
  books.push(newBook);

  res.status(201).json({
    message: "Book created successfully",
    data: newBook,
    links: {
      self: `/books/${newBook.id}`,
      collection: "/books",
    },
  });
};
