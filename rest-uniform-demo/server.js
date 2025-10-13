import express from "express";
import bodyParser from "body-parser";
import bookRoutes from "./route/book.js";

const app = express();
app.use(bodyParser.json());

app.use("/books", bookRoutes);

app.get("/", (req, res) => {
  res.json({
    message: "Welcome to the REST Uniform Interface Demo",
    links: {
      books: "/books",
      example_create: { method: "POST", href: "/books" },
    },
  });
});

const PORT = 3000;
app.listen(PORT, () =>
  console.log(`Server running on http://localhost:${PORT}`)
);
