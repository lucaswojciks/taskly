import { api, type ListParams } from '@/lib/api'
import type { Tag } from '@/types'

/** GET /projects/{id}/tags — plain JSON array, accepts ?limit=&offset=. */
export async function listProjectTags(
  projectId: string,
  params?: ListParams,
): Promise<Tag[]> {
  const { data } = await api.get<Tag[]>(`/projects/${projectId}/tags`, { params })
  return data
}

/** POST /projects/{id}/tags */
export async function createProjectTag(projectId: string, name: string): Promise<Tag> {
  const { data } = await api.post<Tag>(`/projects/${projectId}/tags`, { name })
  return data
}
