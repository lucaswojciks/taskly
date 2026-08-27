import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createProject, listProjects } from '@/lib/projects-api'
import type { Project } from '@/types'

export const PROJECTS_QUERY_KEY = ['projects'] as const

export function useProjects() {
  return useQuery<Project[]>({
    queryKey: PROJECTS_QUERY_KEY,
    queryFn: () => listProjects({ limit: 200 }),
  })
}

export function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => createProject(name),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PROJECTS_QUERY_KEY })
    },
  })
}
