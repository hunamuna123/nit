<script setup lang="ts">
import { ArrowLeft, ArrowRight, Check, CloudOff, ExternalLink, Keyboard, RotateCcw, Sparkles, Undo2, X } from '@lucide/vue'
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
    <header class="bar glass glass--pill">
      <NuxtLink v-if="!embedded" :to="backLink" class="icon-btn" aria-label="Выйти из прохождения">
        <X class="size-5" />
      </NuxtLink>
      <BrandMark v-else size="sm" class="pl-2" />
      <div class="min-w-0 flex-1 px-2">
        <div class="truncate text-[14px] font-semibold">
          {{ p.run.value?.title ?? 'Загрузка…' }}
        </div>
        <div class="mono text-[11.5px] text-[var(--text-4)]">
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
    <div class="px-4 mt-3">
      <HairlineBar :value="p.progress.value" />
    </div>

    <div v-if="p.loadError.value" class="glass glass--lg mx-auto mt-16 max-w-lg p-8 text-center">
      <p class="text-lg font-semibold">
        {{ p.loadError.value }}
      </p>
      <button class="btn-chrome mt-5" @click="p.load()">
        Повторить
      </button>
    </div>

    <div v-else-if="!p.run.value" class="mx-auto max-w-3xl px-4 mt-10 space-y-4">
      <div class="skel h-10 w-2/3" /><div class="skel h-64" />
    </div>

    <section v-else-if="p.finished.value" class="finish mx-auto max-w-2xl px-4 text-center">
      <img src="/glass/infinity.webp" alt="" class="finish__blob">
      <SectionLabel code>
        готово
      </SectionLabel>
      <h1 class="mt-4 display silver halo text-[44px] md:text-[68px] leading-[1]">
        Нить пройдена
      </h1>
      <p class="mt-4 text-[17px] text-[var(--text-2)]">
        Все {{ pl(total, 'шаг', 'шага', 'шагов') }} отмечены. Помогите автору и следующим ученикам — оцените инструкцию.
      </p>
      <div class="glass glass--lg mt-8 p-6 text-left">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <span class="font-semibold">Насколько помогло?</span>
          <RatingStars :value="rating" interactive :size="28" @select="rate" />
        </div>
        <textarea v-if="rating && rating < 5 && !embedded" v-model="review" class="field mt-4 !min-h-[80px] !text-[14.5px]" placeholder="Что стоит улучшить? Автор увидит ваш отзыв" @blur="review && rate(rating)" />
        <p v-if="rated" class="mt-3 text-sm text-[var(--ok)]">
          Спасибо! Оценка учтена в индексе полезности.
        </p>
      </div>
      <div class="mt-8 flex flex-wrap justify-center gap-3">
        <NuxtLink v-if="!embedded" :to="backLink" class="btn-chrome">
          К инструкции <ArrowRight class="size-4" />
        </NuxtLink>
        <NuxtLink v-if="!embedded" to="/guides" class="btn-glass">
          Найти следующую задачу
        </NuxtLink>
        <button class="btn-glass" @click="p.restart()">
          <RotateCcw class="size-4" /> Пройти ещё раз
        </button>
      </div>
    </section>

    <div v-else-if="step" class="layout">
      <aside class="rail">
        <div class="label mb-3 px-3">
          маршрут
        </div>
        <button
          v-for="(s, i) in p.steps.value"
          :key="s.key"
          class="rail__item"
          :class="{ 'rail__item--on': i === p.current.value, 'rail__item--done': isDone(s.key) }"
          @click="p.goTo(i)"
        >
          <span class="rail__dot">
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
          <article :key="step.key" class="card glass glass--lg">
            <div class="flex flex-wrap items-center gap-2">
              <span class="label label--caps"><span class="pearl" />шаг {{ String(p.current.value + 1).padStart(2, '0') }}</span>
              <span class="tag">≈ {{ formatMinutes(step.minutes) }}</span>
              <span v-if="stepDone" class="tag tag--ok"><Check class="size-3.5" />выполнен</span>
              <span v-if="p.run.value.outdated" class="tag tag--warn">есть новая версия</span>
            </div>
            <h1 class="mt-4 text-[28px] md:text-[40px] font-extrabold leading-[1.08] tracking-[-0.03em] silver" style="--lh: 1.08em">
              {{ step.title }}
            </h1>
            <MarkdownView :source="step.body" class="mt-5" />

            <div v-if="step.checklist.length" class="mt-7">
              <div class="label mb-3">
                чек-лист · отметьте, чтобы продолжить
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

            <div class="mt-8 flex flex-wrap items-center gap-3">
              <button class="btn-glass" :disabled="p.current.value === 0" @click="p.goTo(p.current.value - 1)">
                <ArrowLeft class="size-4" /> Назад
              </button>
              <div class="flex-1" />
              <button v-if="stepDone" class="btn-glass btn-glass--sm" @click="p.reopen()">
                <Undo2 class="size-4" /> Снять отметку
              </button>
              <button class="btn-chrome" :disabled="!p.stepReady.value" @click="p.complete()">
                <template v-if="stepDone && p.current.value < total - 1">
                  Дальше <ArrowRight class="size-4" />
                </template>
                <template v-else-if="p.current.value === total - 1 || p.state.done.length === total - 1">
                  <Sparkles class="size-4" /> Завершить
                </template>
                <template v-else>
                  Готово — дальше <ArrowRight class="size-4" />
                </template>
              </button>
            </div>
            <p v-if="!p.stepReady.value" class="mt-3 text-right text-[12.5px] text-[var(--text-4)]">
              Осталось отметить {{ pl(remaining, 'пункт', 'пункта', 'пунктов') }}
            </p>
          </article>
        </Transition>

        <div class="mt-4 glass p-4">
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
            class="dot"
            :class="{ 'dot--on': i === p.current.value, 'dot--done': isDone(s.key) }"
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
  padding: 14px 0 60px;
}

.bar {
  display: flex;
  align-items: center;
  gap: 6px;
  max-width: 1180px;
  height: 60px;
  margin: 0 12px;
  padding: 0 12px 0 8px;
}

@media (min-width: 1204px) {
  .bar { margin: 0 auto; }
}

.player .px-4.mt-3 {
  max-width: 1180px;
  margin-left: auto;
  margin-right: auto;
}

.icon-btn {
  display: inline-grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  color: var(--text-2);
  transition: background .2s;
}

.icon-btn:hover {
  background: var(--wash);
}

.layout {
  display: grid;
  gap: 24px;
  max-width: 1180px;
  margin: 28px auto 0;
  padding: 0 16px;
}

@media (min-width: 1024px) {
  .layout { grid-template-columns: 270px 1fr; }
}

.rail {
  display: none;
}

@media (min-width: 1024px) {
  .rail {
    display: block;
    position: sticky;
    top: 24px;
    align-self: start;
  }
}

.rail__item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 9px 12px;
  border-radius: 16px;
  color: var(--text-3);
  transition: background .2s, color .2s;
}

.rail__item:hover {
  background: var(--wash);
  color: var(--foreground);
}

.rail__item--on {
  color: var(--foreground);
  background: var(--wash-2);
  box-shadow: inset 0 0 0 1px var(--line);
}

.rail__dot {
  flex: none;
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  font-family: var(--font-mono);
  font-size: 11.5px;
  box-shadow: inset 0 0 0 1px var(--line-2);
}

.rail__item--on .rail__dot {
  background: var(--pearl);
  box-shadow: var(--pearl-glow);
  color: #0b0c0e;
}

.rail__item--done .rail__dot {
  color: var(--on-chrome);
  background: var(--chrome);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .8);
}

.card {
  padding: 28px 22px;
}

@media (min-width: 768px) {
  .card { padding: 40px 44px; }
}

.check {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  min-height: 58px;
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 15.5px;
  background: var(--wash);
  box-shadow: inset 0 0 0 1px var(--line);
  transition: background .25s var(--ease), box-shadow .25s var(--ease), transform .16s var(--ease);
}

.check:hover {
  background: var(--wash-2);
}

.check:active {
  transform: scale(.985);
}

.check__box {
  flex: none;
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border-radius: 9px;
  color: transparent;
  box-shadow: inset 0 0 0 1.5px var(--line-2);
  transition: all .3s var(--spring);
}

.check--on {
  background: var(--ok-wash);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--ok) 35%, transparent);
}

.check--on .check__box {
  color: var(--on-chrome);
  background: var(--chrome);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .9), 0 0 14px rgba(200, 230, 215, .35);
  transform: scale(1.06);
}

.check--on > span:nth-child(2) {
  color: var(--text-2);
}

.dots {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-top: 20px;
}

@media (min-width: 1024px) {
  .dots { display: none; }
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--line-2);
  transition: all .3s var(--ease);
}

.dot--done {
  background: var(--text-3);
}

.dot--on {
  width: 28px;
  border-radius: 6px;
  background: var(--pearl);
  box-shadow: var(--pearl-glow);
}

.finish {
  position: relative;
  padding-top: 70px;
}

.finish__blob {
  width: min(360px, 80vw);
  margin: 0 auto -40px;
  animation: float 6s ease-in-out infinite alternate;
  filter: drop-shadow(0 30px 50px rgba(0, 0, 0, .45));
}

@keyframes float {
  to { transform: translateY(-14px) rotate(6deg); }
}

.step-enter-active,
.step-leave-active {
  transition: opacity .28s var(--ease), transform .28s var(--ease);
}

.step-enter-from {
  opacity: 0;
  transform: translateX(24px);
}

.step-leave-to {
  opacity: 0;
  transform: translateX(-24px);
}

.player--embed {
  padding-top: 10px;
}

.player--embed .bar {
  margin: 0 10px;
}
</style>
