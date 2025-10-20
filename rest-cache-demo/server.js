const express = require("express");
const crypto = require("crypto");
const app = express();

//data
const productData = {
  id: 42,
  name: "Logitech MX Master Toronto 3S",
  price: 109.98,
  inStock: true,
  gap: 100,
  shippingStatus: "None",
};

app.get("/product", (req, res) => {
  // tạo data với json và etag
  const body = JSON.stringify(productData);
  const etag = `"${crypto.createHash("md5").update(body).digest("hex")}"`;

  // xem client có gửi etag ko
  if (req.headers["if-none-match"] === etag) {
    console.log("[ETag MATCH] Trả về 304 Not Modified");
    return res.status(304).end(); // Không gửi lại data nếu giống nhau
  }

  //trả data và etag mới
  res.set("Cache-Control", "public, max-age=100"); // Cho phép cache nếu có ETag
  res.set("ETag", etag);

  console.log("[ETag MISMATCH or missing] Trả về 200 OK + JSON");
  console.log("Server generated ETag:", etag);
  console.log("Client sent If-None-Match:", req.headers["if-none-match"]);

  res.json(productData);
});

const PORT = 4000;
app.listen(PORT, () => {
  console.log(`🔁 ETag demo running at http://localhost:${PORT}/product`);
});
