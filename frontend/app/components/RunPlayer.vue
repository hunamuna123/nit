<script setup lang="ts">
import { ArrowLeft, ArrowRight, Check, CloudOff, ExternalLink, Keyboard, RotateCcw, Undo2, X } from '@lucide/vue'
import { toast } from 'vue-sonner'
import type { GuideDetail, RatingOut } from '~/types/api'

const props = withDefaults(defineProps<{ slug: string, embedded?: boolean }>(), { embedded: false })
const p = useRunPlayer(props.slug)
const detail = ref<GuideDetail | null>(null)
const tools = ref<{ openStuck: () => void } | null>(null)

onMounted(async () => {
  await p.load()
  try {
    detail.value = await api<GuideDetail>(`/api/guides/${props.slug}`, { silent: true })
  }
  catch { /* офлайн, ну и ладно */ }
})

const step = computed(() => p.step.value)
const total = computed(() => p.steps.value.length)
const isDone = (key: string) => p.state.done.includes(key)
const checked = (itemKey: string) => (step.value ? p.checkedFor(step.value.key).includes(itemKey) : false)
const stepDone = computed(() => (step.value ? isDone(step.value.key) : false))
const remaining = computed(() => step.value?.checklist.filter(i => !checked(i.key)).length ?? 0)
const leftMinutes = computed(() => p.steps.value.filter(s => !isDone(s.key)).reduce((a, s) => a + s.minutes, 0))

const rating = ref(0)
const review = ref('')
const rated = ref(false)
async function rate(value: number) {
  rating.value = value
  try {
    await api<RatingOut>(`/api/guides/${props.slug}/rating`, { method: 'POST', body: { value, review: review.value } })
    rated.value = true
  }
  catch { /* тост уже был */ }
}
watch(() => p.finished.value, (v) => {
  if (v) toast.success('Инструкция пройдена!')
})

function onKey(e: KeyboardEvent) {
  const t = e.target as HTMLElement
  if (t.closest('input, textarea, [contenteditable], [role="dialog"]')) return
  if (p.finished.value || !step.value) return
  if (e.key === 'Enter' || e.key === 'ArrowRight') {
    e.preventDefault()
    if (p.stepReady.value) p.complete()
  }
  else if (e.key === 'ArrowLeft') {
    p.goTo(p.current.value - 1)
  }
  else if (/^[1-9]$/.test(e.key)) {
    const item = step.value.checklist[Number(e.key) - 1]
    if (item) p.toggle(item.key)
  }
  else if (e.key === '?') {
    tools.value?.openStuck()
  }
}
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))

const backLink = computed(() => `/guides/${props.slug}`)
</script>

<template>
  <div class="player" :class="embedded && 'player--embed'">
    <header class="bar">
      <NuxtLink v-if="!embedded" :to="backLink" class="icon-btn" aria-label="Выйти из прохождения">
        <X class="size-5" />
      </NuxtLink>
      <BrandMark v-else size="sm" class="pl-1" />
      <div class="min-w-0 flex-1 px-2">
        <div class="truncate serif text-[15px] font-semibold">
          {{ p.run.value?.title ?? 'Загрузка…' }}
        </div>
        <div class="tabular-nums text-[11.5px] text-[var(--text-4)]">
          <template v-if="p.run.value">
            {{ p.finished.value ? 'пройдено' : `шаг ${p.current.value + 1} из ${total}` }} · {{ percent(p.progress.value) }}
            <template v-if="!p.finished.value && leftMinutes"> · осталось ≈ {{ formatMinutes(leftMinutes) }}</template>
          </template>
        </div>
      </div>
      <span v-if="!p.online.value" class="tag tag--warn" title="Прогресс сохраняется на устройстве и уйдёт на сервер, когда появится сеть">
        <CloudOff class="size-3.5" /> офлайн · {{ p.queue.value.length }}
      </span>
      <span v-else-if="p.syncing.value" class="tag">синхронизация…</span>
      <a v-if="embedded" :href="backLink" target="_blank" class="icon-btn" aria-label="Открыть на сайте"><ExternalLink class="size-4" /></a>
    </header>
    <div class="progress">
      <HairlineBar
        :value="p.progress.value"
        :parts="p.steps.value.map(s => isDone(s.key))"
        :current="p.finished.value ? -1 : p.current.value"
      />
    </div>

    <div v-if="p.loadError.value" class="panel mx-auto mt-16 max-w-lg p-8 text-center">
      <p class="text-lg font-semibold">
        {{ p.loadError.value }}
      </p>
      <button class="btn-primary mt-5" @click="p.load()">
        Повторить
      </button>
    </div>

    <div v-else-if="!p.run.value" class="mx-auto max-w-3xl px-4 mt-10 space-y-4">
      <div class="skel h-10 w-2/3" /><div class="skel h-64" />
    </div>

    <section v-else-if="p.finished.value" class="finish mx-auto max-w-2xl px-4 text-center">
      <BrandMark :word="false" size="lg" class="finish__knot" />
      <h1 class="mt-5 page-title">
        Нить завязана
      </h1>
      <p class="mt-3 text-[16px] text-[var(--text-3)]">
        Все {{ pl(total, 'шаг', 'шага', 'шагов') }} отмечены. Помогите автору и следующим ученикам — оцените инструкцию.
      </p>
      <div class="panel mt-8 p-6 text-left">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <span class="font-semibold">Насколько помогло?</span>
          <RatingStars :value="rating" interactive :size="28" @select="rate" />
        </div>
        <textarea v-if="rating && rating < 5 && !embedded" v-model="review" class="field mt-4 !min-h-[80px] !text-[14.5px]" placeholder="Что стоит улучшить? Автор увидит ваш отзыв" @blur="review && rate(rating)" />
        <p v-if="rated" class="mt-3 text-sm text-[var(--ok)]">
          Спасибо! Оценка учтена в индексе полезности.
        </p>
      </div>
      <div class="mt-8 flex flex-wrap justify-center gap-2">
        <NuxtLink v-if="!embedded" :to="backLink" class="btn-primary">
          К инструкции <ArrowRight class="size-4" />
        </NuxtLink>
        <NuxtLink v-if="!embedded" to="/guides" class="btn-secondary">
          Найти следующую задачу
        </NuxtLink>
        <button class="btn-secondary" @click="p.restart()">
          <RotateCcw class="size-4" /> Пройти ещё раз
        </button>
      </div>
    </section>

    <div v-else-if="step" class="layout">
      <aside class="rail">
        <div class="label mb-2 px-2.5">
          Шаги
        </div>
        <button
          v-for="(s, i) in p.steps.value"
          :key="s.key"
          class="rail__item"
          :class="{ 'rail__item--on': i === p.current.value, 'rail__item--done': isDone(s.key) }"
          @click="p.goTo(i)"
        >
          <span class="rail__dot num">
            <Check v-if="isDone(s.key)" class="size-3.5" />
            <template v-else>{{ i + 1 }}</template>
          </span>
          <span class="text-left text-[13.5px] leading-snug line-clamp-2">{{ s.title }}</span>
        </button>
        <div class="mt-6 px-3 text-[12px] text-[var(--text-4)] leading-relaxed">
          <Keyboard class="size-3.5 inline mr-1" /><span class="kbd">1</span>–<span class="kbd">9</span> отметить пункт,
          <span class="kbd">Enter</span> дальше, <span class="kbd">←</span> назад, <span class="kbd">?</span> застрял
        </div>
      </aside>

      <main class="min-w-0">
        <Transition name="step" mode="out-in">
          <article :key="step.key" class="card panel">
            <div class="flex flex-wrap items-center gap-2">
              <span class="label">Шаг {{ p.current.value + 1 }} из {{ total }}</span>
              <span class="tag">≈ {{ formatMinutes(step.minutes) }}</span>
              <span v-if="stepDone" class="tag tag--ok"><Check class="size-3.5" />выполнен</span>
              <span v-if="p.run.value.outdated" class="tag tag--warn">есть новая версия</span>
            </div>
            <h1 class="mt-4 page-title">
              {{ step.title }}
            </h1>
            <MarkdownView :source="step.body" class="mt-5" />

            <div v-if="step.checklist.length" class="mt-7">
              <div class="label mb-3">
                Отметьте, чтобы продолжить
              </div>
              <div class="space-y-2">
                <button
                  v-for="(item, i) in step.checklist"
                  :key="item.key"
                  class="check"
                  :class="checked(item.key) && 'check--on'"
                  role="checkbox"
                  :aria-checked="checked(item.key)"
                  @click="p.toggle(item.key)"
                >
                  <span class="check__box"><Check class="size-4" /></span>
                  <span class="flex-1 text-left">{{ item.text }}</span>
                  <span class="kbd hidden md:inline-grid">{{ i + 1 }}</span>
                </button>
              </div>
            </div>

            <div class="mt-8 flex flex-wrap items-center gap-2">
              <button class="btn-secondary" :disabled="p.current.value === 0" @click="p.goTo(p.current.value - 1)">
                <ArrowLeft class="size-4" /> Назад
              </button>
              <div class="flex-1" />
              <button v-if="stepDone" class="btn-secondary btn-sm" @click="p.reopen()">
                <Undo2 class="size-4" /> Снять отметку
              </button>
              <button class="btn-primary" :disabled="!p.stepReady.value" @click="p.complete()">
                <template v-if="stepDone && p.current.value < total - 1">
                  Дальше <ArrowRight class="size-4" />
                </template>
                <template v-else-if="p.current.value === total - 1 || p.state.done.length === total - 1">
                  Завершить
                </template>
                <template v-else>
                  Готово, дальше <ArrowRight class="size-4" />
                </template>
              </button>
            </div>
            <p v-if="!p.stepReady.value" class="mt-3 text-right text-[12.5px] text-[var(--text-4)]">
              Осталось отметить {{ pl(remaining, 'пункт', 'пункта', 'пунктов') }}
            </p>
          </article>
        </Transition>

        <div class="mt-4 panel p-4">
          <RunStepTools
            ref="tools"
            :slug="slug"
            :step="step"
            :help="p.help"
            :embedded="embedded"
            :stats="detail?.step_stats[step.key] ? { up: detail.step_stats[step.key]!.up, down: detail.step_stats[step.key]!.down, my_vote: detail.step_stats[step.key]!.my_vote ?? null } : undefined"
          />
        </div>

        <div class="dots">
          <button
            v-for="(s, i) in p.steps.value"
            :key="s.key"
            class="pager"
            :class="{ 'pager--on': i === p.current.value, 'pager--done': isDone(s.key) }"
            :aria-label="`Шаг ${i + 1}`"
            @click="p.goTo(i)"
          />
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.player {
  min-height: 100dvh;
  padding-bottom: 60px;
}

.bar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 6px;
  height: 56px;
  padding: 0 12px 0 8px;
  background: var(--background);
}

.progress {
  position: sticky;
  top: 56px;
  z-index: 19;
  padding: 6px 12px;
  background: var(--background);
  border-bottom: 1px solid var(--line);
}

.icon-btn {
  display: inline-grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  color: var(--text-3);
  transition: background .15s, color .15s;
}

.icon-btn:hover {
  color: var(--foreground);
  background: var(--wash);
}

.layout {
  display: grid;
  gap: 24px;
  max-width: 1120px;
  margin: 28px auto 0;
  padding: 0 16px;
}

@media (min-width: 1024px) {
  .layout { grid-template-columns: 250px 1fr; }
}

.rail {
  display: none;
}

@media (min-width: 1024px) {
  .rail {
    display: block;
    position: sticky;
    top: 96px;
    align-self: start;
  }
}

.rail__item {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  width: 100%;
  padding: 7px 10px;
  border-radius: 8px;
  color: var(--text-3);
  transition: background .15s, color .15s;
}

.rail__item > span:last-child {
  padding-top: 2px;
}

/* нить между кружками шагов, пройденный кусок красим */
.rail__item:not(:last-of-type)::before {
  content: '';
  position: absolute;
  left: 21px;
  top: 32px;
  bottom: -6px;
  width: 2px;
  background-image: linear-gradient(180deg, var(--line-2) 0 5px, transparent 5px 9px);
  background-size: 2px 9px;
  background-repeat: repeat-y;
}

.rail__item--done:not(:last-of-type)::before {
  background: var(--thread);
  border-radius: 2px;
}

.rail__item:hover {
  background: var(--wash);
  color: var(--foreground);
}

.rail__item--on {
  color: var(--foreground);
  background: var(--card);
  box-shadow: inset 0 0 0 1px var(--line);
}

.rail__dot {
  position: relative;
  z-index: 1;
  flex: none;
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-size: 12.5px;
  font-weight: 600;
  background: var(--background);
  border: 1.5px solid var(--line-2);
}

.rail__item--on .rail__dot {
  color: var(--thread);
  border-color: var(--thread);
  box-shadow: 0 0 0 3px var(--thread-wash);
}

.rail__item--done .rail__dot {
  color: #fff;
  background: var(--thread);
  border-color: var(--thread);
}

.card {
  padding: 24px 20px;
  border-radius: 16px;
}

@media (min-width: 768px) {
  .card { padding: 36px 40px; }
}

.check {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  min-height: 52px;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 15px;
  background: var(--card);
  border: 1px solid var(--line);
  transition: background .15s, border-color .15s;
}

.check:hover {
  border-color: var(--line-2);
}

.check__box {
  flex: none;
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  color: transparent;
  background: var(--card);
  border: 1.5px solid color-mix(in srgb, var(--thread) 45%, var(--line-2));
  transition: background .15s, border-color .15s, color .15s;
}

.check--on {
  background: var(--background);
}

.check--on > span:nth-child(2) {
  text-decoration: line-through;
  text-decoration-color: color-mix(in srgb, var(--thread) 55%, transparent);
}

.check--on .check__box {
  color: var(--primary-foreground);
  background: var(--primary);
  border-color: var(--primary);
}

.check--on > span:nth-child(2) {
  color: var(--text-3);
}

.dots {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
  margin-top: 20px;
}

@media (min-width: 1024px) {
  .dots { display: none; }
}

.pager {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--line-2);
  transition: width .2s, background .2s;
}

.pager--done {
  background: var(--text-4);
}

.pager--on {
  width: 22px;
  border-radius: 4px;
  background: var(--thread);
}

.finish {
  padding-top: 64px;
}

.finish__knot :deep(svg) {
  width: 64px;
  height: 64px;
}

.step-enter-active,
.step-leave-active {
  transition: opacity .18s ease;
}

.step-enter-from,
.step-leave-to {
  opacity: 0;
}
</style>
