import jwt from "jsonwebtoken";

// Token settings
const JWT_SECRET = "your-secret-key";
const TOKEN_EXPIRES_IN = "1h"; // Token hết hạn sau 1 giờ
const TOKEN_ALGORITHM = "HS256"; // Có thể sử dụng "RS256" với key pairs cho production

// Store cho revoked/blacklisted tokens (trong thực tế nên dùng Redis hoặc DB)
const tokenBlacklist = new Set();

// Danh sách người dùng mẫu (trong thực tế nên lưu vào database)
export const users = [
  { id: 1, username: "admin", password: "admin123", role: "admin" },
  { id: 2, username: "user", password: "user123", role: "user" },
];

// Tạo JWT token
export const generateToken = (user) => {
  // Tạo payload với các claims tiêu chuẩn
  const payload = {
    sub: user.id.toString(), // subject (người dùng)
    userId: user.id,
    username: user.username,
    role: user.role,
    iat: Math.floor(Date.now() / 1000), // issued at time (thời điểm phát hành)
  };

  // Tạo token
  const token = jwt.sign(payload, JWT_SECRET, {
    expiresIn: TOKEN_EXPIRES_IN,
    algorithm: TOKEN_ALGORITHM,
  });

  return {
    token,
    expiresIn: 60 * 60, // 1 hour in seconds
    tokenType: "Bearer",
  };
};

// Verify JWT token
export const verifyToken = (token) => {
  try {
    // Verify signature and expiration
    const decoded = jwt.verify(token, JWT_SECRET, {
      algorithms: [TOKEN_ALGORITHM],
    });

    // Check if token is blacklisted (revoked)
    if (tokenBlacklist.has(token)) {
      console.error("Token is blacklisted");
      return null;
    }

    return decoded;
  } catch (error) {
    console.error("JWT verification failed:", error.message);
    return null;
  }
};

// Thêm token vào blacklist (khi logout)
export const revokeToken = (token) => {
  try {
    // Thêm vào blacklist
    tokenBlacklist.add(token);
    return true;
  } catch (error) {
    console.error("Token revocation failed:", error.message);
    return false;
  }
};

// Tìm user theo username/password
export const findUser = (username, password) => {
  // Trong thực tế nên hash password và so sánh hash
  return users.find(
    (user) => user.username === username && user.password === password
  );
};

// Tìm user theo id
export const findUserById = (id) => {
  return users.find((user) => user.id === id);
};
