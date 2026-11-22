<script setup lang="ts">
import { ArrowRight, ChartNoAxesColumn, GitFork, ListChecks, Search, Sparkles, WifiOff } from '@lucide/vue'
import type { GuideList, PlatformStats } from '~/types/api'

useHead({ title: 'Пошаговые инструкции с чек-листами' })

const { data: stats } = useFetch<PlatformStats>('/api/meta/stats', { key: 'stats' })
const { data: popular } = useFetch<GuideList>('/api/guides', { key: 'home-popular', query: { sort: 'useful', limit: 6 } })
const { data: categories } = useCategories()

const q = ref('')
const router = useRouter()
function search() {
  router.push({ path: '/guides', query: q.value.trim() ? { q: q.value.trim() } : {} })
}

const tasks = ['собрать пк', 'справка в деканате', 'установить docker', 'налоговый вычет', 'резюме на стажировку']

const features = [
  { icon: Search, title: 'Найдите инструкцию', text: 'Поиск понимает запрос своими словами и прощает опечатки.' },
  { icon: ListChecks, title: 'Пройдите по шагам', text: 'Один шаг на экране, чек-лист и сохранённый прогресс. Работает без интернета.' },
  { icon: ChartNoAxesColumn, title: 'Авторы видят проблемы', text: 'Статистика показывает, на каком шаге бросают, и автор правит именно его.' },
]

const funnel = [
  { t: 'Проверить статус виртуализации', v: 100 },
  { t: 'Узнать модель платы', v: 97 },
  { t: 'Включить виртуализацию в BIOS', v: 58, hot: true },
  { t: 'Установить WSL 2', v: 49 },
  { t: 'Запустить Docker Desktop', v: 45 },
]
</script>

<template>
  <div>
    <section class="hero">
      <div class="mx-auto max-w-[1200px] px-5 py-12 md:py-20 grid gap-12 lg:grid-cols-[1fr_440px] lg:gap-16 items-center">
        <div>
          <h1 class="hero__title">
            Пошаговые инструкции, которые <span class="text-[var(--primary)]">доводят до&nbsp;результата</span>
          </h1>
          <p class="mt-5 max-w-[540px] text-[16px] md:text-[17.5px] leading-relaxed text-[var(--text-3)]">
            От сборки ПК до справки в деканате. Отмечайте шаги по чек-листу, а если застряли — спросите
            у тех, кто уже прошёл.
          </p>

          <form class="hero-search" @submit.prevent="search">
            <Search class="size-[18px] shrink-0 text-[var(--text-4)]" />
            <input v-model="q" class="flex-1 min-w-0 bg-transparent outline-none text-[15px] placeholder:text-[var(--text-4)]" placeholder="Что нужно сделать?">
            <button class="btn-primary btn-sm shrink-0" type="submit">
              Найти
            </button>
          </form>

          <div class="mt-3 flex flex-wrap items-center gap-2">
            <span class="text-[13px] text-[var(--text-4)] mr-1">Например:</span>
            <NuxtLink v-for="t in tasks" :key="t" :to="{ path: '/guides', query: { q: t } }" class="chip !h-7 !text-[13px]">
              {{ t }}
            </NuxtLink>
          </div>

          <dl v-if="stats" class="hero__stats">
            <div>
              <dt>прохождений</dt>
              <dd>{{ formatNumber(stats.runs) }}</dd>
            </div>
            <div>
              <dt>дошли до конца</dt>
              <dd>{{ formatNumber(stats.completions) }}</dd>
            </div>
            <div>
              <dt>инструкций</dt>
              <dd>{{ formatNumber(stats.guides) }}</dd>
            </div>
          </dl>
        </div>

        <HeroPreview />
      </div>
    </section>

    <section class="mx-auto max-w-[1200px] px-5 mt-14">
      <div class="grid gap-8 md:grid-cols-3">
        <div v-for="f in features" :key="f.title" class="flex gap-3.5">
          <span class="icon-box"><component :is="f.icon" class="size-[18px]" /></span>
          <div>
            <h3 class="font-semibold text-[15.5px]">
              {{ f.title }}
            </h3>
            <p class="mt-1 text-[14px] leading-relaxed text-[var(--text-3)]">
              {{ f.text }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <section class="mx-auto max-w-[1200px] px-5 mt-16">
      <div class="flex items-center justify-between gap-4">
        <h2 class="home-h2">
          Популярные инструкции
        </h2>
        <NuxtLink to="/guides" class="text-[14px] font-medium text-[var(--ice)] inline-flex items-center gap-1 hover:underline underline-offset-4">
          Весь каталог <ArrowRight class="size-4" />
        </NuxtLink>
      </div>
      <div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <GuideCard v-for="(g, i) in popular?.items ?? []" :key="g.id" :guide="g" :index="i" />
      </div>
    </section>

    <section class="mx-auto max-w-[1200px] px-5 mt-16">
      <h2 class="home-h2">
        Категории
      </h2>
      <div class="mt-6 grid gap-3 grid-cols-2 md:grid-cols-4">
        <NuxtLink
          v-for="c in categories"
          :key="c.slug"
          :to="{ path: '/guides', query: { category: c.slug } }"
          class="panel panel--hover p-4 flex items-center gap-3"
        >
          <span class="icon-box"><CategoryIcon :slug="c.slug" class="size-[18px]" /></span>
          <div class="min-w-0">
            <div class="font-semibold text-[15px] truncate">
              {{ c.title }}
            </div>
            <div class="text-[13px] text-[var(--text-4)] tabular-nums">
              {{ pl(c.count, 'инструкция', 'инструкции', 'инструкций') }}
            </div>
          </div>
        </NuxtLink>
        <NuxtLink to="/studio/new" class="panel panel--hover p-4 flex items-center gap-3 border-dashed">
          <span class="icon-box"><Sparkles class="size-[18px]" /></span>
          <div class="min-w-0">
            <div class="font-semibold text-[15px]">
              Нет нужной?
            </div>
            <div class="text-[13px] text-[var(--text-4)]">
              Напишите свою
            </div>
          </div>
        </NuxtLink>
      </div>
    </section>

    <section class="mx-auto max-w-[1200px] px-5 mt-16">
      <div class="panel p-6 md:p-10 grid gap-10 lg:grid-cols-2 items-center">
        <div>
          <h2 class="home-h2 !text-[26px] md:!text-[32px]">
            Для авторов: видно, где люди застревают
          </h2>
          <p class="mt-3 text-[15px] leading-relaxed text-[var(--text-3)] max-w-[480px]">
            По каждому шагу считаем, сколько людей бросили, сколько времени заняло и как часто нажимали
            «Застрял». Шаги с проблемами подсвечиваются.
          </p>
          <ul class="mt-6 space-y-3 text-[14.5px] text-[var(--text-2)]">
            <li class="flex items-center gap-3">
              <ChartNoAxesColumn class="size-4 text-[var(--text-4)]" />Воронка и сравнение версий
            </li>
            <li class="flex items-center gap-3">
              <Sparkles class="size-4 text-[var(--text-4)]" />ИИ предлагает новую редакцию шага по комментариям
            </li>
            <li class="flex items-center gap-3">
              <GitFork class="size-4 text-[var(--text-4)]" />Правки от читателей, как pull request
            </li>
            <li class="flex items-center gap-3">
              <WifiOff class="size-4 text-[var(--text-4)]" />Прохождения офлайн досылаются позже
            </li>
          </ul>
          <NuxtLink to="/studio" class="btn-primary mt-7">
            Открыть студию
          </NuxtLink>
        </div>

        <div class="rounded-[10px] border border-[var(--line)] bg-[var(--subtle)] p-4 md:p-5" aria-label="Пример воронки по шагам">
          <div class="flex items-center justify-between mb-3">
            <span class="text-[13px] font-medium text-[var(--text-3)]">Установить Docker · доля дошедших</span>
            <span class="tag tag--crit">узкое место</span>
          </div>
          <div v-for="(f, i) in funnel" :key="f.t" class="funnel__row" :class="f.hot && 'funnel__row--hot'">
            <span class="tabular-nums text-[12px] text-[var(--text-4)] w-4">{{ i + 1 }}</span>
            <div class="flex-1 min-w-0">
              <div class="flex justify-between gap-3 text-[13.5px]">
                <span class="truncate">{{ f.t }}</span>
                <span class="tabular-nums text-[var(--text-3)]">{{ f.v }}%</span>
              </div>
              <div class="funnel__bar">
                <span :style="{ width: `${f.v}%` }" />
              </div>
              <p v-if="f.hot" class="mt-1.5 text-[12.5px] text-[var(--crit)]">
                Бросают 40% · в 2,8 раза дольше плана · «Застрял» 31 раз
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero {
  border-bottom: 1px solid var(--line);
  background: var(--subtle);
}

.hero__title {
  max-width: 640px;
  font-size: 38px;
  font-weight: 700;
  line-height: 1.04;
  letter-spacing: -.04em;
}

@media (min-width: 768px) {
  .hero__title { font-size: 58px; }
}

.hero__stats {
  display: flex;
  gap: 36px;
  margin-top: 36px;
}

.hero__stats > div {
  display: flex;
  flex-direction: column-reverse;
  gap: 2px;
}

.hero__stats dd {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -.03em;
  font-variant-numeric: tabular-nums;
}

.hero__stats dt {
  font-size: 13px;
  color: var(--text-4);
}

.home-h2 {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -.03em;
}

.hero-search {
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: 560px;
  margin-top: 28px;
  height: 48px;
  padding: 0 6px 0 14px;
  border-radius: 10px;
  background: var(--card);
  border: 1px solid var(--input);
  box-shadow: var(--shadow-sm);
  transition: border-color .15s, box-shadow .15s;
}

.hero-search:focus-within {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ring) 18%, transparent);
}

.funnel__row {
  display: flex;
  gap: 10px;
  padding: 9px 8px;
  border-radius: 8px;
}

.funnel__row--hot {
  background: var(--crit-wash);
}

.funnel__bar {
  height: 5px;
  margin-top: 6px;
  border-radius: 5px;
  background: var(--wash-2);
  overflow: hidden;
}

.funnel__bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--primary);
}

.funnel__row--hot .funnel__bar span {
  background: var(--crit);
}
</style>
