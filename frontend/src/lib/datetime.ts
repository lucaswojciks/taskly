/** ISO string -> value for `<input type="datetime-local">` (local time). */
export function isoToDatetimeLocal(iso: string | null): string {
  if (!iso) {
    return ''
  }
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  const pad = (value: number) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
    date.getHours(),
  )}:${pad(date.getMinutes())}`
}

/** `<input type="datetime-local">` value (local time) -> ISO string with timezone. */
export function datetimeLocalToIso(value: string): string {
  return new Date(value).toISOString()
}
