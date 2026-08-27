import { useCallback, useState } from 'react'
import { clearToken, getToken, setToken } from '@/lib/auth'

/**
 * Minimal auth state helper for the skeleton. Route protection itself reads the
 * token synchronously (see ProtectedRoute); this hook is a convenience for the
 * login/register screens to be built next.
 */
export function useAuth() {
  const [token, setTokenState] = useState<string | null>(() => getToken())

  const login = useCallback((newToken: string) => {
    setToken(newToken)
    setTokenState(newToken)
  }, [])

  const logout = useCallback(() => {
    clearToken()
    setTokenState(null)
  }, [])

  return { token, isAuthenticated: token !== null, login, logout }
}
