<script setup lang="ts">
import { ArrowRight, Search } from '@lucide/vue'
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

const tasks = ['собрать ПК', 'справка в деканате', 'установить Docker', 'налоговый вычет']

const how = [
  { t: 'Найдите задачу', d: 'Пишите как думаете: «не включается комп после сборки» найдёт сборку ПК, опечатки тоже не страшны.' },
  { t: 'Идите по шагам', d: 'Один шаг на экране и чек-лист к нему. Прогресс сохраняется сам, даже без регистрации и без интернета.' },
  { t: 'Застряли — спросите', d: 'Прямо в шаге советы тех, кто уже прошёл, и подсказка GigaChat. Автор видит, где трудно, и правит.' },
]

const funnel = [
  { t: 'Проверить статус виртуализации', v: 100 },
  { t: 'Узнать модель платы', v: 97 },
  { t: 'Включить виртуализацию в BIOS', v: 58, hot: true },
  { t: 'Установить WSL 2', v: 49 },
  { t: 'Запустить Docker Desktop', v: 45 },
]

const forAuthors = [
  'воронка по шагам и сравнение версий «до / после»',
  'GigaChat читает комментарии и предлагает новую редакцию шага',
  'правки от читателей — как pull request',
  'офлайн-прохождения досылаются, когда появится сеть',
]
</script>

<template>
  <div>
    <section class="hero">
      <div class="mx-auto max-w-[1200px] px-5 pt-12 pb-16 md:pt-20 md:pb-24 grid gap-12 lg:grid-cols-[1fr_440px] lg:gap-20 items-center">
        <div>
          <h1 class="hero__title">
            Чтобы <em>с&nbsp;первого раза</em><br class="hidden md:inline"> и&nbsp;ничего не&nbsp;забыть
          </h1>
          <p class="hero__lead">
            Пошаговые инструкции с чек-листами — от сборки компьютера до справки из деканата.
            Отмечаете шаг, идёте дальше, а если застряли, рядом советы тех, кто уже прошёл.
          </p>

          <form class="hero-search" @submit.prevent="search">
            <Search class="size-[18px] shrink-0 text-[var(--text-4)]" />
            <input v-model="q" class="flex-1 min-w-0 bg-transparent outline-none text-[15.5px] placeholder:text-[var(--text-4)]" placeholder="Что нужно сделать?" aria-label="Что нужно сделать">
            <button class="btn-primary btn-sm shrink-0" type="submit">
              Найти
            </button>
          </form>

          <p class="hero__examples">
            <span class="text-[var(--text-4)]">Например:&nbsp;</span>
            <template v-for="(t, i) in tasks" :key="t">
              <NuxtLink :to="{ path: '/guides', query: { q: t } }" class="link">{{ t }}</NuxtLink><span v-if="i < tasks.length - 1" class="text-[var(--text-4)]"> · </span>
            </template>
          </p>

          <p v-if="stats" class="hero__stats tabular-nums">
            {{ pl(stats.runs, 'прохождение', 'прохождения', 'прохождений') }} · {{ formatNumber(stats.completions) }} дошли до конца · {{ pl(stats.guides, 'инструкция', 'инструкции', 'инструкций') }}
          </p>
        </div>

        <HeroPreview />
      </div>
    </section>

    <section class="mx-auto max-w-[1200px] px-5 mt-20">
      <h2 class="home-h2">
        Как это устроено
      </h2>
      <ol class="how">
        <li v-for="(s, i) in how" :key="s.t" class="how__step">
          <span class="how__num num">{{ i + 1 }}</span>
          <div>
            <h3 class="how__title">
              {{ s.t }}
            </h3>
            <p class="how__text">
              {{ s.d }}
            </p>
          </div>
        </li>
      </ol>
    </section>

    <section class="mx-auto max-w-[1200px] px-5 mt-24">
      <div class="flex items-baseline justify-between gap-4">
        <h2 class="home-h2">
          Чаще всего проходят
        </h2>
        <NuxtLink to="/guides" class="link inline-flex items-center gap-1 text-[14.5px] shrink-0">
          Весь каталог <ArrowRight class="size-4" />
        </NuxtLink>
      </div>
      <div class="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <GuideCard v-for="(g, i) in popular?.items ?? []" :key="g.id" :guide="g" :index="i" />
      </div>
    </section>

    <section class="mx-auto max-w-[1200px] px-5 mt-24">
      <h2 class="home-h2">
        Оглавление
      </h2>
      <div class="toc">
        <NuxtLink
          v-for="c in categories"
          :key="c.slug"
          :to="{ path: '/guides', query: { category: c.slug } }"
          class="toc__row"
        >
          <span class="toc__title">{{ c.title }}</span>
          <span class="toc__fill" aria-hidden="true" />
          <span class="toc__count num">{{ c.count }}</span>
        </NuxtLink>
        <NuxtLink to="/studio/new" class="toc__row toc__row--new">
          <span class="toc__title">Нет нужной — напишите свою</span>
          <span class="toc__fill" aria-hidden="true" />
          <ArrowRight class="size-4 shrink-0" />
        </NuxtLink>
      </div>
    </section>

    <section class="mx-auto max-w-[1200px] px-5 mt-24">
      <div class="authors panel">
        <div>
          <h2 class="home-h2">
            Автор видит, где люди застревают
          </h2>
          <p class="mt-4 text-[15.5px] leading-relaxed text-[var(--text-3)] max-w-[470px]">
            По каждому шагу считаем, сколько людей бросили, сколько времени ушло и как часто нажимали «Застрял».
            Самый трудный шаг сразу видно — его и стоит переписать.
          </p>
          <ul class="authors__list">
            <li v-for="f in forAuthors" :key="f">
              {{ f }}
            </li>
          </ul>
          <NuxtLink to="/studio" class="btn-primary mt-8">
            Открыть студию
          </NuxtLink>
        </div>

        <figure class="funnel" aria-label="Пример воронки по шагам">
          <figcaption class="flex items-baseline justify-between gap-3 mb-4">
            <span class="serif text-[16px] font-semibold">Установить Docker</span>
            <span class="text-[12.5px] text-[var(--text-4)]">доля дошедших до шага</span>
          </figcaption>
          <div v-for="(f, i) in funnel" :key="f.t" class="funnel__row" :class="f.hot && 'funnel__row--hot'">
            <span class="funnel__n num">{{ i + 1 }}</span>
            <div class="flex-1 min-w-0">
              <div class="flex justify-between gap-3 text-[14px]">
                <span class="truncate">{{ f.t }}</span>
                <span class="tabular-nums text-[var(--text-3)]">{{ f.v }}%</span>
              </div>
              <div class="funnel__bar">
                <span :style="{ width: `${f.v}%` }" />
              </div>
              <p v-if="f.hot" class="funnel__note">
                Узкое место: бросают 40%, сидят в 2,8 раза дольше плана, «Застрял» — 31 раз
              </p>
            </div>
          </div>
        </figure>
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero {
  border-bottom: 1px solid var(--line);
}

.hero__title {
  font-family: var(--font-serif);
  font-optical-sizing: auto;
  font-size: 38px;
  font-weight: 600;
  line-height: 1.08;
  letter-spacing: -.025em;
}

.hero__title em {
  font-style: italic;
  font-weight: 500;
}

@media (min-width: 768px) {
  .hero__title { font-size: 62px; }
}

.hero__lead {
  margin-top: 22px;
  max-width: 540px;
  font-size: 16.5px;
  line-height: 1.6;
  color: var(--text-3);
}

@media (min-width: 768px) {
  .hero__lead { font-size: 18px; }
}

.hero-search {
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: 540px;
  margin-top: 32px;
  height: 52px;
  padding: 0 7px 0 16px;
  border-radius: 12px;
  background: var(--card);
  border: 1px solid var(--line-2);
  box-shadow: var(--shadow-md);
  transition: border-color .15s, box-shadow .15s;
}

.hero-search:focus-within {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ring) 16%, transparent), var(--shadow-md);
}

.hero-search .btn-sm {
  height: 38px;
}

.hero__examples {
  margin-top: 14px;
  font-size: 14px;
  line-height: 1.9;
  color: var(--text-2);
}

.hero__examples .link {
  text-decoration-color: var(--line-2);
}

.hero__examples .link:hover {
  text-decoration-color: var(--thread);
}

.hero__stats {
  margin-top: 28px;
  font-size: 13.5px;
  color: var(--text-4);
}

.home-h2 {
  font-family: var(--font-serif);
  font-optical-sizing: auto;
  font-size: 28px;
  font-weight: 600;
  line-height: 1.15;
  letter-spacing: -.02em;
}

@media (min-width: 768px) {
  .home-h2 { font-size: 34px; }
}

.how {
  position: relative;
  display: grid;
  gap: 28px;
  margin-top: 36px;
}

/* на мобилке нить идет от кружка к кружку, не дальше последнего */
.how__step:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 19px;
  top: 40px;
  bottom: -28px;
  width: 2px;
  background: var(--thread);
}

@media (min-width: 768px) {
  .how__step:not(:last-child)::before {
    content: none;
  }

  .how {
    grid-template-columns: repeat(3, 1fr);
    gap: 40px;
  }

  .how::before {
    content: '';
    position: absolute;
    left: 20px;
    right: 0;
    top: 19px;
    bottom: auto;
    width: auto;
    height: 2px;
    background-image: linear-gradient(90deg, var(--thread) 0 calc(100% - 140px), transparent calc(100% - 140px));
    background-color: transparent;
  }

  .how::after {
    content: '';
    position: absolute;
    right: 0;
    top: 19px;
    width: 140px;
    height: 2px;
    background-image: linear-gradient(90deg, var(--thread) 0 8px, transparent 8px 14px);
    background-size: 14px 2px;
    background-repeat: repeat-x;
  }
}

.how__step {
  position: relative;
  display: flex;
  gap: 16px;
}

@media (min-width: 768px) {
  .how__step {
    flex-direction: column;
    gap: 18px;
  }
}

.how__num {
  position: relative;
  z-index: 1;
  flex: none;
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  font-size: 18px;
  font-weight: 600;
  color: var(--thread);
  background: var(--background);
  border: 2px solid var(--thread);
}

.how__title {
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 600;
  line-height: 1.3;
}

.how__text {
  margin-top: 6px;
  max-width: 340px;
  font-size: 14.5px;
  line-height: 1.6;
  color: var(--text-3);
}

.toc {
  display: grid;
  gap: 0 56px;
  margin-top: 24px;
  border-top: 1px solid var(--line);
}

@media (min-width: 768px) {
  .toc { grid-template-columns: 1fr 1fr; }
}

.toc__row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 15px 2px 13px;
  border-bottom: 1px solid var(--line);
  transition: color .15s;
}

.toc__title {
  font-family: var(--font-serif);
  font-optical-sizing: auto;
  font-size: 19px;
  font-weight: 500;
}

.toc__fill {
  flex: 1;
  min-width: 24px;
  height: 1px;
  transform: translateY(-4px);
  background-image: radial-gradient(circle, var(--line-2) 1.1px, transparent 1.3px);
  background-size: 7px 3px;
  background-repeat: repeat-x;
  background-position: 0 50%;
}

.toc__count {
  font-size: 17px;
  color: var(--text-3);
}

.toc__row:hover .toc__title,
.toc__row:hover .toc__count {
  color: var(--thread);
}

.toc__row--new {
  color: var(--text-3);
}

.toc__row--new .toc__title {
  font-style: italic;
}

.authors {
  display: grid;
  gap: 40px;
  align-items: center;
  padding: 28px 22px;
}

@media (min-width: 1024px) {
  .authors {
    grid-template-columns: 1fr 1fr;
    gap: 56px;
    padding: 48px 52px;
  }
}

.authors__list {
  margin-top: 22px;
  display: grid;
  gap: 10px;
  font-size: 15px;
  color: var(--text-2);
}

.authors__list li {
  position: relative;
  padding-left: 24px;
}

.authors__list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: .7em;
  width: 14px;
  height: 2px;
  border-radius: 2px;
  background: var(--thread);
}

.funnel {
  padding: 22px 20px;
  border-radius: 12px;
  background: var(--background);
  border: 1px solid var(--line);
}

.funnel__row {
  display: flex;
  gap: 12px;
  padding: 10px 10px;
  border-radius: 10px;
}

.funnel__n {
  width: 16px;
  padding-top: 1px;
  font-size: 14px;
  color: var(--text-4);
}

.funnel__row--hot {
  background: var(--thread-wash);
}

.funnel__row--hot .funnel__n {
  color: var(--thread);
}

.funnel__bar {
  height: 4px;
  margin-top: 7px;
  border-radius: 4px;
  background: var(--wash-2);
  overflow: hidden;
}

.funnel__bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: color-mix(in srgb, var(--foreground) 62%, transparent);
}

.funnel__row--hot .funnel__bar span {
  background: var(--thread);
}

.funnel__note {
  margin-top: 7px;
  font-size: 13px;
  line-height: 1.45;
  color: var(--thread);
}
</style>
