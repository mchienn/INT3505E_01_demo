import { verifyToken, findUserById, revokeToken } from "./jwt.js";

export const authenticate = (req, res, next) => {
  try {
    const authHeader = req.headers.authorization?.trim();

    if (!authHeader) {
      return res.status(401).json({
        error: "Unauthorized",
        message: "Authentication required",
      });
    }

    let token = authHeader;
    if (authHeader.toLowerCase().startsWith("bearer ")) {
      token = authHeader.slice(7).trim();
    }

    if (!token) {
      return res.status(401).json({
        error: "Unauthorized",
        message: "Authentication required",
      });
    }

    req.token = token;

    const decoded = verifyToken(token);
    if (!decoded) {
      return res.status(401).json({
        error: "Unauthorized",
        message: "Invalid or expired token",
      });
    }

    const user = findUserById(decoded.userId);
    if (!user) {
      return res.status(401).json({
        error: "Unauthorized",
        message: "User not found",
      });
    }

    const { password, ...userData } = user;
    req.user = userData;

    next();
  } catch (error) {
    return res.status(500).json({
      error: "Server Error",
      message: "Authentication failed",
    });
  }
};

export const authorize = (roles = []) => {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        error: "Unauthorized",
        message: "Authentication required",
      });
    }

    const allowedRoles = Array.isArray(roles) ? roles : [roles];

    if (allowedRoles.length > 0 && !allowedRoles.includes(req.user.role)) {
      return res.status(403).json({
        error: "Forbidden",
        message: "Insufficient permissions",
      });
    }

    next();
  };
};

export const logoutHandler = (req, res) => {
  try {
    const token = req.token;

    if (!token) {
      return res.status(400).json({
        error: "Bad Request",
        message: "No token provided",
      });
    }

    revokeToken(token);

    res.json({ message: "Logged out successfully" });
  } catch (error) {
    res.status(500).json({
      error: "Server Error",
      message: "Failed to logout",
    });
  }
};
