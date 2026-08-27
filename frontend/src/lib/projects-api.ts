import { api, type ListParams } from '@/lib/api'
import type { Project } from '@/types'

/** GET /projects — plain JSON array, accepts ?limit=&offset=. */
export async function listProjects(params?: ListParams): Promise<Project[]> {
  const { data } = await api.get<Project[]>('/projects', { params })
  return data
}

/** POST /projects */
export async function createProject(name: string): Promise<Project> {
  const { data } = await api.post<Project>('/projects', { name })
  return data
}
