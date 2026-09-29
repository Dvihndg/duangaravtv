/*
 * Frontend runtime configuration.
 *
 * Keep this empty when the static frontend and /api/v1 share the same origin
 * (for example, the included Vercel deployment). For a separate static host,
 * set this to the public backend API base URL, including /api/v1:
 *
 * window.GARAGE_API_BASE = "https://api.example.com/api/v1";
 *
 * For a temporary preview, ?api=https%3A%2F%2Fapi.example.com%2Fapi%2Fv1
 * is also accepted and does not require editing this file.
 */
const apiFromQuery = new URLSearchParams(window.location.search).get("api");
window.GARAGE_API_BASE = window.GARAGE_API_BASE || apiFromQuery || "";
