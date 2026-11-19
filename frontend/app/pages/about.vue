<script setup lang="ts">
import {
  ArrowRight, BadgeCheck, Bot, ChartNoAxesColumn, Code2, Database, FileDown, GitFork, GitPullRequest,
  Layers, LifeBuoy, ListChecks, MessageSquareText, Search, ShieldCheck, Sparkles, WifiOff,
} from '@lucide/vue'

useHead({ title: 'Как это работает' })

const problems = [
  { t: 'Разбросано', d: 'Нужное размазано по форумам, чатам и видео на 40 минут.' },
  { t: 'Без порядка', d: 'Непонятно, что делать сначала, а что потом, — и сколько это займёт.' },
  { t: 'Легко пропустить', d: 'Забытый шаг всплывает в самом конце: «а печать в деканате поставили?»' },
  { t: 'Авторы вслепую', d: 'Автор не знает, где читатели застряли и бросили, — инструкция устаревает.' },
]

const loop = [
  { n: '01', t: 'Найди', icon: Search, d: 'Умный поиск понимает формулировку задачи «своими словами», прощает опечатки и сортирует по полезности.' },
  { n: '02', t: 'Пройди', icon: ListChecks, d: 'Один экран — один шаг. Чек-лист не пускает дальше, пока не отмечено важное. Прогресс-бар и таймлайн шагов.' },
  { n: '03', t: 'Помоги', icon: MessageSquareText, d: '«Полезно / не полезно», советы к шагу, кнопка «Застрял», предложение правки, форк улучшенной версии.' },
  { n: '04', t: 'Улучши', icon: ChartNoAxesColumn, d: 'Автор видит воронку по шагам и индекс узких мест, ИИ предлагает новую редакцию, новая версия сравнивается со старой.' },
]

const signals = [
  { w: 50, t: 'Доля бросивших', d: 'среди дошедших до шага — главный сигнал' },
  { w: 20, t: 'Время против оценки', d: 'во сколько раз медиана превышает заявленные минуты' },
  { w: 15, t: '«Не полезно»', d: 'доля негативных голосов на шаге' },
  { w: 15, t: '«Застрял»', d: 'как часто ученики просят помощи' },
]

const search = [
  { t: 'Морфология', d: 'Полнотекстовый поиск PostgreSQL со словарём russian: «справки» найдёт «справку». Веса: название › описание › шаги.', tag: 'fts' },
  { t: 'Опечатки', d: 'Триграммы pg_trgm по названию и тегам: «Dockr», «акадмический» — всё равно найдётся.', tag: 'pg_trgm' },
  { t: 'Смысл', d: 'Эмбеддинги bge-m3 в pgvector: «не включается комп после сборки» → «Собрать игровой ПК».', tag: 'pgvector' },
  { t: 'Слияние', d: 'Три ранжирования объединяются Reciprocal Rank Fusion, совпадение подсвечивается в фрагменте текста.', tag: 'rrf' },
]

const collab = [
  { icon: Layers, t: 'Версии', d: 'Черновик редактируется, публикация создаёт неизменяемую версию. Прохождения привязаны к версии — видно, стало ли лучше после правки.' },
  { icon: GitFork, t: 'Форки', d: 'Любой может сделать улучшенную версию чужой инструкции. Ключи шагов сохраняются — форк и оригинал можно сравнивать.' },
  { icon: GitPullRequest, t: 'Правки как pull request', d: 'Ученик предлагает новую редакцию шага, автор видит «было / стало» и вливает одной кнопкой в черновик.' },
  { icon: BadgeCheck, t: 'Роли', d: 'Ученик, эксперт и админ. Эксперт проверяет инструкции в своих категориях — бейдж и бонус к полезности.' },
]

const ai = [
  { t: 'Черновик по теме', d: 'Пишешь «оформить академ» — получаешь шаги с чек-листами и оценкой времени.' },
  { t: 'Импорт из текста', d: 'Пост с форума или конспект видео → структурированная инструкция.' },
  { t: 'Улучшить шаг', d: 'Понятнее, проще, с чек-листом или с частыми ошибками.' },
  { t: 'Проверка полноты', d: 'Редактор находит пропущенные шаги, неясности и опасные места.' },
  { t: 'Разбор узких мест', d: 'ИИ читает метрики и комментарии к проблемному шагу и пишет новую редакцию.' },
  { t: 'Подсказка «Застрял»', d: 'Короткий совет ученику с учётом его вопроса и советов других.' },
]

const extras = [
  { icon: WifiOff, t: 'Офлайн', d: 'PWA: инструкцию можно скачать, проходить без сети — события дойдут, когда сеть вернётся (идемпотентно).' },
  { icon: FileDown, t: 'PDF', d: 'Печатная версия с квадратиками чек-листов и QR-кодом на онлайн-прохождение.' },
  { icon: Code2, t: 'Встраивание', d: 'iframe-виджет для сайта кафедры или блога: интерактивные шаги прямо на чужой странице.' },
  { icon: LifeBuoy, t: 'Мобильная версия', d: 'Таб-бар, крупные чекбоксы, жесты — проходить удобно с телефона, стоя в очереди в деканат.' },
]

const stack = [
  { icon: Sparkles, t: 'Фронтенд', d: 'Nuxt 4 · Vue 3 · Tailwind v4 · shadcn-vue · Pinia · TipTap · PWA' },
  { icon: ShieldCheck, t: 'Бэкенд', d: 'FastAPI · SQLAlchemy 2 (async) · Alembic · Pydantic · JWT в httpOnly-cookie' },
  { icon: Database, t: 'Данные', d: 'PostgreSQL 17 · pgvector · pg_trgm · S3-хранилище картинок' },
  { icon: Bot, t: 'ИИ', d: 'OpenRouter: DeepSeek V4.1 Flash со structured outputs · bge-m3 для эмбеддингов' },
]
</script>

<template>
  <div class="mx-auto max-w-[1180px] px-5 pt-14">
    <section class="scrim max-w-[820px]">
      <SectionLabel code>
        как это работает
      </SectionLabel>
      <h1 class="mt-6 display silver halo text-[42px] md:text-[78px] leading-[1] rise" style="--lh: 1em">
        Инструкция, которая учится на своих читателях
      </h1>
      <p class="mt-6 text-[17px] md:text-[19px] leading-relaxed text-[var(--text-2)] rise" style="--i: 1">
        Нить превращает разрозненные советы в маршрут с чек-листами, а каждое прохождение — в данные,
        по которым автор находит и чинит места, где люди спотыкаются.
      </p>
    </section>

    <section class="mt-20">
      <SectionLabel num="00">
        проблема
      </SectionLabel>
      <h2 class="h2 silver halo">
        Почему «на ощупь» не работает
      </h2>
      <div class="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <article v-for="(p, i) in problems" :key="p.t" class="glass p-6 rise" :style="{ '--i': i }">
          <span class="mono text-[12px] text-[var(--crit)]">×{{ i + 1 }}</span>
          <h3 class="mt-3 text-[20px] font-bold">
            {{ p.t }}
          </h3>
          <p class="mt-2 text-[14.5px] text-[var(--text-3)] leading-snug">
            {{ p.d }}
          </p>
        </article>
      </div>
    </section>

    <section class="mt-20">
      <SectionLabel num="01">
        цикл
      </SectionLabel>
      <h2 class="h2 silver halo">
        Найди → пройди → помоги → улучши
      </h2>
      <div class="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <article v-for="(s, i) in loop" :key="s.n" class="glass glass--hover p-6 min-h-[260px] flex flex-col rise" :style="{ '--i': i }">
          <div class="flex items-start justify-between">
            <span class="display text-[44px] leading-none silver">{{ s.n }}</span>
            <span class="ico"><component :is="s.icon" class="size-[18px]" /></span>
          </div>
          <h3 class="mt-4 text-[24px] font-extrabold tracking-tight">
            {{ s.t }}
          </h3>
          <p class="mt-3 text-[14.5px] text-[var(--text-3)] leading-snug">
            {{ s.d }}
          </p>
        </article>
      </div>
    </section>

    <section class="mt-20">
      <div class="glass glass--lg p-6 md:p-12 grid gap-10 lg:grid-cols-[1fr_1fr] items-center overflow-hidden">
        <img src="/glass/torus.webp" alt="" class="absolute -right-24 -bottom-24 w-[420px] opacity-30 -z-[1] pointer-events-none">
        <div>
          <SectionLabel num="02">
            аналитика
          </SectionLabel>
          <h2 class="h2 silver">
            Индекс узкого места
          </h2>
          <p class="mt-5 text-[16px] leading-relaxed text-[var(--text-2)]">
            Для каждого шага складываем четыре сигнала из реальных прохождений в число от 0 до 100.
            Прохождение без активности дольше 30 минут считается брошенным — на том шаге, где человек остановился.
          </p>
          <div class="mt-6 flex flex-wrap gap-2">
            <span class="tag tag--crit">≥ 45 — критично</span>
            <span class="tag tag--warn">≥ 25 — внимание</span>
            <span class="tag tag--ok">&lt; 25 — ровно</span>
          </div>
          <p class="mt-5 text-[14px] text-[var(--text-3)]">
            Сравнение версий показывает эффект правки: у демо-инструкции про Docker после v2 доля бросивших на шаге с BIOS упала с 50% до 15%.
          </p>
        </div>
        <div class="space-y-3">
          <div v-for="s in signals" :key="s.t" class="signal">
            <div class="flex items-baseline justify-between gap-3">
              <span class="font-semibold">{{ s.t }}</span>
              <span class="display silver text-[28px] leading-none">{{ s.w }}%</span>
            </div>
            <div class="signal__bar">
              <span :style="{ width: `${s.w * 2}%` }" />
            </div>
            <p class="mt-2 text-[13px] text-[var(--text-4)]">
              {{ s.d }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <section class="mt-20">
      <SectionLabel num="03">
        умный поиск
      </SectionLabel>
      <h2 class="h2 silver halo">
        Три поиска в одном запросе
      </h2>
      <div class="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <article v-for="(s, i) in search" :key="s.t" class="glass p-6 rise" :style="{ '--i': i }">
          <span class="tag tag--ice">{{ s.tag }}</span>
          <h3 class="mt-4 text-[20px] font-bold">
            {{ s.t }}
          </h3>
          <p class="mt-2 text-[14.5px] text-[var(--text-3)] leading-snug">
            {{ s.d }}
          </p>
        </article>
      </div>
    </section>

    <section class="mt-20">
      <SectionLabel num="04">
        вместе
      </SectionLabel>
      <h2 class="h2 silver halo">
        Как в git, только для инструкций
      </h2>
      <div class="mt-8 grid gap-3 md:grid-cols-2">
        <article v-for="(c, i) in collab" :key="c.t" class="glass p-6 flex gap-4 rise" :style="{ '--i': i }">
          <span class="ico shrink-0"><component :is="c.icon" class="size-[18px]" /></span>
          <div>
            <h3 class="text-[19px] font-bold">
              {{ c.t }}
            </h3>
            <p class="mt-1.5 text-[14.5px] text-[var(--text-3)] leading-snug">
              {{ c.d }}
            </p>
          </div>
        </article>
      </div>
    </section>

    <section class="mt-20">
      <div class="glass glass--lg p-6 md:p-12 overflow-hidden">
        <img src="/glass/peanut.webp" alt="" class="absolute -right-16 -top-16 w-[300px] opacity-40 -z-[1] pointer-events-none">
        <SectionLabel num="05">
          ии-редактор
        </SectionLabel>
        <h2 class="h2 silver">
          ИИ пишет черновик — человек отвечает за правду
        </h2>
        <p class="mt-4 max-w-[640px] text-[15.5px] text-[var(--text-2)]">
          DeepSeek через OpenRouter отвечает строго по JSON-схеме (structured outputs), ответ валидируется Pydantic.
          Лимиты на пользователя и журнал расходов — в админке.
        </p>
        <div class="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div v-for="a in ai" :key="a.t" class="p-5 rounded-[20px] bg-[var(--wash)] shadow-[inset_0_0_0_1px_var(--line)]">
            <div class="flex items-center gap-2 font-semibold">
              <Sparkles class="size-4 text-[var(--ice)]" />{{ a.t }}
            </div>
            <p class="mt-1.5 text-[14px] text-[var(--text-3)] leading-snug">
              {{ a.d }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <section class="mt-20">
      <SectionLabel num="06">
        и ещё
      </SectionLabel>
      <h2 class="h2 silver halo">
        Везде, где нужна инструкция
      </h2>
      <div class="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <article v-for="(e, i) in extras" :key="e.t" class="glass p-6 rise" :style="{ '--i': i }">
          <span class="ico"><component :is="e.icon" class="size-[18px]" /></span>
          <h3 class="mt-4 text-[19px] font-bold">
            {{ e.t }}
          </h3>
          <p class="mt-2 text-[14px] text-[var(--text-3)] leading-snug">
            {{ e.d }}
          </p>
        </article>
      </div>
    </section>

    <section class="mt-20">
      <SectionLabel num="07">
        стек
      </SectionLabel>
      <h2 class="h2 silver halo">
        Под капотом
      </h2>
      <div class="mt-8 glass overflow-hidden">
        <div v-for="s in stack" :key="s.t" class="stack-row">
          <span class="ico size-9"><component :is="s.icon" class="size-4" /></span>
          <span class="font-semibold w-28 shrink-0">{{ s.t }}</span>
          <span class="mono text-[13px] text-[var(--text-3)]">{{ s.d }}</span>
        </div>
      </div>
    </section>

    <section class="mt-20 text-center">
      <h2 class="display silver halo text-[34px] md:text-[56px] leading-[1.02]" style="--lh: 1.02em">
        Попробуйте пройти нить
      </h2>
      <div class="mt-8 flex flex-wrap justify-center gap-3">
        <NuxtLink to="/guides" class="btn-chrome">
          Открыть каталог <ArrowRight class="size-4" />
        </NuxtLink>
        <NuxtLink to="/studio/new" class="btn-glass">
          <Sparkles class="size-4" /> Написать инструкцию
        </NuxtLink>
      </div>
    </section>
  </div>
</template>

<style scoped>
.h2 {
  margin-top: 14px;
  font-size: clamp(30px, 4.2vw, 52px);
  font-weight: 800;
  line-height: 1.05;
  letter-spacing: -.035em;
  --lh: 1.05em;
}

.signal {
  padding: 16px 18px;
  border-radius: 20px;
  background: var(--wash);
  box-shadow: inset 0 0 0 1px var(--line);
}

.signal__bar {
  height: 6px;
  margin-top: 10px;
  border-radius: 6px;
  background: var(--line);
  overflow: hidden;
}

.signal__bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(255, 255, 255, .25), #fff);
}

:root:not(.dark) .signal__bar span {
  background: linear-gradient(90deg, rgba(20, 25, 35, .25), #1a1d22);
}

.stack-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  flex-wrap: wrap;
}

.stack-row + .stack-row {
  box-shadow: inset 0 1px 0 var(--line);
}
</style>
