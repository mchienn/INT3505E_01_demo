import jwt from "jsonwebtoken";

const JWT_SECRET = "your-secret-key";
const TOKEN_EXPIRES_IN = "1h";
const TOKEN_ALGORITHM = "HS256";

const tokenBlacklist = new Set();

export const users = [
  { id: 1, username: "admin", password: "admin123", role: "admin" },
  { id: 2, username: "user", password: "user123", role: "user" },
];

export const generateToken = (user) => {
  const payload = {
    sub: user.id.toString(),
    userId: user.id,
    username: user.username,
    role: user.role,
    iat: Math.floor(Date.now() / 1000),
  };

  const token = jwt.sign(payload, JWT_SECRET, {
    expiresIn: TOKEN_EXPIRES_IN,
    algorithm: TOKEN_ALGORITHM,
  });

  return {
    token,
    expiresIn: 60 * 60,
  };
};

export const verifyToken = (token) => {
  try {
    const decoded = jwt.verify(token, JWT_SECRET, {
      algorithms: [TOKEN_ALGORITHM],
    });

    if (tokenBlacklist.has(token)) {
      return null;
    }

    return decoded;
  } catch (error) {
    return null;
  }
};

export const revokeToken = (token) => {
  tokenBlacklist.add(token);
  return true;
};

export const findUser = (username, password) => {
  return users.find(
    (user) => user.username === username && user.password === password
  );
};

export const findUserById = (id) => {
  return users.find((user) => user.id === id);
};
