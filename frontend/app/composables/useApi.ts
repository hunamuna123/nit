import { toast } from 'vue-sonner'

type FetchOpts = Parameters<typeof $fetch>[1]

export function apiErrorMessage(e: unknown, fallback = 'Что-то пошло не так'): string {
  const data = (e as { data?: { detail?: unknown } })?.data
  const detail = data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg)
  const status = (e as { status?: number })?.status
  if (status === 401) return 'Нужно войти в аккаунт'
  if (status === 429) return 'Слишком много запросов, подождите немного'
  if (!status) return 'Нет соединения с сервером'
  return fallback
}

export function api<T>(url: string, opts: FetchOpts & { silent?: boolean } = {}): Promise<T> {
  const { silent, ...rest } = opts
  const headers = new Headers(rest.headers as HeadersInit | undefined)
  const anon = getAnonId()
  if (anon) headers.set('x-nit-anon', anon)
  return ($fetch as (u: string, o: FetchOpts) => Promise<T>)(url, { ...rest, headers }).catch((e: unknown) => {
    if (!silent) toast.error(apiErrorMessage(e))
    throw e
  })
}

export function anonHeaders(): Record<string, string> {
  const anon = getAnonId()
  return anon ? { 'x-nit-anon': anon } : {}
}
