<script setup lang="ts">
import { BadgeCheck, Plus, Search, Sparkles, X } from '@lucide/vue'
import type { GuideCard, GuideList } from '~/types/api'

useHead({ title: 'Каталог инструкций' })

const route = useRoute()
const router = useRouter()
const { data: categories } = useCategories()

const SORTS = [
  { v: 'useful', l: 'Полезные' },
  { v: 'popular', l: 'Популярные' },
  { v: 'new', l: 'Новые' },
  { v: 'quick', l: 'Быстрые' },
  { v: 'rating', l: 'Рейтинг' },
]
const TIMES = [
  { v: 'any', l: 'Любое время' },
  { v: '30', l: 'до 30 минут' },
  { v: '60', l: 'до часа' },
  { v: '120', l: 'до 2 часов' },
]
const MODES: Record<string, string> = { fts: 'по словам', fuzzy: 'с опечатками', semantic: 'по смыслу' }
const PAGE = 12

const str = (v: unknown) => (typeof v === 'string' ? v : '')
const q = ref(str(route.query.q))
const filters = computed(() => ({
  q: str(route.query.q) || undefined,
  category: str(route.query.category) || undefined,
  difficulty: str(route.query.difficulty) || undefined,
  verified: route.query.verified === '1' ? true : undefined,
  max_minutes: str(route.query.max_minutes) || undefined,
  sort: str(route.query.sort) || 'useful',
}))

function setQuery(patch: Record<string, string | undefined>) {
  const next = Object.fromEntries(Object.entries({ ...route.query, ...patch }).filter(([, v]) => v))
  router.replace({ query: next })
}

let timer: ReturnType<typeof setTimeout> | undefined
watch(q, (v) => {
  clearTimeout(timer)
  timer = setTimeout(() => setQuery({ q: v.trim() || undefined }), 300)
})
watch(() => route.query.q, v => (q.value = str(v)))

const { data, status } = useFetch<GuideList>('/api/guides', {
  key: 'catalog',
  query: computed(() => ({ ...filters.value, limit: PAGE })),
})

const extra = ref<GuideCard[]>([])
const loadingMore = ref(false)
watch(filters, () => (extra.value = []))
const items = computed(() => [...(data.value?.items ?? []), ...extra.value])
async function more() {
  loadingMore.value = true
  try {
    const r = await api<GuideList>('/api/guides', { query: { ...filters.value, limit: PAGE, offset: items.value.length } })
    extra.value.push(...r.items)
  }
  finally {
    loadingMore.value = false
  }
}

const activeCategory = computed(() => categories.value?.find(c => c.slug === filters.value.category))
</script>

<template>
  <div class="mx-auto max-w-[1200px] px-5 pt-10">
    <div class="flex flex-wrap items-end justify-between gap-6">
      <div>
        <h1 class="page-title">
          {{ activeCategory?.title ?? 'Все инструкции' }}
        </h1>
        <p class="mt-2 text-[var(--text-3)] max-w-[560px]">
          {{ activeCategory?.description ?? 'Пошаговые инструкции для задач, которые делаете впервые.' }}
        </p>
      </div>
      <NuxtLink to="/studio/new" class="btn-secondary btn-sm">
        <Plus class="size-4" /> Написать свою
      </NuxtLink>
    </div>

    <div class="mt-6 relative">
      <Search class="absolute left-3.5 top-1/2 -translate-y-1/2 size-[18px] text-[var(--text-4)] z-[3] pointer-events-none" />
      <input v-model="q" type="search" class="field !h-11 !pl-10 !pr-10" placeholder="Опишите задачу своими словами">
      <button v-if="q" class="absolute right-3 top-1/2 -translate-y-1/2 z-[3] text-[var(--text-3)] hover:text-foreground" aria-label="Очистить" @click="q = ''">
        <X class="size-[18px]" />
      </button>
    </div>
    <div v-if="filters.q && data" class="mt-3 flex flex-wrap items-center gap-2 text-sm text-[var(--text-3)]">
      Найдено {{ pl(data.total, 'инструкция', 'инструкции', 'инструкций') }}
      <span v-for="m in data.search_modes" :key="m" class="tag tag--info">{{ MODES[m] ?? m }}</span>
    </div>

    <div class="mt-4 -mx-5 px-5 flex gap-2 overflow-x-auto pb-1 [scrollbar-width:none]">
      <button class="chip" :class="!filters.category && 'chip--on'" @click="setQuery({ category: undefined })">
        Все
      </button>
      <button
        v-for="c in categories"
        :key="c.slug"
        class="chip"
        :class="filters.category === c.slug && 'chip--on'"
        @click="setQuery({ category: filters.category === c.slug ? undefined : c.slug })"
      >
        <CategoryIcon :slug="c.slug" class="size-4" />{{ c.title }}
        <span class="tabular-nums text-[11px] opacity-60">{{ c.count }}</span>
      </button>
    </div>

    <div class="mt-4 flex flex-wrap items-center gap-3">
      <div class="seg">
        <button
          v-for="(d, i) in ['Любая', 'Легко', 'Средне', 'Сложно']"
          :key="d"
          class="seg__btn"
          :class="(filters.difficulty ?? '0') === String(i) || (!filters.difficulty && i === 0) ? 'seg__btn--on' : ''"
          @click="setQuery({ difficulty: i ? String(i) : undefined })"
        >
          {{ d }}
        </button>
      </div>

      <Select :model-value="filters.max_minutes ?? 'any'" @update:model-value="v => setQuery({ max_minutes: v === 'any' ? undefined : String(v) })">
        <SelectTrigger class="h-8 min-w-[140px]">
          <SelectValue placeholder="Любое время" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem v-for="t in TIMES" :key="t.v" :value="t.v">
            {{ t.l }}
          </SelectItem>
        </SelectContent>
      </Select>

      <label class="flex items-center gap-2 h-8 px-3 rounded-lg border border-[var(--line)] cursor-pointer text-[13.5px]">
        <Switch :model-value="filters.verified === true" @update:model-value="v => setQuery({ verified: v ? '1' : undefined })" />
        <BadgeCheck class="size-4 text-[var(--ok)]" /> Проверено экспертом
      </label>

      <div class="flex-1" />

      <div class="flex items-center gap-1 text-sm">
        <span class="label mr-1">Сортировка:</span>
        <button
          v-for="s in SORTS"
          :key="s.v"
          class="h-8 px-2.5 rounded-md transition-colors"
          :class="filters.sort === s.v ? 'bg-[var(--wash-2)] text-foreground' : 'text-[var(--text-3)] hover:text-foreground'"
          :disabled="!!filters.q"
          :title="filters.q ? 'При поиске результаты упорядочены по релевантности' : ''"
          @click="setQuery({ sort: s.v === 'useful' ? undefined : s.v })"
        >
          {{ s.l }}
        </button>
      </div>
    </div>

    <div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <template v-if="status === 'pending' && !items.length">
        <div v-for="i in 6" :key="i" class="skel h-[236px]" />
      </template>
      <GuideCard v-for="(g, i) in items" :key="g.id" :guide="g" :index="i % PAGE" />
    </div>

    <div v-if="status !== 'pending' && !items.length" class="panel mt-4 p-10 text-center">
      <h3 class="text-lg font-semibold">
        Такой инструкции пока нет
      </h3>
      <p class="mt-2 text-[var(--text-3)]">
        Опишите задачу, и ИИ соберёт черновик шагов. Останется проверить и опубликовать.
      </p>
      <NuxtLink :to="{ path: '/studio/new', query: filters.q ? { topic: filters.q } : {} }" class="btn-primary mt-6">
        <Sparkles class="size-4" /> Создать{{ filters.q ? ` «${filters.q}»` : '' }} с ИИ
      </NuxtLink>
    </div>

    <div v-if="data && items.length < data.total" class="mt-8 flex justify-center">
      <button class="btn-secondary" :disabled="loadingMore" @click="more">
        {{ loadingMore ? 'Загружаем…' : `Показать ещё (${data.total - items.length})` }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.seg {
  display: inline-flex;
  padding: 2px;
  gap: 2px;
  border-radius: 8px;
  background: var(--wash);
}

.seg__btn {
  height: 28px;
  padding: 0 10px;
  border-radius: 6px;
  font-size: 13.5px;
  color: var(--text-3);
  transition: background .15s, color .15s;
}

.seg__btn--on {
  color: var(--foreground);
  background: var(--card);
  box-shadow: var(--shadow-sm);
}
</style>
