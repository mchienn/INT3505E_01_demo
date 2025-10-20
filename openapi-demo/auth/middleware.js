import { verifyToken, findUserById, revokeToken } from "./jwt.js";

// Authentication middleware
export const authenticate = (req, res, next) => {
  try {
    // Lấy token từ header
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return res.status(401).json({
        error: "Unauthorized",
        message: "Authentication required",
      });
    }

    // Extract token
    const token = authHeader.split(" ")[1];

    // Store token cho việc revoke khi cần
    req.token = token;

    // Verify token
    const decoded = verifyToken(token);
    if (!decoded) {
      // Token không hợp lệ - trả về lỗi 401
      return res.status(401).json({
        error: "Unauthorized",
        message: "Invalid or expired token",
        code: "token_invalid",
      });
    }

    // Kiểm tra thời gian hết hạn
    const currentTime = Math.floor(Date.now() / 1000);
    if (decoded.exp && decoded.exp < currentTime) {
      return res.status(401).json({
        error: "Unauthorized",
        message: "Token expired",
        code: "token_expired",
      });
    }

    // Đưa thông tin user vào request
    const user = findUserById(decoded.userId);
    if (!user) {
      return res.status(401).json({
        error: "Unauthorized",
        message: "User not found",
      });
    }

    // Không gửi password đi tiếp
    const { password, ...userData } = user;
    req.user = userData;

    // Lưu thông tin token đã giải mã
    req.decoded = decoded;

    // Đi tiếp
    next();
  } catch (error) {
    console.error("Auth error:", error);
    return res.status(500).json({
      error: "Server Error",
      message: "Authentication failed",
    });
  }
};

// Role-based authorization middleware
export const authorize = (roles = []) => {
  return (req, res, next) => {
    // Ensure req.user exists (authenticate middleware ran first)
    if (!req.user) {
      return res.status(401).json({
        error: "Unauthorized",
        message: "Authentication required",
      });
    }

    // Convert string to array if needed
    if (typeof roles === "string") {
      roles = [roles];
    }

    // Check if user's role is in the allowed roles
    if (roles.length > 0 && !roles.includes(req.user.role)) {
      return res.status(403).json({
        error: "Forbidden",
        message: "You do not have permission to access this resource",
      });
    }
    // User has required role
    next();
  };
};

// Middleware đăng xuất (revoke token)
export const logoutHandler = (req, res) => {
  try {
    // Token đã được lưu trong req.token từ middleware authenticate
    const token = req.token;

    if (!token) {
      return res.status(400).json({
        error: "Bad Request",
        message: "No token provided",
      });
    }

    // Revoke token (đưa vào blacklist)
    const revoked = revokeToken(token);

    if (!revoked) {
      return res.status(500).json({
        error: "Server Error",
        message: "Failed to logout",
      });
    }

    return res.json({
      message: "Logged out successfully",
    });
  } catch (error) {
    console.error("Logout error:", error);
    return res.status(500).json({
      error: "Server Error",
      message: "Failed to logout",
    });
  }
};
