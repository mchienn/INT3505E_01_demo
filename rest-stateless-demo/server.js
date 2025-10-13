const express = require("express");
const session = require("express-session");
const app = express();

app.use(express.json());

// Khởi tạo session (Stateful)
app.use(
  session({
    secret: "secret-key",
    resave: false,
    saveUninitialized: true,
  })
);

// ---------- Stateless ----------
app.get("/stateless/greet", (req, res) => {
  const name = req.query.name;
  if (!name) {
    return res.status(400).json({ message: "Missing name in query" });
  }

  res.json({ message: `Hello ${name}, from stateless API` });
});

// ---------- Stateful ----------
app.post("/stateful/login", (req, res) => {
  const { name } = req.body;
  if (!name) {
    return res.status(400).json({ message: "Missing name in body" });
  }

  req.session.user = name;
  res.json({ message: `Logged in as ${name}` });
});

app.get("/stateful/greet", (req, res) => {
  const user = req.session.user;
  if (!user) {
    return res.status(401).json({ message: "Not logged in" });
  }

  res.json({ message: `Hello ${user}, from stateful API` });
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
