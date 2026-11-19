<script setup lang="ts">
import { ArrowRight, ArrowUpRight, ChartNoAxesColumn, GitFork, ListChecks, MessageSquareText, Search, Sparkles, WifiOff } from '@lucide/vue'
import type { GuideList, PlatformStats } from '~/types/api'

useHead({ title: 'Пошаговые инструкции, которые проходят до конца' })

const { data: stats } = useFetch<PlatformStats>('/api/meta/stats', { key: 'stats' })
const { data: popular } = useFetch<GuideList>('/api/guides', { key: 'home-popular', query: { sort: 'useful', limit: 6 } })
const { data: categories } = useCategories()

const q = ref('')
const router = useRouter()
function search() {
  router.push({ path: '/guides', query: q.value.trim() ? { q: q.value.trim() } : {} })
}

const steps = [
  {
    n: '01',
    title: 'Найди',
    icon: Search,
    points: ['Поиск понимает смысл: «не включается комп после сборки»', 'Прощает опечатки и формы слов', 'Рейтинг полезности, а не просто лайки'],
  },
  {
    n: '02',
    title: 'Пройди',
    icon: ListChecks,
    points: ['Один экран — один шаг', 'Чек-лист не даст пропустить важное', 'Прогресс сохраняется, работает офлайн'],
  },
  {
    n: '03',
    title: 'Помоги',
    icon: MessageSquareText,
    points: ['Кнопка «Застрял» — советы и подсказка ИИ', '«Полезно / не полезно» на каждом шаге', 'Предложи правку или сделай форк'],
  },
  {
    n: '04',
    title: 'Улучши',
    icon: ChartNoAxesColumn,
    points: ['Воронка по шагам и индекс узких мест', 'ИИ читает комментарии и предлагает правку', 'Новая версия — сравнение «до / после»'],
  },
]

const funnel = [
  { t: 'Проверить статус виртуализации', v: 100 },
  { t: 'Узнать модель платы', v: 97 },
  { t: 'Включить виртуализацию в BIOS', v: 58, hot: true },
  { t: 'Установить WSL 2', v: 49 },
  { t: 'Запустить Docker Desktop', v: 45 },
]

const tasks = ['собрать пк', 'справка в деканате', 'отчёт по лабораторной', 'установить docker', 'налоговый вычет', 'первый pull request', 'заселение в общагу', 'резюме на стажировку']
</script>

<template>
  <div>
    <section class="relative">
      <div class="absolute inset-0 grid-lines pointer-events-none" />
      <div class="relative mx-auto max-w-[1180px] px-5 pt-16 md:pt-24 pb-14">
        <div class="flex items-center justify-between gap-4 rise">
          <SectionLabel code>
            платформа инструкций
          </SectionLabel>
          <span v-if="stats" class="glass glass--pill hidden sm:inline-flex items-center gap-2.5 h-10 px-4 text-sm">
            <span class="pearl pearl--sm" />
            <span class="mono">{{ formatNumber(stats.runs) }}</span> прохождений ·
            <span class="mono">{{ formatNumber(stats.guides) }}</span> инструкций
          </span>
        </div>

        <h1 class="hero-title display silver halo rise" style="--i: 1">
          Делай впервые&nbsp;—<br>как в сотый раз
        </h1>
        <p class="mt-6 max-w-[620px] text-[17px] md:text-[19px] leading-relaxed text-[var(--text-2)] halo rise" style="--i: 2">
          Интерактивные инструкции с чек-листами — от сборки ПК до справки в деканате.
          Отметил шаг — перешёл дальше. А автор видит, где ученики спотыкаются, и чинит именно это место.
        </p>

        <form class="hero-search glass glass--lg rise" style="--i: 3" @submit.prevent="search">
          <Search class="size-5 shrink-0 text-[var(--text-3)] ml-2" />
          <input v-model="q" class="flex-1 min-w-0 bg-transparent outline-none text-[16px] md:text-[17px] placeholder:text-[var(--text-4)]" placeholder="Что нужно сделать? «оформить академ», «докер на винду»…">
          <button class="btn-chrome shrink-0" type="submit">
            Найти <ArrowRight class="size-4" />
          </button>
        </form>

        <div class="mt-4 flex flex-wrap gap-2 rise" style="--i: 4">
          <NuxtLink v-for="t in tasks.slice(0, 5)" :key="t" :to="{ path: '/guides', query: { q: t } }" class="chip">
            {{ t }}
          </NuxtLink>
        </div>

        <div class="mt-10 flex flex-wrap gap-3 rise" style="--i: 5">
          <NuxtLink to="/guides" class="btn-chrome">
            Открыть каталог <ArrowUpRight class="size-4" />
          </NuxtLink>
          <NuxtLink to="/studio/new" class="btn-glass">
            <Sparkles class="size-4" /> Написать инструкцию с ИИ
          </NuxtLink>
        </div>
      </div>

      <div class="py-5 border-y border-[var(--line)] bg-[var(--wash)]">
        <MarqueeTicker :items="tasks" />
      </div>
    </section>

    <section class="mx-auto max-w-[1180px] px-5 mt-24">
      <SectionLabel num="01">
        как это работает
      </SectionLabel>
      <h2 class="section-title silver halo">
        Нить проходит через всю задачу
      </h2>
      <div class="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <article v-for="(s, i) in steps" :key="s.n" class="glass glass--hover p-6 rise min-h-[300px] flex flex-col" :style="{ '--i': i }">
          <div class="flex items-start justify-between">
            <span class="display text-[44px] leading-none silver">{{ s.n }}</span>
            <span class="ico"><component :is="s.icon" class="size-[18px]" /></span>
          </div>
          <h3 class="mt-4 text-[26px] font-extrabold tracking-tight">
            {{ s.title }}
          </h3>
          <ul class="mt-4 space-y-2.5">
            <li v-for="p in s.points" :key="p" class="flex gap-2.5 text-[14.5px] text-[var(--text-3)] leading-snug">
              <span class="pearl pearl--sm mt-[7px]" />{{ p }}
            </li>
          </ul>
        </article>
      </div>
    </section>

    <section class="mx-auto max-w-[1180px] px-5 mt-24">
      <div class="flex items-end justify-between gap-4">
        <div>
          <SectionLabel num="02">
            самое полезное
          </SectionLabel>
          <h2 class="section-title silver halo">
            Проходят до конца
          </h2>
        </div>
        <NuxtLink to="/guides" class="btn-glass btn-glass--sm hidden sm:inline-flex">
          Весь каталог <ArrowRight class="size-4" />
        </NuxtLink>
      </div>
      <div class="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <GuideCard v-for="(g, i) in popular?.items ?? []" :key="g.id" :guide="g" :index="i" />
      </div>
    </section>

    <section class="mx-auto max-w-[1180px] px-5 mt-24">
      <div class="glass glass--lg overflow-hidden p-6 md:p-12 grid gap-10 lg:grid-cols-[1fr_1.1fr] items-center">
        <div>
          <SectionLabel num="03">
            для авторов
          </SectionLabel>
          <h2 class="section-title silver">
            Видно, где спотыкаются
          </h2>
          <p class="mt-5 text-[16px] leading-relaxed text-[var(--text-2)] max-w-[480px]">
            Каждое прохождение — это сигнал. Нить собирает, где бросают, где сидят дольше заявленного,
            где жмут «Застрял», и считает индекс проблемности каждого шага.
          </p>
          <ul class="mt-6 space-y-3 text-[15px]">
            <li class="flex gap-3">
              <span class="ico size-8"><ChartNoAxesColumn class="size-4" /></span><span class="pt-1">Воронка и сравнение версий «до / после правки»</span>
            </li>
            <li class="flex gap-3">
              <span class="ico size-8"><Sparkles class="size-4" /></span><span class="pt-1">ИИ читает комментарии и пишет новую редакцию шага</span>
            </li>
            <li class="flex gap-3">
              <span class="ico size-8"><GitFork class="size-4" /></span><span class="pt-1">Правки от учеников вливаются, как pull request</span>
            </li>
            <li class="flex gap-3">
              <span class="ico size-8"><WifiOff class="size-4" /></span><span class="pt-1">Ученики проходят офлайн — события дойдут позже</span>
            </li>
          </ul>
          <NuxtLink to="/studio" class="btn-chrome mt-8">
            Открыть студию <ArrowRight class="size-4" />
          </NuxtLink>
        </div>

        <div class="funnel glass p-5 md:p-6" aria-label="Пример воронки по шагам">
          <div class="flex items-center justify-between mb-5">
            <span class="label">воронка · установить docker</span>
            <span class="tag tag--crit">узкое место</span>
          </div>
          <div v-for="(f, i) in funnel" :key="f.t" class="funnel__row" :class="f.hot && 'funnel__row--hot'">
            <span class="mono text-xs text-[var(--text-4)] w-6">{{ String(i + 1).padStart(2, '0') }}</span>
            <div class="flex-1 min-w-0">
              <div class="flex justify-between gap-3 text-[13.5px]">
                <span class="truncate">{{ f.t }}</span>
                <span class="mono text-[var(--text-3)]">{{ f.v }}%</span>
              </div>
              <div class="funnel__bar">
                <span :style="{ width: `${f.v}%` }" />
              </div>
              <p v-if="f.hot" class="mt-2 text-[12.5px] text-[var(--crit)]">
                Бросают 40% дошедших · в 2,8 раза дольше · «Застрял» — 31 раз
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="mx-auto max-w-[1180px] px-5 mt-24">
      <SectionLabel num="04">
        категории
      </SectionLabel>
      <h2 class="section-title silver halo">
        От бюрократии до железа
      </h2>
      <div class="mt-10 grid gap-3 grid-cols-2 md:grid-cols-4">
        <NuxtLink
          v-for="(c, i) in categories"
          :key="c.slug"
          :to="{ path: '/guides', query: { category: c.slug } }"
          class="glass glass--hover p-5 rise flex flex-col gap-4 min-h-[150px]"
          :style="{ '--i': i }"
        >
          <span class="ico"><CategoryIcon :slug="c.slug" class="size-[18px]" /></span>
          <div class="mt-auto">
            <div class="font-bold text-[17px]">
              {{ c.title }}
            </div>
            <div class="text-[13px] text-[var(--text-3)] mono">
              {{ pl(c.count, 'инструкция', 'инструкции', 'инструкций') }}
            </div>
          </div>
        </NuxtLink>
        <NuxtLink to="/studio/new" class="glass glass--hover p-5 flex flex-col gap-4 min-h-[150px] glass--lit">
          <span class="ico"><Sparkles class="size-[18px]" /></span>
          <div class="mt-auto">
            <div class="font-bold text-[17px]">
              Нет нужной?
            </div>
            <div class="text-[13px] text-[var(--text-3)]">
              ИИ набросает черновик за минуту
            </div>
          </div>
        </NuxtLink>
      </div>
    </section>

    <section v-if="stats" class="mx-auto max-w-[1180px] px-5 mt-24">
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div
v-for="(s, i) in [
          { v: stats.guides, l: 'инструкций' },
          { v: stats.steps, l: 'шагов с чек-листами' },
          { v: stats.runs, l: 'прохождений' },
          { v: stats.completions, l: 'дошли до конца' },
        ]" :key="s.l" class="rise" :style="{ '--i': i }"
        >
          <div class="display silver text-[44px] md:text-[64px] leading-none">
            {{ formatNumber(s.v) }}
          </div>
          <div class="mt-2 label">
            <span class="pearl pearl--sm" />{{ s.l }}
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero-title {
  margin-top: 34px;
  font-size: clamp(38px, 6.6vw, 96px);
  line-height: .98;
  --lh: .98em;
}

.hero-search {
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 680px;
  margin-top: 36px;
  padding: 8px 8px 8px 12px;
  border-radius: 999px;
}

.section-title {
  margin-top: 14px;
  font-size: clamp(32px, 4.6vw, 56px);
  font-weight: 800;
  line-height: 1.04;
  letter-spacing: -.035em;
  --lh: 1.04em;
}

.funnel__row {
  display: flex;
  gap: 12px;
  padding: 12px 10px;
  border-radius: 16px;
}

.funnel__row--hot {
  background: var(--crit-wash);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--crit) 35%, transparent);
}

.funnel__bar {
  height: 6px;
  margin-top: 8px;
  border-radius: 6px;
  background: var(--line);
  overflow: hidden;
}

.funnel__bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(255, 255, 255, .25), #fff);
}

:root:not(.dark) .funnel__bar span {
  background: linear-gradient(90deg, rgba(20, 25, 35, .25), #1a1d22);
}

.funnel__row--hot .funnel__bar span {
  background: linear-gradient(90deg, color-mix(in srgb, var(--crit) 30%, transparent), var(--crit));
}
</style>
