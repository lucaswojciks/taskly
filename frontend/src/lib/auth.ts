const TOKEN_KEY = 'taskly.token'

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token)
  } catch {
    // storage unavailable (private mode, blocked) — nothing we can do
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY)
  } catch {
    // storage unavailable — nothing we can do
  }
}

export function isAuthenticated(): boolean {
  return getToken() !== null
}
