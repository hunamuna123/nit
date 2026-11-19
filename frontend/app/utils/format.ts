export function plural(n: number, one: string, few: string, many: string): string {
  const a = Math.abs(n) % 100
  const b = a % 10
  if (a > 10 && a < 20) return many
  if (b > 1 && b < 5) return few
  if (b === 1) return one
  return many
}

export function pl(n: number, one: string, few: string, many: string): string {
  return `${formatNumber(n)} ${plural(n, one, few, many)}`
}

export function formatNumber(n: number): string {
  return new Intl.NumberFormat('ru-RU').format(n)
}

export function formatMinutes(min: number): string {
  if (min < 60) return `${min} мин`
  const h = Math.floor(min / 60)
  const m = min % 60
  return m ? `${h} ч ${m} мин` : `${h} ч`
}

export function formatSeconds(sec: number | null | undefined): string {
  if (sec == null) return '—'
  if (sec < 60) return `${Math.round(sec)} с`
  return formatMinutes(Math.round(sec / 60))
}

export function percent(x: number | null | undefined, digits = 0): string {
  if (x == null) return '—'
  return `${(x * 100).toFixed(digits)}%`
}

const rtf = new Intl.RelativeTimeFormat('ru', { numeric: 'auto' })

export function timeAgo(iso: string | null | undefined): string {
  if (!iso) return ''
  const diff = (new Date(iso).getTime() - Date.now()) / 1000
  const abs = Math.abs(diff)
  if (abs < 60) return 'только что'
  if (abs < 3600) return rtf.format(Math.round(diff / 60), 'minute')
  if (abs < 86400) return rtf.format(Math.round(diff / 3600), 'hour')
  if (abs < 86400 * 30) return rtf.format(Math.round(diff / 86400), 'day')
  return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' })
}

export const DIFFICULTY = ['', 'Легко', 'Средне', 'Сложно'] as const

export const ROLE_LABEL: Record<string, string> = {
  learner: 'Ученик',
  expert: 'Эксперт',
  admin: 'Админ',
}

export function initials(name: string): string {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map(w => w[0]!.toUpperCase()).join('')
}

export function snippetParts(s: string): { text: string, hit: boolean }[] {
  return s.split(/(\[\[.*?\]\])/g).filter(Boolean).map(part =>
    part.startsWith('[[') ? { text: part.slice(2, -2), hit: true } : { text: part, hit: false },
  )
}
