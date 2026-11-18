/** Address of the server for this build, without a trailing /api. */
export function apiOrigin(): string {
  const configured = (
    process.env.REACT_APP_API_URL ||
    "https://class-cancellation-backend.onrender.com/api"
  ).trim();
  return configured.replace(/\/+$/, "").replace(/\/api$/i, "");
}
