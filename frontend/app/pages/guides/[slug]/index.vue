<script setup lang="ts">
import {
  BadgeCheck, Bookmark, ChevronDown, Clock, Code2, Download, FileDown, GitFork, ListChecks,
  MessageSquare, Play, RotateCcw, ThumbsDown, ThumbsUp, WifiOff,
} from '@lucide/vue'
import { toast } from 'vue-sonner'
import type { BookmarkOut, CommentOut, CreatedOut, GuideCard, GuideDetail, RunOut } from '~/types/api'

const route = useRoute()
const router = useRouter()
const auth = useAuth()
const slug = computed(() => String(route.params.slug))

const { data: guide, error, refresh } = await useFetch<GuideDetail>(() => `/api/guides/${slug.value}`, {
  key: `guide-${slug.value}`,
  headers: anonHeaders(),
})
if (error.value) throw createError({ statusCode: 404, statusMessage: 'Инструкция не найдена', fatal: true })

onMounted(() => {
  if (!auth.user) refresh()
})

const { data: comments, refresh: refreshComments } = useFetch<CommentOut[]>(() => `/api/guides/${slug.value}/comments`, { default: () => [] })
const { data: forks } = useFetch<GuideCard[]>(() => `/api/guides/${slug.value}/forks`, { default: () => [] })
const { data: similar } = useFetch<GuideCard[]>(() => `/api/guides/${slug.value}/similar`, { default: () => [], server: false })
const { data: categories } = useCategories()

useHead(() => ({
  title: guide.value?.title ?? 'Инструкция',
  meta: [{ name: 'description', content: guide.value?.summary ?? '' }],
}))

const g = computed(() => guide.value!)
const run = computed(() => g.value.my_run)
const runStep = computed(() => Math.min((run.value?.current_step ?? 0) + 1, g.value.steps_count))
const open = ref<string | null>(null)
const commentsByStep = computed(() => {
  const map: Record<string, CommentOut[]> = {}
  for (const c of comments.value ?? []) map[c.step_key ?? '_'] = [...(map[c.step_key ?? '_'] ?? []), c]
  return map
})

async function start(restart = false) {
  if (restart) {
    await api<RunOut>(`/api/guides/${slug.value}/runs`, { method: 'POST', query: { restart: true } })
  }
  router.push(`/guides/${slug.value}/run`)
}

async function toggleBookmark() {
  if (!auth.user) return router.push({ path: '/login', query: { next: route.fullPath } })
  const r = await api<BookmarkOut>(`/api/guides/${slug.value}/bookmark`, { method: 'POST' })
  guide.value!.bookmarked = r.bookmarked
  toast.success(r.bookmarked ? 'Сохранено в «Мои»' : 'Убрано из сохранённых')
}

const forking = ref(false)
async function fork() {
  if (!auth.user) return router.push({ path: '/login', query: { next: route.fullPath } })
  forking.value = true
  try {
    const r = await api<CreatedOut>(`/api/guides/${slug.value}/fork`, { method: 'POST' })
    toast.success('Форк создан — улучшайте и публикуйте свою версию')
    router.push(`/studio/${r.id}`)
  }
  finally {
    forking.value = false
  }
}

async function rate(value: number) {
  const r = await api<{ rating: number | null, rating_count: number, my_rating: number }>(`/api/guides/${slug.value}/rating`, { method: 'POST', body: { value } })
  Object.assign(guide.value!, { rating: r.rating, rating_count: r.rating_count, my_rating: r.my_rating })
  toast.success('Спасибо за оценку!')
}

const offlineSaved = ref(false)
onMounted(() => (offlineSaved.value = hasOfflineRun(slug.value)))
async function saveOffline() {
  await prepareOffline(slug.value)
  offlineSaved.value = true
  toast.success('Инструкция доступна без интернета', { description: 'Прогресс синхронизируется, когда сеть вернётся' })
}

const newComment = ref('')
const posting = ref(false)
async function postComment() {
  if (!newComment.value.trim()) return
  posting.value = true
  try {
    await api(`/api/guides/${slug.value}/comments`, { method: 'POST', body: { body: newComment.value, kind: 'comment' } })
    newComment.value = ''
    refreshComments()
  }
  finally {
    posting.value = false
  }
}

const embedOpen = ref(false)
const origin = computed(() => (import.meta.client ? window.location.origin : ''))
const embedCode = computed(() => `<iframe src="${origin.value}/embed/${slug.value}" width="100%" height="680" style="border:0;border-radius:24px" title="${g.value.title} — Нить" loading="lazy"></iframe>`)
async function copyEmbed() {
  await navigator.clipboard.writeText(embedCode.value)
  toast.success('Код для вставки скопирован')
}

const KIND: Record<string, string> = { question: 'вопрос', tip: 'совет', comment: 'комментарий' }
</script>

<template>
  <div v-if="guide" class="mx-auto max-w-[1180px] px-5 pt-10">
    <div class="grid gap-8 lg:grid-cols-[1fr_360px]">
      <div class="min-w-0">
        <div class="flex flex-wrap items-center gap-2 rise">
          <NuxtLink :to="{ path: '/guides', query: { category: g.category } }" class="tag hover:text-foreground">
            <CategoryIcon :slug="g.category" class="size-3.5" />{{ categoryTitle(categories, g.category) }}
          </NuxtLink>
          <span class="tag">v{{ g.version.number }}</span>
          <span v-if="g.verified" class="tag tag--ok"><BadgeCheck class="size-3.5" />проверено экспертом</span>
          <NuxtLink v-if="g.forked_from" :to="`/guides/${g.forked_from.slug}`" class="tag hover:text-foreground">
            <GitFork class="size-3.5" />форк «{{ g.forked_from.title }}»
          </NuxtLink>
        </div>

        <h1 class="mt-5 text-[36px] md:text-[54px] font-extrabold leading-[1.04] tracking-[-0.035em] silver halo rise" style="--lh: 1.04em; --i: 1">
          {{ g.title }}
        </h1>
        <p class="mt-4 text-[17px] leading-relaxed text-[var(--text-2)] max-w-[680px] halo rise" style="--i: 2">
          {{ g.summary }}
        </p>

        <div class="mt-6 flex flex-wrap gap-x-6 gap-y-2 mono text-[13px] text-[var(--text-3)] rise" style="--i: 3">
          <span class="inline-flex items-center gap-1.5"><ListChecks class="size-4" />{{ pl(g.steps_count, 'шаг', 'шага', 'шагов') }}</span>
          <span class="inline-flex items-center gap-1.5"><Clock class="size-4" />{{ formatMinutes(g.est_minutes) }}</span>
          <span>сложность: {{ DIFFICULTY[g.difficulty]?.toLowerCase() }}</span>
          <span v-for="t in g.tags" :key="t">#{{ t }}</span>
        </div>

        <div class="mt-8 glass glass--lg p-5 md:p-6 rise" style="--i: 4">
          <template v-if="run && run.status !== 'completed'">
            <div class="flex items-center justify-between text-sm mb-3">
              <span class="label">ваш прогресс</span>
              <span class="mono text-[var(--text-3)]">{{ percent(run.progress) }}</span>
            </div>
            <HairlineBar :value="run.progress" />
            <div class="mt-5 flex flex-wrap gap-3">
              <button class="btn-chrome" @click="start()">
                <Play class="size-4" /> Продолжить с шага {{ runStep }}
              </button>
              <button class="btn-glass" @click="start(true)">
                <RotateCcw class="size-4" /> Заново
              </button>
            </div>
            <p v-if="run.outdated" class="mt-3 text-[13px] text-[var(--warn)]">
              Вы проходите v{{ run.version_number }}, а автор уже обновил инструкцию до v{{ g.version.number }} — можно начать заново по новой версии.
            </p>
          </template>
          <template v-else-if="run && run.status === 'completed'">
            <div class="flex flex-wrap items-center gap-4 justify-between">
              <div>
                <div class="font-bold text-lg">
                  Вы прошли эту инструкцию 🎉
                </div>
                <div class="text-sm text-[var(--text-3)] mt-1 flex items-center gap-2">
                  {{ g.my_rating ? 'Ваша оценка:' : 'Оцените, насколько помогло:' }}
                  <RatingStars :value="g.my_rating ?? 0" interactive :size="18" @select="rate" />
                </div>
              </div>
              <button class="btn-glass" @click="start(true)">
                <RotateCcw class="size-4" /> Пройти ещё раз
              </button>
            </div>
          </template>
          <template v-else>
            <div class="flex flex-wrap items-center gap-4 justify-between">
              <div>
                <div class="font-bold text-lg">
                  Готовы? Это займёт около {{ formatMinutes(g.est_minutes) }}
                </div>
                <div class="text-sm text-[var(--text-3)] mt-1">
                  Можно без регистрации — прогресс сохранится на этом устройстве.
                </div>
              </div>
              <button class="btn-chrome" @click="start()">
                <Play class="size-4" /> Начать прохождение
              </button>
            </div>
          </template>

          <div class="mt-5 pt-4 border-t border-[var(--line)] flex flex-wrap gap-2">
            <button class="chip" :class="g.bookmarked && 'chip--on'" @click="toggleBookmark">
              <Bookmark class="size-4" :class="g.bookmarked && 'fill-current'" /> {{ g.bookmarked ? 'Сохранено' : 'Сохранить' }}
            </button>
            <button class="chip" :disabled="forking" @click="fork">
              <GitFork class="size-4" /> Сделать форк
            </button>
            <button class="chip" :class="offlineSaved && 'chip--on'" @click="saveOffline">
              <component :is="offlineSaved ? WifiOff : Download" class="size-4" /> {{ offlineSaved ? 'Доступно офлайн' : 'Скачать офлайн' }}
            </button>
            <NuxtLink :to="`/guides/${g.slug}/print`" target="_blank" class="chip">
              <FileDown class="size-4" /> PDF
            </NuxtLink>
            <button class="chip" @click="embedOpen = true">
              <Code2 class="size-4" /> Встроить
            </button>
          </div>
        </div>

        <section class="mt-12">
          <div class="flex items-end justify-between">
            <SectionLabel num="01">
              маршрут
            </SectionLabel>
            <span class="label">{{ pl(comments?.length ?? 0, 'комментарий', 'комментария', 'комментариев') }}</span>
          </div>
          <ol class="mt-5 space-y-2.5">
            <li v-for="(s, i) in g.steps" :key="s.key" class="step glass rise" :style="{ '--i': Math.min(i, 8) }">
              <button class="step__head" :aria-expanded="open === s.key" @click="open = open === s.key ? null : s.key">
                <span class="step__num display">{{ String(i + 1).padStart(2, '0') }}</span>
                <span class="flex-1 min-w-0 text-left">
                  <span class="block font-semibold text-[16px] leading-snug">{{ s.title }}</span>
                  <span class="mt-1 flex flex-wrap gap-x-4 gap-y-1 mono text-[12px] text-[var(--text-4)]">
                    <span>{{ formatMinutes(s.minutes) }}</span>
                    <span v-if="s.checklist.length">{{ pl(s.checklist.length, 'пункт', 'пункта', 'пунктов') }} чек-листа</span>
                    <span v-if="g.step_stats[s.key]?.up" class="inline-flex items-center gap-1"><ThumbsUp class="size-3" />{{ g.step_stats[s.key]!.up }}</span>
                    <span v-if="g.step_stats[s.key]?.down" class="inline-flex items-center gap-1"><ThumbsDown class="size-3" />{{ g.step_stats[s.key]!.down }}</span>
                    <span v-if="commentsByStep[s.key]?.length" class="inline-flex items-center gap-1"><MessageSquare class="size-3" />{{ commentsByStep[s.key]!.length }}</span>
                  </span>
                </span>
                <ChevronDown class="size-5 text-[var(--text-3)] transition-transform" :class="open === s.key && 'rotate-180'" />
              </button>
              <div v-if="open === s.key" class="px-5 pb-5 md:pl-[76px]">
                <MarkdownView :source="s.body" />
                <ul v-if="s.checklist.length" class="mt-4 space-y-2">
                  <li v-for="c in s.checklist" :key="c.key" class="flex items-start gap-2.5 text-[14.5px]">
                    <span class="mt-0.5 size-[18px] rounded-md shrink-0 shadow-[inset_0_0_0_1.5px_var(--line-2)]" />{{ c.text }}
                  </li>
                </ul>
                <div v-if="commentsByStep[s.key]?.length" class="mt-5 space-y-2">
                  <div v-for="c in commentsByStep[s.key]" :key="c.id" class="comment">
                    <UserAvatar :id="c.user.id" :name="c.user.name" :size="28" />
                    <div class="min-w-0">
                      <div class="flex flex-wrap items-center gap-2 text-[12.5px]">
                        <span class="font-semibold">{{ c.user.name }}</span>
                        <span v-if="c.user.role === 'expert'" class="tag tag--ok !h-5">эксперт</span>
                        <span v-if="c.is_author" class="tag tag--lit !h-5">автор</span>
                        <span class="tag !h-5" :class="c.kind === 'tip' && 'tag--ice'">{{ KIND[c.kind] }}</span>
                        <span class="text-[var(--text-4)]">{{ timeAgo(c.created_at) }}</span>
                      </div>
                      <p class="mt-1 text-[14px] text-[var(--text-2)] whitespace-pre-line">
                        {{ c.body }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </li>
          </ol>
        </section>

        <section class="mt-12">
          <SectionLabel num="02">
            обсуждение
          </SectionLabel>
          <div class="mt-5 glass p-5">
            <form v-if="auth.user" class="flex gap-3 items-start" @submit.prevent="postComment">
              <UserAvatar :id="auth.user.id" :name="auth.user.name" :size="34" />
              <textarea v-model="newComment" class="field !min-h-[52px] !h-[52px] focus:!h-24 transition-[height]" placeholder="Поделитесь опытом или задайте вопрос по инструкции" />
              <button class="btn-chrome btn-chrome--sm mt-1.5" :disabled="posting || !newComment.trim()">
                Отправить
              </button>
            </form>
            <p v-else class="text-[var(--text-3)] text-sm">
              <NuxtLink :to="{ path: '/login', query: { next: route.fullPath } }" class="underline text-foreground">Войдите</NuxtLink>, чтобы комментировать. Советы к конкретному шагу удобнее оставлять прямо во время прохождения.
            </p>
            <div v-if="commentsByStep._?.length" class="mt-5 space-y-2">
              <div v-for="c in commentsByStep._" :key="c.id" class="comment">
                <UserAvatar :id="c.user.id" :name="c.user.name" :size="28" />
                <div>
                  <div class="text-[12.5px]">
                    <span class="font-semibold">{{ c.user.name }}</span> <span class="text-[var(--text-4)]">· {{ timeAgo(c.created_at) }}</span>
                  </div>
                  <p class="mt-1 text-[14px] text-[var(--text-2)] whitespace-pre-line">
                    {{ c.body }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section v-if="forks?.length" class="mt-12">
          <SectionLabel num="03">
            улучшенные версии
          </SectionLabel>
          <p class="mt-3 text-[var(--text-3)] text-sm">
            Форки — версии этой инструкции от других авторов. Сравните, какая проходится легче.
          </p>
          <div class="mt-5 grid gap-4 sm:grid-cols-2">
            <GuideCard v-for="(f, i) in forks" :key="f.id" :guide="f" :index="i" compact />
          </div>
        </section>
      </div>

      <aside class="space-y-4 lg:sticky lg:top-[96px] self-start">
        <div class="glass glass--lg p-6 overflow-hidden rise" style="--i: 2">
          <img :src="`/glass/${g.cover}.webp`" alt="" class="absolute -right-12 -top-10 w-48 opacity-60 -z-[1] pointer-events-none">
          <div class="label">индекс полезности</div>
          <div class="mt-2 flex items-end gap-3">
            <span class="display silver text-[72px] leading-[.9]">{{ g.usefulness }}</span>
            <span class="mb-2 text-sm text-[var(--text-3)]">из 100</span>
          </div>
          <p class="mt-2 text-[12.5px] text-[var(--text-4)] leading-snug">
            Оценки, доля дошедших до конца и «полезно» на шагах{{ g.verified ? ' + проверка экспертом' : '' }}.
          </p>
          <div class="mt-5 grid grid-cols-2 gap-3">
            <div class="stat">
              <span class="stat__v mono">{{ percent(g.completion_rate) }}</span>
              <span class="stat__l">дошли до конца</span>
            </div>
            <div class="stat">
              <span class="stat__v mono">{{ formatNumber(g.runs_count) }}</span>
              <span class="stat__l">прохождений</span>
            </div>
            <div class="stat col-span-2">
              <span class="flex items-center gap-2">
                <span class="stat__v mono">{{ g.rating?.toFixed(1) ?? '—' }}</span>
                <RatingStars :value="g.rating ?? 0" :size="14" />
              </span>
              <span class="stat__l">{{ pl(g.rating_count, 'оценка', 'оценки', 'оценок') }}</span>
            </div>
          </div>
        </div>

        <NuxtLink :to="`/u/${g.author.id}`" class="glass glass--hover p-5 flex items-center gap-3 rise" style="--i: 3">
          <UserAvatar :id="g.author.id" :name="g.author.name" :size="44" />
          <div class="min-w-0">
            <div class="label">автор</div>
            <div class="font-semibold truncate mt-0.5">
              {{ g.author.name }}
            </div>
          </div>
        </NuxtLink>

        <div v-if="g.verified_by" class="glass p-5 rise" style="--i: 4">
          <div class="flex items-center gap-3">
            <span class="ico text-[var(--ok)]"><BadgeCheck class="size-5" /></span>
            <div>
              <div class="font-semibold">
                Проверено экспертом
              </div>
              <div class="text-[13px] text-[var(--text-3)]">
                {{ g.verified_by.name }} · {{ formatDate(g.verified_at) }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="similar?.length" class="glass p-5 rise" style="--i: 5">
          <div class="label mb-3">
            похожие по смыслу
          </div>
          <NuxtLink v-for="s in similar" :key="s.id" :to="`/guides/${s.slug}`" class="flex items-center gap-3 py-2.5 group border-t first:border-t-0 border-[var(--line)]">
            <img :src="`/glass/${s.cover}.webp`" alt="" class="size-10 object-contain">
            <span class="min-w-0">
              <span class="block text-[14px] font-medium leading-snug group-hover:underline underline-offset-2">{{ s.title }}</span>
              <span class="block mono text-[11.5px] text-[var(--text-4)]">{{ s.steps_count }} шагов · {{ s.usefulness }}</span>
            </span>
          </NuxtLink>
        </div>
      </aside>
    </div>

    <Dialog v-model:open="embedOpen">
      <DialogContent class="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Встроить на свой сайт</DialogTitle>
          <DialogDescription>
            Интерактивный виджет с чек-листами — для сайта кафедры, блога или Notion. Прогресс ученика хранится в его браузере.
          </DialogDescription>
        </DialogHeader>
        <pre class="mono text-[12.5px] whitespace-pre-wrap break-all p-4 rounded-2xl bg-[var(--wash)] shadow-[inset_0_0_0_1px_var(--line)]">{{ embedCode }}</pre>
        <div class="flex gap-3">
          <button class="btn-chrome btn-chrome--sm" @click="copyEmbed">
            Скопировать код
          </button>
          <a :href="`/embed/${g.slug}`" target="_blank" class="btn-glass btn-glass--sm">Открыть превью</a>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<style scoped>
.step {
  border-radius: 22px;
}

.step__head {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  padding: 16px 18px;
}

.step__num {
  width: 44px;
  font-size: 22px;
  color: var(--text-4);
  flex: none;
}

.comment {
  display: flex;
  gap: 10px;
  padding: 12px;
  border-radius: 16px;
  background: var(--wash);
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px 14px;
  border-radius: 16px;
  background: var(--wash);
  box-shadow: inset 0 0 0 1px var(--line);
}

.stat__v {
  font-size: 20px;
  font-weight: 600;
}

.stat__l {
  font-size: 12px;
  color: var(--text-4);
}
</style>
