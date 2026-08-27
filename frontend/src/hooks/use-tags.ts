import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createProjectTag, listProjectTags } from '@/lib/tags-api'
import type { Tag } from '@/types'

export function projectTagsQueryKey(projectId: string | null) {
  return ['projects', projectId, 'tags'] as const
}

export function useProjectTags(projectId: string | null) {
  return useQuery<Tag[]>({
    queryKey: projectTagsQueryKey(projectId),
    queryFn: () => listProjectTags(projectId as string, { limit: 200 }),
    enabled: projectId !== null,
  })
}

export function useCreateTag(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => createProjectTag(projectId, name),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: projectTagsQueryKey(projectId) })
    },
  })
}
