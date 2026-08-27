/** Domain types mirroring the Taskly backend schemas. */

export type TaskStatus = 'not_started' | 'in_progress' | 'done' | 'cancelled'

export interface User {
  id: string
  email: string
  created_at: string
}

export interface AuthToken {
  access_token: string
  token_type: string
  expires_in: number
}

export interface Project {
  id: string
  name: string
  created_at: string
  updated_at: string
}

export interface Tag {
  id: string
  project_id: string
  name: string
  created_at: string
  updated_at: string
}

export interface Attachment {
  id: string
  file_name: string
  content_type: string
  uploaded_at: string
  url: string
}

export interface Task {
  id: string
  project_id: string
  title: string
  short_description: string
  full_description: string
  deadline: string | null
  status: TaskStatus
  tags: Tag[]
  attachments: Attachment[]
  created_at: string
  updated_at: string
}

export interface ApiError {
  error: {
    code: string
    message: string
  }
}
