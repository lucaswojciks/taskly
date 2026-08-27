import { api } from '@/lib/api'
import type { Attachment } from '@/types'

/**
 * POST /projects/{id}/tasks/{task_id}/attachments — multipart/form-data.
 * `onProgress` reports 0-100 while the file uploads.
 */
export async function uploadAttachment(
  projectId: string,
  taskId: string,
  file: File,
  onProgress?: (percent: number) => void,
): Promise<Attachment> {
  const { data } = await api.postForm<Attachment>(
    `/projects/${projectId}/tasks/${taskId}/attachments`,
    { file },
    {
      onUploadProgress: (event) => {
        if (onProgress && event.total) {
          onProgress(Math.round((event.loaded / event.total) * 100))
        }
      },
    },
  )
  return data
}

/** DELETE /projects/{id}/tasks/{task_id}/attachments/{attachment_id} */
export async function deleteAttachment(
  projectId: string,
  taskId: string,
  attachmentId: string,
): Promise<void> {
  await api.delete(
    `/projects/${projectId}/tasks/${taskId}/attachments/${attachmentId}`,
  )
}
