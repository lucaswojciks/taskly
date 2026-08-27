const MONTHS_PT = [
  'jan',
  'fev',
  'mar',
  'abr',
  'mai',
  'jun',
  'jul',
  'ago',
  'set',
  'out',
  'nov',
  'dez',
]

/** ISO date string -> "29 ago 2026", or null when there is no deadline. */
export function formatDeadline(iso: string | null): string | null {
  if (!iso) {
    return null
  }
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return null
  }
  return `${date.getDate()} ${MONTHS_PT[date.getMonth()]} ${date.getFullYear()}`
}
