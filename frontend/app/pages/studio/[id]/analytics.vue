<script setup lang="ts">
import {
  AlertOctagon, AlertTriangle, ArrowDownRight, ArrowLeft, ArrowUpRight, Check, CircleCheck, Eye, LifeBuoy,
  MessageSquare, PenLine, Sparkles, ThumbsDown, ThumbsUp,
} from '@lucide/vue'
import { toast } from 'vue-sonner'
import type { Analytics, EditorDoc, GuideDetail, InsightItem, InsightsOut, StepAnalytics } from '~/types/api'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const id = Number(route.params.id)
const versionId = ref<number | null>(typeof route.query.version === 'string' ? Number(route.query.version) : null)

const { data, status, error } = useFetch<Analytics>(() => `/api/studio/guides/${id}/analytics`, {
  query: computed(() => (versionId.value ? { version_id: versionId.value } : {})),
  watch: [versionId],
})
useHead(() => ({ title: data.value ? `Аналитика · ${data.value.title}` : 'Аналитика' }))

const detail = ref<GuideDetail | null>(null)
watch(() => data.value?.slug, async (slug) => {
  if (slug && !detail.value) detail.value = await api<GuideDetail>(`/api/guides/${slug}`, { silent: true }).catch(() => null)
}, { immediate: true })

const a = computed(() => data.value)
const totals = computed(() => a.value?.totals)
const maxReached = computed(() => Math.max(1, ...(a.value?.steps.map(s => s.reached) ?? [1])))
const problems = computed(() => (a.value?.steps ?? []).filter(s => a.value!.bottlenecks.includes(s.key)).sort((x, y) => y.score - x.score))
const isLatest = computed(() => a.value && a.value.versions.at(-1)?.id === a.value.version.id)

const LEVEL = {
  critical: { label: 'критично', cls: 'tag--crit', icon: AlertOctagon },
  warn: { label: 'внимание', cls: 'tag--warn', icon: AlertTriangle },
  ok: { label: 'норма', cls: 'tag--ok', icon: CircleCheck },
} as const

function deltaDrop(s: StepAnalytics) {
  if (s.prev_drop_rate == null || !s.reached) return null
  return s.drop_rate - s.prev_drop_rate
}

const insights = ref<InsightsOut | null>(null)
const analyzing = ref(false)
async function analyze() {
  analyzing.value = true
  try {
    insights.value = await api<InsightsOut>(`/api/studio/guides/${id}/insights`, { method: 'POST' })
  }
  finally {
    analyzing.value = false
  }
}
const insightFor = (key: string) => insights.value?.items.find(i => i.step_key === key)
const showDiff = ref<InsightItem | null>(null)
const currentStep = (key: string) => detail.value?.steps.find(s => s.key === key)
const applied = ref<Set<string>>(new Set())

async function applyInsight(it: InsightItem) {
  const doc = await api<EditorDoc>(`/api/studio/guides/${id}`)
  const steps = doc.steps.map(s => ({
    key: s.key,
    title: s.key === it.step_key ? it.proposed_title : s.title,
    body: s.key === it.step_key ? it.proposed_body : s.body,
    minutes: s.minutes,
    checklist: s.key === it.step_key ? it.proposed_checklist.map(text => ({ text })) : s.checklist,
  }))
  await api(`/api/studio/guides/${id}`, {
    method: 'PUT',
    body: { title: doc.title, summary: doc.summary, category: doc.category, tags: doc.tags, difficulty: doc.difficulty, cover: doc.cover, steps },
  })
  applied.value.add(it.step_key)
  showDiff.value = null
  toast.success('Новая редакция шага в черновике', {
    description: 'Проверьте её в редакторе и опубликуйте новой версией — здесь появится сравнение',
    action: { label: 'В редактор', onClick: () => navigateTo(`/studio/${id}`) },
  })
}

const timeline = computed(() => a.value?.timeline ?? [])
const tMax = computed(() => Math.max(1, ...timeline.value.map(d => Math.max(d.started, d.completed))))
const hoverDay = ref<number | null>(null)
const dayLabel = (iso: string) => new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
</script>

<template>
  <div class="mx-auto max-w-[1240px] px-5 pt-10">
    <div v-if="error" class="glass glass--lg p-10 text-center">
      <p class="text-lg font-semibold">
        {{ apiErrorMessage(error, 'Аналитика недоступна') }}
      </p>
      <NuxtLink :to="`/studio/${id}`" class="btn-chrome mt-5">
        В редактор
      </NuxtLink>
    </div>

    <template v-else-if="a && totals">
      <div class="flex flex-wrap items-end justify-between gap-6">
        <div class="scrim min-w-0">
          <NuxtLink to="/studio" class="label hover:text-foreground">
            <ArrowLeft class="size-3.5" /> студия
          </NuxtLink>
          <h1 class="mt-4 text-[32px] md:text-[48px] font-extrabold leading-[1.05] silver" style="--lh: 1.05em">
            {{ a.title }}
          </h1>
          <p class="mt-2 text-[var(--text-3)]">
            Где ученики спотыкаются и что с этим делать
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <NuxtLink :to="`/studio/${id}`" class="btn-glass btn-glass--sm">
            <PenLine class="size-4" /> Редактор
          </NuxtLink>
          <NuxtLink :to="`/guides/${a.slug}`" class="btn-glass btn-glass--sm">
            <Eye class="size-4" /> Страница
          </NuxtLink>
        </div>
      </div>

      <div class="mt-6 flex flex-wrap items-center gap-2">
        <span class="label mr-1">версия</span>
        <button
          v-for="v in [...a.versions].reverse()"
          :key="v.id"
          class="chip !h-9"
          :class="a.version.id === v.id && 'chip--on'"
          @click="versionId = v.id === a.versions.at(-1)?.id ? null : v.id"
        >
          v{{ v.number }} <span class="mono text-[11px] opacity-60">{{ v.runs }}</span>
        </button>
        <span v-if="status === 'pending'" class="label">загружаем…</span>
      </div>

      <div class="mt-6 grid grid-cols-2 md:grid-cols-4 xl:grid-cols-7 gap-3">
        <div
v-for="(k, i) in [
          { l: 'прохождений', v: formatNumber(totals.runs) },
          { l: 'дошли до конца', v: percent(totals.completion_rate) },
          { l: 'бросили', v: formatNumber(totals.abandoned) },
          { l: 'в процессе', v: formatNumber(totals.active) },
          { l: 'медиана времени', v: totals.median_total_minutes != null ? formatMinutes(Math.round(totals.median_total_minutes)) : '—' },
          { l: 'рейтинг', v: totals.rating?.toFixed(1) ?? '—' },
          { l: '«полезно»', v: percent(totals.helpful_ratio) },
        ]" :key="k.l" class="glass p-4 rise" :style="{ '--i': i }"
        >
          <div class="label !text-[11px]">
            {{ k.l }}
          </div>
          <div class="mt-2 mono text-[26px] font-semibold leading-none">
            {{ k.v }}
          </div>
        </div>
      </div>

      <section class="mt-12">
        <div class="flex flex-wrap items-end justify-between gap-4">
          <div>
            <SectionLabel num="01">
              узкие места
            </SectionLabel>
            <h2 class="mt-3 text-[28px] md:text-[36px] font-extrabold silver">
              {{ problems.length ? `${pl(problems.length, 'шаг требует', 'шага требуют', 'шагов требуют')} внимания` : 'Ученики проходят ровно' }}
            </h2>
          </div>
          <button v-if="problems.length && isLatest" class="btn-chrome" :disabled="analyzing" @click="analyze">
            <Sparkles class="size-4" :class="analyzing && 'animate-pulse'" />
            {{ analyzing ? 'ИИ читает комментарии…' : insights ? 'Разобрать заново' : 'Разобрать с ИИ' }}
          </button>
        </div>
        <p v-if="insights" class="mt-4 glass p-4 text-[15px] text-[var(--text-2)]">
          <Sparkles class="size-4 inline mr-1.5 text-[var(--ice)]" />{{ insights.summary }}
        </p>

        <div v-if="problems.length" class="mt-6 grid gap-4 lg:grid-cols-2">
          <article v-for="(s, i) in problems" :key="s.key" class="problem glass glass--lg rise" :class="`problem--${s.level}`" :style="{ '--i': i }">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <span class="tag" :class="LEVEL[s.level].cls">
                    <component :is="LEVEL[s.level].icon" class="size-3.5" />{{ LEVEL[s.level].label }}
                  </span>
                  <span class="label">шаг {{ String(s.position + 1).padStart(2, '0') }}</span>
                </div>
                <h3 class="mt-3 text-[20px] font-bold leading-snug">
                  {{ s.title }}
                </h3>
              </div>
              <div class="text-right shrink-0">
                <div class="display text-[40px] leading-none" :class="s.level === 'critical' ? 'text-[var(--crit)]' : 'text-[var(--warn)]'">
                  {{ s.score }}
                </div>
                <div class="label !text-[10.5px] mt-1">
                  индекс
                </div>
              </div>
            </div>
            <ul class="mt-4 space-y-1.5">
              <li v-for="r in s.reasons" :key="r" class="flex items-center gap-2 text-[14px] text-[var(--text-2)]">
                <span class="pearl pearl--sm" />{{ r }}
              </li>
              <li v-if="s.prev_drop_rate != null" class="flex items-center gap-2 text-[14px]" :class="(deltaDrop(s) ?? 0) < 0 ? 'text-[var(--ok)]' : 'text-[var(--crit)]'">
                <component :is="(deltaDrop(s) ?? 0) < 0 ? ArrowDownRight : ArrowUpRight" class="size-4" />
                в прошлой версии бросали {{ percent(s.prev_drop_rate) }}
              </li>
            </ul>

            <div v-if="insightFor(s.key)" class="insight">
              <div class="label mb-2">
                <Sparkles class="size-3.5" /> разбор ии
              </div>
              <p class="text-[14px] text-[var(--text-2)]">
                <b class="text-foreground">Почему:</b> {{ insightFor(s.key)!.diagnosis }}
              </p>
              <p class="mt-2 text-[14px] text-[var(--text-2)]">
                <b class="text-foreground">Что сделать:</b> {{ insightFor(s.key)!.recommendation }}
              </p>
              <div class="mt-4 flex flex-wrap gap-2">
                <button class="btn-glass btn-glass--sm" @click="showDiff = insightFor(s.key)!">
                  Новая редакция шага
                </button>
                <button v-if="!applied.has(s.key)" class="btn-chrome btn-chrome--sm" @click="applyInsight(insightFor(s.key)!)">
                  <Check class="size-4" /> В черновик
                </button>
                <span v-else class="tag tag--ok h-[38px]"><Check class="size-3.5" />в черновике</span>
              </div>
            </div>
          </article>
        </div>
        <div v-else class="mt-6 glass p-6 flex items-center gap-4">
          <span class="ico text-[var(--ok)]"><CircleCheck class="size-5" /></span>
          <p class="text-[var(--text-2)]">
            Ни на одном шаге нет аномальных потерь, задержек или жалоб. Так держать!
          </p>
        </div>
      </section>

      <section class="mt-12">
        <SectionLabel num="02">
          воронка по шагам · v{{ a.version.number }}
        </SectionLabel>
        <div class="mt-5 glass glass--lg p-2 md:p-4 overflow-x-auto">
          <table class="funnel w-full min-w-[920px]">
            <thead>
              <tr>
                <th class="w-[34%]">
                  шаг
                </th>
                <th class="w-[22%]">
                  дошли
                </th>
                <th>бросили</th>
                <th>время</th>
                <th><ThumbsUp class="size-3.5 inline" /> / <ThumbsDown class="size-3.5 inline" /></th>
                <th><LifeBuoy class="size-3.5 inline" /></th>
                <th><MessageSquare class="size-3.5 inline" /></th>
                <th class="text-right">
                  индекс
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in a.steps" :key="s.key" :class="`row--${s.level}`">
                <td>
                  <div class="flex items-center gap-3">
                    <span class="mono text-[12px] text-[var(--text-4)] w-6">{{ String(s.position + 1).padStart(2, '0') }}</span>
                    <span class="font-medium text-[14px] leading-snug">{{ s.title }}</span>
                  </div>
                </td>
                <td :title="`Дошли: ${s.reached}, завершили шаг: ${s.completed}`">
                  <div class="bar">
                    <span class="bar__fill" :style="{ width: `${(s.reached / maxReached) * 100}%` }" />
                  </div>
                  <div class="mt-1 mono text-[12px] text-[var(--text-3)]">
                    {{ s.reached }} · {{ percent(totals.runs ? s.reached / totals.runs : 0) }}
                  </div>
                </td>
                <td>
                  <span class="mono text-[13px]" :class="s.drop_rate >= 0.08 && s.dropped >= 2 ? 'text-[var(--crit)]' : 'text-[var(--text-2)]'">{{ percent(s.drop_rate) }}</span>
                  <span v-if="deltaDrop(s) != null && Math.abs(deltaDrop(s)!) >= 0.01" class="delta mono" :class="deltaDrop(s)! < 0 ? 'delta--good' : 'delta--bad'">
                    {{ deltaDrop(s)! < 0 ? '↓' : '↑' }}{{ Math.abs(Math.round(deltaDrop(s)! * 100)) }} п.п.
                  </span>
                </td>
                <td class="mono text-[13px]">
                  <span class="text-[var(--text-2)]">{{ formatSeconds(s.median_seconds) }}</span>
                  <span class="text-[var(--text-4)]"> / {{ s.minutes }} мин</span>
                  <span v-if="s.time_ratio && s.time_ratio >= 1.6" class="block text-[11.5px] text-[var(--warn)]">×{{ s.time_ratio.toFixed(1) }}</span>
                </td>
                <td class="mono text-[13px] text-[var(--text-2)]">
                  {{ s.up }} / <span :class="s.down > s.up ? 'text-[var(--crit)]' : ''">{{ s.down }}</span>
                </td>
                <td class="mono text-[13px]" :class="s.stuck >= 5 ? 'text-[var(--warn)]' : 'text-[var(--text-2)]'">
                  {{ s.stuck }}
                </td>
                <td class="mono text-[13px] text-[var(--text-2)]">
                  {{ s.comments }}<span v-if="s.suggestions" class="text-[var(--ice)]"> +{{ pl(s.suggestions, 'правка', 'правки', 'правок') }}</span>
                </td>
                <td class="text-right">
                  <span class="score" :class="`score--${s.level}`" :title="LEVEL[s.level].label">
                    <component :is="LEVEL[s.level].icon" class="size-3.5" />{{ s.score }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="mt-3 text-[12.5px] text-[var(--text-4)] max-w-3xl">
          Индекс 0–100: 50% — доля бросивших среди дошедших, 20% — превышение времени над заявленным, 15% — «не полезно», 15% — нажатия «Застрял».
          Прохождение считается брошенным после 30 минут без активности.
        </p>
      </section>

      <section class="mt-12 grid gap-4 lg:grid-cols-[1.6fr_1fr]">
        <div class="glass glass--lg p-6">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <SectionLabel num="03">
              динамика · 30 дней
            </SectionLabel>
            <div class="flex items-center gap-4 text-[12.5px] text-[var(--text-3)]">
              <span class="flex items-center gap-1.5"><i class="legend legend--a" />начали</span>
              <span class="flex items-center gap-1.5"><i class="legend legend--b" />завершили</span>
            </div>
          </div>
          <div class="chart mt-6" @mouseleave="hoverDay = null">
            <div v-for="(d, i) in timeline" :key="d.day" class="chart__col" @mouseenter="hoverDay = i">
              <span class="chart__bar chart__bar--a" :style="{ height: `${(d.started / tMax) * 100}%` }" />
              <span class="chart__bar chart__bar--b" :style="{ height: `${(d.completed / tMax) * 100}%` }" />
              <div v-if="hoverDay === i" class="chart__tip" :class="i > timeline.length - 6 && 'chart__tip--left'">
                <div class="font-semibold">
                  {{ dayLabel(d.day) }}
                </div>
                <div><i class="legend legend--a" /> начали: <b class="mono">{{ d.started }}</b></div>
                <div><i class="legend legend--b" /> завершили: <b class="mono">{{ d.completed }}</b></div>
              </div>
            </div>
          </div>
          <div class="mt-2 flex justify-between mono text-[11px] text-[var(--text-4)]">
            <span>{{ timeline[0] && dayLabel(timeline[0].day) }}</span>
            <span>сегодня</span>
          </div>
        </div>

        <div class="glass glass--lg p-6">
          <SectionLabel num="04">
            версии
          </SectionLabel>
          <div class="mt-5 space-y-4">
            <div v-for="v in [...a.versions].reverse()" :key="v.id">
              <div class="flex items-center justify-between gap-3 text-[14px]">
                <span class="flex items-center gap-2 min-w-0">
                  <span class="tag shrink-0" :class="v.id === a.version.id && 'tag--lit'">v{{ v.number }}</span>
                  <span class="truncate text-[var(--text-2)]">{{ v.changelog || 'без описания' }}</span>
                </span>
                <span class="mono shrink-0">{{ percent(v.completion_rate) }}</span>
              </div>
              <div class="bar mt-2">
                <span class="bar__fill" :style="{ width: `${v.completion_rate * 100}%` }" />
              </div>
              <div class="mt-1 mono text-[11.5px] text-[var(--text-4)]">
                {{ pl(v.runs, 'прохождение', 'прохождения', 'прохождений') }} · {{ formatDate(v.published_at) }}
              </div>
            </div>
          </div>
          <p v-if="a.versions.length > 1" class="mt-5 text-[13px] text-[var(--text-3)]">
            Доходимость v{{ a.versions.at(-1)!.number }} vs v{{ a.versions.at(-2)!.number }}:
            <b :class="a.versions.at(-1)!.completion_rate >= a.versions.at(-2)!.completion_rate ? 'text-[var(--ok)]' : 'text-[var(--crit)]'">
              {{ a.versions.at(-1)!.completion_rate >= a.versions.at(-2)!.completion_rate ? '+' : '' }}{{ Math.round((a.versions.at(-1)!.completion_rate - a.versions.at(-2)!.completion_rate) * 100) }} п.п.
            </b>
          </p>
        </div>
      </section>
    </template>

    <div v-else class="space-y-4">
      <div class="skel h-16 w-1/2" /><div class="skel h-24" /><div class="skel h-80" />
    </div>

    <Dialog :open="!!showDiff" @update:open="v => !v && (showDiff = null)">
      <DialogContent class="sm:max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Новая редакция: {{ showDiff?.proposed_title }}</DialogTitle>
          <DialogDescription>{{ showDiff?.recommendation }}</DialogDescription>
        </DialogHeader>
        <template v-if="showDiff">
          <TextDiff :before="currentStep(showDiff.step_key)?.body ?? ''" :after="showDiff.proposed_body" mode="preview" />
          <div v-if="showDiff.proposed_checklist.length" class="flex flex-wrap gap-1.5">
            <span v-for="c in showDiff.proposed_checklist" :key="c" class="tag tag--ok">☐ {{ c }}</span>
          </div>
          <div class="flex justify-end gap-2">
            <button class="btn-glass btn-glass--sm" @click="showDiff = null">
              Закрыть
            </button>
            <button class="btn-chrome btn-chrome--sm" :disabled="applied.has(showDiff.step_key)" @click="applyInsight(showDiff)">
              <Check class="size-4" /> Применить в черновик
            </button>
          </div>
        </template>
      </DialogContent>
    </Dialog>
  </div>
</template>

<style scoped>
.problem {
  padding: 22px;
}

.problem--critical::before {
  background: linear-gradient(135deg, color-mix(in srgb, var(--crit) 70%, transparent), rgba(255, 255, 255, .05) 45%, color-mix(in srgb, var(--crit) 35%, transparent));
}

.problem--warn::before {
  background: linear-gradient(135deg, color-mix(in srgb, var(--warn) 60%, transparent), rgba(255, 255, 255, .05) 45%, color-mix(in srgb, var(--warn) 30%, transparent));
}

.insight {
  margin-top: 18px;
  padding: 16px;
  border-radius: 18px;
  background: var(--ice-wash);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--ice) 25%, transparent);
}

.funnel {
  border-collapse: separate;
  border-spacing: 0;
}

.funnel th {
  padding: 10px 12px;
  text-align: left;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: var(--text-4);
}

.funnel td:not(:first-child) {
  white-space: nowrap;
}

.funnel td {
  padding: 12px;
  vertical-align: middle;
  border-top: 1px solid var(--line);
}

.funnel tr.row--critical td {
  background: var(--crit-wash);
}

.funnel tr.row--warn td {
  background: var(--warn-wash);
}

.funnel tr td:first-child {
  border-radius: 14px 0 0 14px;
}

.funnel tr td:last-child {
  border-radius: 0 14px 14px 0;
}

.bar {
  height: 6px;
  border-radius: 6px;
  background: var(--line);
  overflow: hidden;
}

.bar__fill {
  display: block;
  height: 100%;
  border-radius: 6px;
  background: linear-gradient(90deg, rgba(255, 255, 255, .3), #fff);
  transition: width .6s var(--ease);
}

:root:not(.dark) .bar__fill {
  background: linear-gradient(90deg, rgba(20, 25, 35, .3), #1a1d22);
}

.delta {
  margin-left: 6px;
  font-size: 11.5px;
}

.delta--good {
  color: var(--ok);
}

.delta--bad {
  color: var(--crit);
}

.score {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-family: var(--font-mono);
  font-size: 12.5px;
  font-weight: 600;
}

.score--ok {
  color: var(--text-3);
  background: var(--wash);
}

.score--warn {
  color: var(--warn);
  background: var(--warn-wash);
}

.score--critical {
  color: var(--crit);
  background: var(--crit-wash);
}

.dark .chart,
.dark .legend {
  --series-a: #3987e5;
  --series-b: #199e70;
}

.chart,
.legend {
  --series-a: #2a78d6;
  --series-b: #1baf7a;
}

.legend {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 3px;
}

.legend--a {
  background: var(--series-a);
}

.legend--b {
  background: var(--series-b);
}

.chart {
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 200px;
  padding-bottom: 1px;
  border-bottom: 1px solid var(--line-2);
}

.chart__col {
  position: relative;
  flex: 1;
  height: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 2px;
  cursor: default;
}

.chart__col:hover {
  background: var(--wash);
  border-radius: 6px 6px 0 0;
}

.chart__bar {
  width: 40%;
  max-width: 9px;
  min-height: 2px;
  border-radius: 4px 4px 0 0;
}

.chart__bar--a {
  background: var(--series-a);
}

.chart__bar--b {
  background: var(--series-b);
}

.chart__tip {
  position: absolute;
  z-index: 5;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-20%);
  min-width: 150px;
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 12.5px;
  line-height: 1.6;
  white-space: nowrap;
  color: var(--popover-foreground);
  background: var(--popover);
  box-shadow: var(--glass-hi), var(--glass-shadow-sm), inset 0 0 0 1px var(--line-2);
  pointer-events: none;
}

.chart__tip--left {
  transform: translateX(-85%);
}
</style>
