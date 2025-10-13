import express from "express";
import {
  getBooks,
  getBookById,
  createBook,
} from "../controlllers/bookController.js";

const router = express.Router();

router.get("/", getBooks);
router.get("/:id", getBookById);
router.post("/", createBook);

export default router;
