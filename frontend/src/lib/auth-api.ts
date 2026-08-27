import { api } from '@/lib/api'
import type { AuthToken, User } from '@/types'

export interface Credentials {
  email: string
  password: string
}

/** POST /auth/login — JSON body, returns the access token. */
export async function loginRequest(credentials: Credentials): Promise<AuthToken> {
  const { data } = await api.post<AuthToken>('/auth/login', credentials)
  return data
}

/** POST /auth/register — creates the user (does not log in). */
export async function registerRequest(credentials: Credentials): Promise<User> {
  const { data } = await api.post<User>('/auth/register', credentials)
  return data
}

/** GET /auth/me — the currently authenticated user. */
export async function meRequest(): Promise<User> {
  const { data } = await api.get<User>('/auth/me')
  return data
}
