import type { HelpOut, RunOut, RunState } from '~/types/api'

// события копятся в localStorage и уходят пачками, время на шаге тикает только пока вкладка видна

interface QueuedEvent {
  client_id: string
  type: 'view' | 'complete' | 'stuck' | 'reopen'
  step_key: string
  duration_ms?: number | null
  at: string
}

interface Stored {
  run: RunOut
  queue: QueuedEvent[]
  savedAt: string
}

const storeKey = (slug: string) => `nit:run:${slug}`

function readStored(slug: string): Stored | null {
  try {
    const raw = localStorage.getItem(storeKey(slug))
    return raw ? (JSON.parse(raw) as Stored) : null
  }
  catch {
    return null
  }
}

function writeStored(slug: string, data: Stored) {
  try {
    localStorage.setItem(storeKey(slug), JSON.stringify(data))
  }
  catch { /* место кончилось, пофиг */ }
}

export function hasOfflineRun(slug: string): boolean {
  if (import.meta.server) return false
  return !!readStored(slug)
}

export async function prepareOffline(slug: string): Promise<void> {
  const run = await api<RunOut>(`/api/guides/${slug}/runs`, { method: 'POST' })
  const prev = readStored(slug)
  writeStored(slug, { run, queue: prev?.run.id === run.id ? prev.queue : [], savedAt: new Date().toISOString() })
}

export function useRunPlayer(slug: string) {
  const run = ref<RunOut | null>(null)
  const current = ref(0)
  const state = reactive<RunState>({ checked: {}, done: [] })
  const queue = ref<QueuedEvent[]>([])
  const online = ref(true)
  const syncing = ref(false)
  const loadError = ref<string | null>(null)
  const finished = ref(false)

  const steps = computed(() => run.value?.steps ?? [])
  const step = computed(() => steps.value[current.value] ?? null)
  const progress = computed(() => (steps.value.length ? state.done.length / steps.value.length : 0))
  const checkedFor = (key: string) => state.checked[key] ?? []
  const stepReady = computed(() => {
    const s = step.value
    if (!s) return false
    return s.checklist.every(i => checkedFor(s.key).includes(i.key))
  })

  let visibleMs = 0
  let since = 0
  function startTimer() {
    visibleMs = 0
    since = document.visibilityState === 'visible' ? performance.now() : 0
  }
  function elapsed() {
    return Math.round(visibleMs + (since ? performance.now() - since : 0))
  }
  function onVisibility() {
    if (document.visibilityState === 'hidden') {
      if (since) visibleMs += performance.now() - since
      since = 0
      flush(true)
    }
    else {
      since = performance.now()
    }
  }

  function persist() {
    if (!run.value) return
    run.value.state = { checked: { ...state.checked }, done: [...state.done] }
    run.value.current_step = current.value
    writeStored(slug, { run: run.value, queue: queue.value, savedAt: new Date().toISOString() })
  }

  function push(type: QueuedEvent['type'], key: string, duration?: number) {
    queue.value.push({ client_id: crypto.randomUUID(), type, step_key: key, duration_ms: duration ?? null, at: new Date().toISOString() })
    persist()
    scheduleFlush()
  }

  let flushTimer: ReturnType<typeof setTimeout> | undefined
  function scheduleFlush() {
    clearTimeout(flushTimer)
    flushTimer = setTimeout(() => flush(), 900)
  }

  async function flush(keepalive = false) {
    if (!run.value || syncing.value) return
    const batch = queue.value.slice(0, 250)
    const body = {
      current_step: current.value,
      state: { checked: state.checked, done: state.done },
      events: batch,
      completed: finished.value,
    }
    if (keepalive) {
      // keepalive чтоб запрос не умер вместе с вкладкой
      try {
        fetch(`/api/runs/${run.value.id}/sync`, {
          method: 'POST',
          keepalive: true,
          headers: { 'content-type': 'application/json', ...anonHeaders() },
          body: JSON.stringify(body),
        })
      }
      catch { /* офлайн */ }
      return
    }
    syncing.value = true
    try {
      await api<RunOut>(`/api/runs/${run.value.id}/sync`, { method: 'POST', body, silent: true })
      const sent = new Set(batch.map(e => e.client_id))
      queue.value = queue.value.filter(e => !sent.has(e.client_id))
      online.value = true
      persist()
      if (queue.value.length) scheduleFlush()
    }
    catch {
      online.value = false
    }
    finally {
      syncing.value = false
    }
  }

  async function load(restart = false) {
    loadError.value = null
    const stored = readStored(slug)
    try {
      const r = await api<RunOut>(`/api/guides/${slug}/runs`, { method: 'POST', query: restart ? { restart: true } : {}, silent: true })
      // офлайн копия свежее - берем ее и досылаем очередь
      if (!restart && stored && stored.run.id === r.id && stored.queue.length) {
        run.value = { ...r, state: stored.run.state, current_step: stored.run.current_step }
        queue.value = stored.queue
      }
      else {
        run.value = r
        queue.value = []
      }
      online.value = true
    }
    catch (e) {
      if (stored && !restart) {
        run.value = stored.run
        queue.value = stored.queue
        online.value = false
      }
      else {
        loadError.value = apiErrorMessage(e, 'Не удалось загрузить инструкцию')
        return
      }
    }
    const r = run.value!
    state.checked = { ...r.state.checked }
    state.done = [...r.state.done]
    finished.value = r.status === 'completed'
    current.value = Math.min(r.current_step, Math.max(0, r.steps.length - 1))
    startTimer()
    if (!finished.value && step.value) push('view', step.value.key)
    if (queue.value.length) flush()
  }

  function toggle(itemKey: string) {
    const s = step.value
    if (!s) return
    const list = new Set(checkedFor(s.key))
    if (list.has(itemKey)) list.delete(itemKey)
    else list.add(itemKey)
    state.checked[s.key] = [...list]
    persist()
    scheduleFlush()
  }

  function goTo(i: number) {
    if (i < 0 || i >= steps.value.length || i === current.value) return
    current.value = i
    startTimer()
    push('view', steps.value[i]!.key)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function complete() {
    const s = step.value
    if (!s || !stepReady.value) return
    if (!state.done.includes(s.key)) {
      state.done.push(s.key)
      push('complete', s.key, elapsed())
    }
    const next = steps.value.findIndex((x, i) => i > current.value && !state.done.includes(x.key))
    if (next >= 0) goTo(next)
    else if (state.done.length >= steps.value.length) finish()
    else goTo(steps.value.findIndex(x => !state.done.includes(x.key)))
  }

  function reopen() {
    const s = step.value
    if (!s) return
    state.done = state.done.filter(k => k !== s.key)
    finished.value = false
    push('reopen', s.key)
  }

  function finish() {
    finished.value = true
    persist()
    flush()
  }

  async function restart() {
    finished.value = false
    await load(true)
  }

  async function help(question: string): Promise<HelpOut | null> {
    const s = step.value
    if (!run.value || !s) return null
    try {
      return await api<HelpOut>(`/api/runs/${run.value.id}/help`, { method: 'POST', body: { step_key: s.key, question } })
    }
    catch {
      push('stuck', s.key)
      return null
    }
  }

  onMounted(() => {
    document.addEventListener('visibilitychange', onVisibility)
    const goOnline = () => {
      online.value = true
      flush()
    }
    const goOffline = () => (online.value = false)
    window.addEventListener('online', goOnline)
    window.addEventListener('offline', goOffline)
    onBeforeUnmount(() => {
      document.removeEventListener('visibilitychange', onVisibility)
      window.removeEventListener('online', goOnline)
      window.removeEventListener('offline', goOffline)
      flush(true)
    })
  })

  return {
    run, steps, step, current, state, progress, stepReady, finished, online, syncing, queue, loadError,
    checkedFor, load, toggle, goTo, complete, reopen, restart, help, flush,
  }
}
