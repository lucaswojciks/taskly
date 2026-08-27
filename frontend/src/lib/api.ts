import axios, { type AxiosError } from 'axios'
import { clearToken, getToken } from '@/lib/auth'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

/**
 * Centralised HTTP client for the Taskly backend.
 *
 * Backend contract notes:
 * - `POST /auth/login` takes JSON `{ email, password }` (not OAuth2 form-urlencoded).
 * - List endpoints return a plain JSON array and accept `?limit=&offset=`
 *   (no pagination envelope).
 * - Domain errors come back as `{ "error": { "code", "message" } }`;
 *   request-validation errors as FastAPI's `{ "detail": [...] }`.
 */
export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach the bearer token from localStorage to every request.
api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// On a 401 from an authenticated request, drop the token and bounce to /login.
// The auth endpoints are exempt: a failed login/register must surface its error
// to the form instead of triggering a redirect.
const AUTH_ENDPOINTS = ['/auth/login', '/auth/register']

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const url = error.config?.url ?? ''
    const isAuthEndpoint = AUTH_ENDPOINTS.some((path) => url.includes(path))
    if (error.response?.status === 401 && !isAuthEndpoint) {
      clearToken()
      if (window.location.pathname !== '/login') {
        window.location.assign('/login')
      }
    }
    return Promise.reject(error)
  },
)

/** Query params shared by every list endpoint. */
export interface ListParams {
  limit?: number
  offset?: number
}
