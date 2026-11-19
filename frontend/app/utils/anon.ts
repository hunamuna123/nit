// гостевой id в заголовке а не в куках, иначе в iframe не заведется
const KEY = 'nit:anon'

export function getAnonId(): string | null {
  if (import.meta.server) return null
  try {
    let id = localStorage.getItem(KEY)
    if (!id) {
      id = crypto.randomUUID()
      localStorage.setItem(KEY, id)
    }
    return id
  }
  catch {
    return null
  }
}
