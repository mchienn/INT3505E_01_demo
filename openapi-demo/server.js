import express from "express";
import swaggerUi from "swagger-ui-express";
import YAML from "yamljs";

const app = express();
const swaggerDocument = YAML.load("./openapi.yaml");

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerDocument));

let books = [
  { id: 1, title: "Clean Code", author: "Robert C. Martin" },
  { id: 2, title: "Design Patterns", author: "Erich Gamma" },
];

//  GET /books
app.get("/books", (req, res) => {
  res.json(books);
});

//  GET /books/:id
app.get("/books/:id", (req, res) => {
  const book = books.find((b) => b.id === parseInt(req.params.id));
  if (!book) return res.status(404).json({ error: "Book not found" });
  res.json(book);
});

//  POST /books (fix lỗi req.body undefined)
app.post("/books", (req, res) => {
  console.log("📩 Body nhận được:", req.body);

  // Kiểm tra dữ liệu hợp lệ
  if (!req.body || !req.body.title || !req.body.author) {
    return res.status(400).json({
      error: "Missing 'title' or 'author' in request body",
    });
  }

  const { title, author } = req.body;
  const newBook = { id: books.length + 1, title, author };
  books.push(newBook);

  res.status(201).json({
    message: "Book created successfully",
    data: newBook,
  });
});

//  PUT /books/:id
app.put("/books/:id", (req, res) => {
  const book = books.find((b) => b.id === parseInt(req.params.id));
  if (!book) return res.status(404).json({ error: "Book not found" });

  book.title = req.body.title || book.title;
  book.author = req.body.author || book.author;

  res.json({ message: "Book updated", data: book });
});

// DELETE /books/:id
app.delete("/books/:id", (req, res) => {
  const id = parseInt(req.params.id);
  books = books.filter((b) => b.id !== id);
  res.status(204).send();
});

app.get("/", (req, res) => {
  res.send(`<h2>OpenAPI Demo</h2>
  <p>👉 <a href="/api-docs">Xem tài liệu Swagger UI</a></p>`);
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`🚀 Server đang chạy tại http://localhost:${PORT}`);
  console.log(`📘 Swagger UI: http://localhost:${PORT}/api-docs`);
});
