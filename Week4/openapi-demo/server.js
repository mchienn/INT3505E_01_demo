import express from "express";
import swaggerUi from "swagger-ui-express";
import YAML from "yamljs";
import { findUser, generateToken } from "./auth/jwt.js";
import { authenticate, authorize, logoutHandler } from "./auth/middleware.js";

const app = express();
const swaggerDocument = YAML.load("./openapi.yaml");

app.use(express.json());
app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerDocument));

let books = [
  { id: 1, title: "Clean Code", author: "Robert C. Martin" },
  { id: 2, title: "Design Patterns", author: "Erich Gamma" },
];

app.post("/auth/login", (req, res) => {
  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).json({
      error: "Bad Request",
      message: "Username and password are required",
    });
  }

  const user = findUser(username, password);
  if (!user) {
    return res.status(401).json({
      error: "Unauthorized",
      message: "Invalid username or password",
    });
  }

  const tokenData = generateToken(user);

  res.json({
    message: "Login successful",
    token: tokenData.token,
    expiresIn: tokenData.expiresIn,
    user: {
      id: user.id,
      username: user.username,
      role: user.role,
    },
  });
});

app.post("/auth/logout", authenticate, logoutHandler);

app.get("/auth/me", authenticate, (req, res) => {
  res.json({
    message: "Current user info",
    user: req.user,
  });
});

app.get("/books", authenticate, (req, res) => {
  res.json(books);
});

app.get("/books/:id", authenticate, (req, res) => {
  const bookId = Number(req.params.id);
  const book = books.find((entry) => entry.id === bookId);

  if (!book) {
    return res.status(404).json({
      error: "Not Found",
      message: "Book not found",
    });
  }

  res.json(book);
});

app.post("/books", authenticate, authorize(["admin"]), (req, res) => {
  const { title, author } = req.body || {};

  if (!title || !author) {
    return res.status(400).json({
      error: "Bad Request",
      message: "Both title and author are required",
    });
  }

  const newBook = { id: books.length + 1, title, author };
  books.push(newBook);

  res.status(201).json({
    message: "Book created successfully",
    data: newBook,
  });
});

app.put("/books/:id", authenticate, authorize(["admin"]), (req, res) => {
  const bookId = Number(req.params.id);
  const book = books.find((entry) => entry.id === bookId);

  if (!book) {
    return res.status(404).json({
      error: "Not Found",
      message: "Book not found",
    });
  }

  book.title = req.body?.title || book.title;
  book.author = req.body?.author || book.author;

  res.json({
    message: "Book updated successfully",
    data: book,
  });
});

app.delete("/books/:id", authenticate, authorize(["admin"]), (req, res) => {
  const bookId = Number(req.params.id);
  const existingLength = books.length;
  books = books.filter((entry) => entry.id !== bookId);

  if (books.length === existingLength) {
    return res.status(404).json({
      error: "Not Found",
      message: "Book not found",
    });
  }

  res.status(204).send();
});

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Swagger UI available at http://localhost:${PORT}/api-docs`);
});
