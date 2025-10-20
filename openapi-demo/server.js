import express from "express";
import swaggerUi from "swagger-ui-express";
import YAML from "yamljs";
import { findUser, generateToken, findUserById } from "./auth/jwt.js";
import { authenticate, authorize, logoutHandler } from "./auth/middleware.js";

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

// ========== JWT AUTH ROUTES ==========

// Route đăng nhập
app.post("/auth/login", (req, res) => {
  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).json({
      error: "Bad Request",
      message: "Username and password are required",
    });
  }

  // Xác thực người dùng
  const user = findUser(username, password);
  if (!user) {
    return res.status(401).json({
      error: "Unauthorized",
      message: "Invalid username or password",
    });
  }

  // Tạo JWT token
  const tokenData = generateToken(user);

  // Trả về token cho client
  res.json({
    message: "Login successful",
    token: tokenData.token,
    expiresIn: tokenData.expiresIn,
    tokenType: tokenData.tokenType,
    user: {
      id: user.id,
      username: user.username,
      role: user.role,
    },
  });
});

// Route đăng xuất
app.post("/auth/logout", authenticate, logoutHandler);

// Route công khai - ai cũng truy cập được
app.get("/public", (req, res) => {
  res.json({ message: "This is public data anyone can access" });
});

// Route được bảo vệ - chỉ user đã đăng nhập mới truy cập được
app.get("/protected", authenticate, (req, res) => {
  res.json({
    message: "This is protected data",
    user: req.user,
  });
});

// Route dành cho admin - chỉ user có role admin mới truy cập được
app.get("/admin", authenticate, authorize(["admin"]), (req, res) => {
  res.json({
    message: "Admin panel data",
    user: req.user,
  });
});

// Route để kiểm tra thông tin người dùng hiện tại
app.get("/auth/me", authenticate, (req, res) => {
  res.json({
    message: "Current user info",
    user: req.user,
  });
});

app.get("/", (req, res) => {
  res.send(`<h2>OpenAPI Demo</h2>
  <p>👉 <a href="/api-docs">Xem tài liệu Swagger UI</a></p>
  <p>🔐 <b>JWT Auth Test Routes:</b></p>
  <ul>
    <li><b>POST /auth/login</b> - Đăng nhập (body: { username, password })</li>
    <li><b>POST /auth/logout</b> - Đăng xuất (yêu cầu token)</li>
    <li><b>GET /public</b> - API công khai (không yêu cầu token)</li>
    <li><b>GET /protected</b> - API được bảo vệ (yêu cầu token)</li>
    <li><b>GET /admin</b> - API chỉ dành cho admin (yêu cầu token và role admin)</li>
    <li><b>GET /auth/me</b> - Lấy thông tin user hiện tại (yêu cầu token)</li>
  </ul>
  <p><i>Sử dụng Postman hoặc một công cụ API khác để test</i></p>`);
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`🚀 Server đang chạy tại http://localhost:${PORT}`);
  console.log(`📘 Swagger UI: http://localhost:${PORT}/api-docs`);
  console.log(`🔐 Test JWT Auth tại http://localhost:${PORT}/`);
});
