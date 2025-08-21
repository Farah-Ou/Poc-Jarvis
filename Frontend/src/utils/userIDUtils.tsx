/**
 * Generates a random 8-character alphanumeric string
 */
function generateShortId(): string {
  const chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let id = "";
  for (let i = 0; i < 8; i++) {
    id += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return id;
}

/**
 * Get or create a persistent user session ID (8 chars)
 * Stored in localStorage — survives refresh, not cleared automatically
 */
export function getOrCreateUserId(): string {
  const key = "app_user_id"; // Key name for localStorage
  const existingId = localStorage.getItem(key);

  if (existingId) {
    return existingId;
  }

  const newId = generateShortId();
  localStorage.setItem(key, newId);
  console.log(`Generated new user ID: ${newId}`); // Optional: debug
  return newId;
}

/**
 * Optional: Manually clear the ID (only when you decide)
 */
export function clearUserId() {
  localStorage.removeItem("app_user_id");
}

/**
 * Optional: Get current ID without creating
 */
export function getUserId() {
  return localStorage.getItem("app_user_id");
}
