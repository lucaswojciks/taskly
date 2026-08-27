import { api, type ListParams } from '@/lib/api'
import type { Task, TaskStatus } from '@/types'

/** GET /projects/{id}/tasks — plain JSON array, accepts ?limit=&offset=. */
export async function listProjectTasks(
  projectId: string,
  params?: ListParams,
): Promise<Task[]> {
  const { data } = await api.get<Task[]>(`/projects/${projectId}/tasks`, { params })
  return data
}

export interface CreateTaskPayload {
  title: string
  short_description: string
  full_description?: string
  deadline?: string | null
  status?: TaskStatus
  tag_ids?: string[]
}

/** POST /projects/{id}/tasks */
export async function createProjectTask(
  projectId: string,
  payload: CreateTaskPayload,
): Promise<Task> {
  const { data } = await api.post<Task>(`/projects/${projectId}/tasks`, payload)
  return data
}

/**
 * PATCH body — only the keys present are applied. `deadline: null` clears it;
 * `tag_ids` replaces the whole set.
 */
export interface UpdateTaskPayload {
  title?: string
  short_description?: string
  full_description?: string
  deadline?: string | null
  status?: TaskStatus
  tag_ids?: string[]
}

/** PATCH /projects/{id}/tasks/{task_id} */
export async function updateProjectTask(
  projectId: string,
  taskId: string,
  patch: UpdateTaskPayload,
): Promise<Task> {
  const { data } = await api.patch<Task>(
    `/projects/${projectId}/tasks/${taskId}`,
    patch,
  )
  return data
}

/** DELETE /projects/{id}/tasks/{task_id} */
export async function deleteProjectTask(
  projectId: string,
  taskId: string,
): Promise<void> {
  await api.delete(`/projects/${projectId}/tasks/${taskId}`)
}
