<script setup lang="ts">
import { ArrowRight } from '@lucide/vue'

useHead({ title: 'О проекте' })

const loop = [
  { t: 'Найти', d: 'Поиск понимает запрос своими словами, прощает опечатки и сортирует по полезности.' },
  { t: 'Пройти', d: 'Один шаг на экране, чек-лист к каждому шагу, прогресс сохраняется.' },
  { t: 'Помочь', d: '«Полезно / не полезно», советы к шагу, кнопка «Застрял», правка или форк.' },
  { t: 'Улучшить', d: 'Автор видит воронку по шагам, исправляет проблемные места и сравнивает версии.' },
]

const signals = [
  { w: 50, t: 'Доля бросивших на шаге среди дошедших до него' },
  { w: 20, t: 'Во сколько раз медианное время больше заявленного' },
  { w: 15, t: 'Доля оценок «не полезно»' },
  { w: 15, t: 'Как часто нажимают «Застрял»' },
]

const search = [
  { t: 'Морфология', d: 'полнотекстовый поиск PostgreSQL: «справки» находит «справку»' },
  { t: 'Опечатки', d: 'триграммы pg_trgm по названию и тегам' },
  { t: 'Смысл', d: 'эмбеддинги ru-en-RoSBERTa в pgvector: «не включается комп после сборки» находит сборку ПК' },
]

const collab = [
  { t: 'Версии', d: 'Публикация создаёт неизменяемую версию, прохождения привязаны к ней, поэтому видно, помогла ли правка.' },
  { t: 'Форки', d: 'Можно сделать свою версию чужой инструкции. Шаги сохраняют ключи, форк и оригинал сравниваются.' },
  { t: 'Правки', d: 'Читатель предлагает новую редакцию шага, автор смотрит «было / стало» и принимает в черновик.' },
  { t: 'Эксперты', d: 'Проверяют инструкции в своих категориях. Проверенные получают отметку.' },
]

const ai = [
  'черновик инструкции по теме или из готового текста',
  'улучшение шага: проще, подробнее, с чек-листом',
  'проверка полноты: пропущенные шаги и неясные места',
  'разбор проблемного шага по метрикам и комментариям',
  'подсказка, когда человек нажал «Застрял»',
]

const extras = [
  { t: 'Офлайн', d: 'инструкцию можно сохранить и пройти без сети, события отправятся позже' },
  { t: 'PDF', d: 'печатная версия с чек-листами и QR-кодом на онлайн-версию' },
  { t: 'Встраивание', d: 'виджет через iframe для сайта кафедры или блога' },
]

const stack = [
  { t: 'Фронтенд', d: 'Nuxt 4, Vue 3, Tailwind v4, shadcn-vue, Pinia, TipTap, PWA' },
  { t: 'Бэкенд', d: 'FastAPI, SQLAlchemy 2, Alembic, Pydantic' },
  { t: 'Данные', d: 'PostgreSQL 17, pgvector, pg_trgm, S3' },
  { t: 'ИИ', d: 'GigaChat-2-Max (Сбер): ответ в JSON по шаблону, проверка Pydantic. Эмбеддинги — ai-forever/ru-en-RoSBERTa локально' },
]
</script>

<template>
  <div class="mx-auto max-w-[760px] px-5 pt-12">
    <h1 class="page-title">
      О проекте
    </h1>
    <p class="mt-4 text-[16.5px] leading-relaxed text-[var(--text-2)]">
      Нить — платформа пошаговых инструкций с чек-листами. Люди проходят инструкции шаг за шагом,
      а авторы видят, на каком шаге их бросают, и исправляют именно его.
    </p>

    <section class="about-section">
      <h2 class="section-title">
        Как это работает
      </h2>
      <dl class="mt-4 divide-y divide-[var(--line)] border-y border-[var(--line)]">
        <div v-for="s in loop" :key="s.t" class="py-3 grid gap-1 sm:grid-cols-[140px_1fr]">
          <dt class="font-medium">
            {{ s.t }}
          </dt>
          <dd class="text-[var(--text-3)]">
            {{ s.d }}
          </dd>
        </div>
      </dl>
    </section>

    <section class="about-section">
      <h2 class="section-title">
        Индекс проблемного шага
      </h2>
      <p class="mt-2 text-[var(--text-3)]">
        Каждому шагу считается число от 0 до 100. От 25 шаг помечается, от 45 — считается узким местом.
      </p>
      <div class="mt-4 space-y-3">
        <div v-for="s in signals" :key="s.t" class="grid grid-cols-[48px_1fr] items-center gap-3">
          <span class="tabular-nums font-semibold text-right">{{ s.w }}%</span>
          <div>
            <div class="text-[14.5px]">
              {{ s.t }}
            </div>
            <div class="mt-1.5 h-1 rounded bg-[var(--wash-2)] overflow-hidden">
              <div class="h-full bg-primary" :style="{ width: `${s.w * 2}%` }" />
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="about-section">
      <h2 class="section-title">
        Поиск
      </h2>
      <ul class="mt-3 space-y-2 text-[var(--text-2)]">
        <li v-for="s in search" :key="s.t">
          <span class="font-medium text-foreground">{{ s.t }}</span> — {{ s.d }}
        </li>
      </ul>
      <p class="mt-3 text-[var(--text-3)]">
        Три списка результатов объединяются через Reciprocal Rank Fusion. Если эмбеддинги недоступны,
        поиск работает на первых двух.
      </p>
    </section>

    <section class="about-section">
      <h2 class="section-title">
        Совместная работа
      </h2>
      <dl class="mt-4 divide-y divide-[var(--line)] border-y border-[var(--line)]">
        <div v-for="c in collab" :key="c.t" class="py-3 grid gap-1 sm:grid-cols-[140px_1fr]">
          <dt class="font-medium">
            {{ c.t }}
          </dt>
          <dd class="text-[var(--text-3)]">
            {{ c.d }}
          </dd>
        </div>
      </dl>
    </section>

    <section class="about-section">
      <h2 class="section-title">
        ИИ
      </h2>
      <p class="mt-2 text-[var(--text-3)]">
        Работает на GigaChat. Что умеет:
      </p>
      <ul class="mt-3 list-disc pl-5 space-y-1.5 text-[var(--text-2)] marker:text-[var(--text-4)]">
        <li v-for="a in ai" :key="a">
          {{ a }}
        </li>
      </ul>
    </section>

    <section class="about-section">
      <h2 class="section-title">
        Ещё
      </h2>
      <ul class="mt-3 space-y-2 text-[var(--text-2)]">
        <li v-for="e in extras" :key="e.t">
          <span class="font-medium text-foreground">{{ e.t }}</span> — {{ e.d }}
        </li>
      </ul>
    </section>

    <section class="about-section">
      <h2 class="section-title">
        Стек
      </h2>
      <dl class="mt-4 divide-y divide-[var(--line)] border-y border-[var(--line)]">
        <div v-for="s in stack" :key="s.t" class="py-3 grid gap-1 sm:grid-cols-[140px_1fr]">
          <dt class="font-medium">
            {{ s.t }}
          </dt>
          <dd class="text-[var(--text-3)]">
            {{ s.d }}
          </dd>
        </div>
      </dl>
    </section>

    <div class="about-section flex flex-wrap gap-2">
      <NuxtLink to="/guides" class="btn-primary">
        Открыть каталог <ArrowRight class="size-4" />
      </NuxtLink>
      <NuxtLink to="/studio/new" class="btn-secondary">
        Написать инструкцию
      </NuxtLink>
    </div>
  </div>
</template>

<style scoped>
.about-section {
  margin-top: 44px;
}
</style>
