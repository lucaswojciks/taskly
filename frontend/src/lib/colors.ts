/** Deterministic accent colour for a project, derived from its id. */

const PROJECT_COLORS = [
  '#10b981', // emerald
  '#8b5cf6', // violet
  '#3b82f6', // blue
  '#ec4899', // pink
  '#f59e0b', // amber
  '#14b8a6', // teal
  '#6366f1', // indigo
  '#ef4444', // red
]

function hash(value: string): number {
  let result = 0
  for (let i = 0; i < value.length; i += 1) {
    result = (result * 31 + value.charCodeAt(i)) | 0
  }
  return Math.abs(result)
}

export function projectColor(id: string): string {
  return PROJECT_COLORS[hash(id) % PROJECT_COLORS.length]
}

/** Soft pastel pill classes for a tag, derived from its name. */
const TAG_CLASSES = [
  'bg-sky-100 text-sky-700',
  'bg-violet-100 text-violet-700',
  'bg-amber-100 text-amber-700',
  'bg-emerald-100 text-emerald-700',
  'bg-rose-100 text-rose-700',
  'bg-cyan-100 text-cyan-700',
  'bg-indigo-100 text-indigo-700',
]

export function tagClasses(name: string): string {
  return TAG_CLASSES[hash(name.toLowerCase()) % TAG_CLASSES.length]
}
