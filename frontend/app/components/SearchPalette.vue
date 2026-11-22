<script setup lang="ts">
import { ArrowRight, CornerDownLeft, Search } from '@lucide/vue'
import type { GuideList } from '~/types/api'

const open = defineModel<boolean>('open', { default: false })
const q = ref('')
const result = ref<GuideList | null>(null)
const loading = ref(false)
const active = ref(0)
const router = useRouter()

const examples = ['не включается комп после сборки', 'справка для военкомата', 'докер', 'налоговый вычет за учёбу']
const MODES: Record<string, string> = { fts: 'морфология', fuzzy: 'опечатки', semantic: 'по смыслу' }

let timer: ReturnType<typeof setTimeout> | undefined
let seq = 0
watch(q, (value) => {
  clearTimeout(timer)
  active.value = 0
  if (!value.trim()) {
    result.value = null
    return
  }
  loading.value = true
  timer = setTimeout(async () => {
    const my = ++seq
    try {
      const r = await api<GuideList>('/api/guides', { query: { q: value, limit: 6 }, silent: true })
      if (my === seq) result.value = r
    }
    finally {
      if (my === seq) loading.value = false
    }
  }, 220)
})

watch(open, (v) => {
  if (!v) {
    q.value = ''
    result.value = null
  }
})

function go(slug?: string) {
  open.value = false
  if (slug) router.push(`/guides/${slug}`)
  else router.push({ path: '/guides', query: { q: q.value } })
}

function onKey(e: KeyboardEvent) {
  const n = result.value?.items.length ?? 0
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    active.value = Math.min(n, active.value + 1)
  }
  else if (e.key === 'ArrowUp') {
    e.preventDefault()
    active.value = Math.max(0, active.value - 1)
  }
  else if (e.key === 'Enter') {
    e.preventDefault()
    const item = result.value?.items[active.value]
    go(item?.slug)
  }
}

onMounted(() => {
  const handler = (e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault()
      open.value = !open.value
    }
  }
  window.addEventListener('keydown', handler)
  onBeforeUnmount(() => window.removeEventListener('keydown', handler))
})
</script>

<template>
  <Dialog v-model:open="open">
    <DialogContent class="sm:max-w-2xl p-0 gap-0 overflow-hidden" :show-close-button="false">
      <DialogTitle class="sr-only">
        Поиск инструкций
      </DialogTitle>
      <DialogDescription class="sr-only">
        Ищет по смыслу, с учётом опечаток и форм слов
      </DialogDescription>
      <div class="flex items-center gap-3 px-4 h-14 border-b border-[var(--line)]">
        <Search class="size-5 text-[var(--text-3)]" />
        <input
          v-model="q"
          autofocus
          class="flex-1 bg-transparent outline-none text-[16px] placeholder:text-[var(--text-4)]"
          placeholder="Что нужно сделать? Например: «собрать компьютер»"
          @keydown="onKey"
        >
        <span v-if="loading" class="size-4 rounded-full border-2 border-[var(--line-2)] border-t-[var(--foreground)] animate-spin" />
        <span class="kbd">esc</span>
      </div>

      <div class="max-h-[60vh] overflow-y-auto p-2">
        <div v-if="!q" class="p-4">
          <div class="label mb-3">
            Можно спросить своими словами
          </div>
          <div class="flex flex-wrap gap-2">
            <button v-for="ex in examples" :key="ex" class="chip" @click="q = ex">
              {{ ex }}
            </button>
          </div>
        </div>

        <template v-else-if="result">
          <div v-if="result.search_modes.length" class="flex items-center gap-2 px-3 pt-2 pb-3">
            <span class="label">Нашлось:</span>
            <span v-for="m in result.search_modes" :key="m" class="tag tag--info">{{ MODES[m] ?? m }}</span>
          </div>
          <button
            v-for="(g, i) in result.items"
            :key="g.id"
            class="result"
            :class="active === i && 'result--on'"
            @mouseenter="active = i"
            @click="go(g.slug)"
          >
            <GuideCover :cover="g.cover" :category="g.category" :size="36" />
            <span class="min-w-0 flex-1 text-left">
              <span class="block font-semibold truncate">{{ g.title }}</span>
              <span class="block text-[13px] text-[var(--text-3)] truncate">
                <template v-if="g.snippet">
                  <template v-for="(part, j) in snippetParts(g.snippet)" :key="j">
                    <mark v-if="part.hit" class="bg-transparent text-[var(--foreground)] font-semibold">{{ part.text }}</mark><span v-else>{{ part.text }}</span>
                  </template>
                </template>
                <template v-else>{{ g.steps_count }} {{ plural(g.steps_count, 'шаг', 'шага', 'шагов') }} · {{ formatMinutes(g.est_minutes) }} · {{ g.author.name }}</template>
              </span>
            </span>
            <CornerDownLeft v-if="active === i" class="size-4 text-[var(--text-3)]" />
          </button>
          <p v-if="!result.items.length" class="p-6 text-center text-[var(--text-3)]">
            Ничего не нашлось. Может, это повод <NuxtLink to="/studio/new" class="underline" @click="open = false">написать инструкцию</NuxtLink>?
          </p>
          <button
            v-else
            class="result"
            :class="active === result.items.length && 'result--on'"
            @mouseenter="active = result.items.length"
            @click="go()"
          >
            <span class="icon-box"><ArrowRight class="size-4" /></span>
            <span class="flex-1 text-left font-medium">Все результаты ({{ result.total }})</span>
          </button>
        </template>
      </div>
    </DialogContent>
  </Dialog>
</template>

<style scoped>
.result {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 8px 10px;
  border-radius: 8px;
  transition: background .15s;
}

.result--on {
  background: var(--wash-2);
}
</style>
