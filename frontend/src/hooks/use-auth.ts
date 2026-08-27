import { useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { meRequest } from '@/lib/auth-api'
import { clearToken, getToken, setToken } from '@/lib/auth'
import type { User } from '@/types'

export const ME_QUERY_KEY = ['auth', 'me'] as const

/**
 * The currently authenticated user (GET /auth/me). Only runs when a token is
 * present; a 401 here is handled globally by the axios interceptor (token
 * cleared, redirect to /login).
 */
export function useCurrentUser() {
  return useQuery<User>({
    queryKey: ME_QUERY_KEY,
    queryFn: meRequest,
    enabled: getToken() !== null,
    retry: false,
    staleTime: 5 * 60_000,
  })
}

/** Imperative auth actions for the login / register / logout flows. */
export function useAuth() {
  const queryClient = useQueryClient()

  const login = useCallback(
    (token: string) => {
      setToken(token)
      void queryClient.invalidateQueries({ queryKey: ME_QUERY_KEY })
    },
    [queryClient],
  )

  const logout = useCallback(() => {
    clearToken()
    queryClient.clear()
  }, [queryClient])

  return {
    isAuthenticated: getToken() !== null,
    login,
    logout,
  }
}
