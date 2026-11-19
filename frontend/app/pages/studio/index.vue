<script setup lang="ts">
import { AlertTriangle, ArrowRight, ChartNoAxesColumn, Eye, GitPullRequestArrow, PenLine, Plus, Sparkles } from '@lucide/vue'
import type { StudioGuideItem } from '~/types/api'

definePageMeta({ middleware: 'auth' })
useHead({ title: 'Студия автора' })

const { data: guides, status } = useFetch<StudioGuideItem[]>('/api/studio/guides', { default: () => [] })

const totals = computed(() => {
  const list = guides.value ?? []
  const runs = list.reduce((a, g) => a + g.runs_count, 0)
  const done = list.reduce((a, g) => a + g.completions_count, 0)
  return {
    runs,
    rate: runs ? done / runs : 0,
    suggestions: list.reduce((a, g) => a + g.open_suggestions, 0),
    hot: list.filter(g => g.hot_step?.level === 'critical').length,
  }
})

function statusTag(g: StudioGuideItem) {
  if (g.status === 'draft') return { cls: 'tag--warn', text: 'черновик' }
  if (g.has_unpublished_changes) return { cls: 'tag--ice', text: 'есть неопубликованные правки' }
  return { cls: 'tag--ok', text: 'опубликовано' }
}
</script>

<template>
  <div class="mx-auto max-w-[1180px] px-5 pt-12">
    <div class="flex flex-wrap items-end justify-between gap-6">
      <div class="scrim">
        <SectionLabel code>
          студия автора
        </SectionLabel>
        <h1 class="mt-4 text-[40px] md:text-[60px] font-extrabold leading-[1.02] silver" style="--lh: 1.02em">
          Ваши инструкции
        </h1>
        <p class="mt-3 text-[var(--text-3)] max-w-[560px]">
          Пишите, публикуйте версии и смотрите, на каком шаге ученики спотыкаются.
        </p>
      </div>
      <div class="flex flex-wrap gap-3">
        <NuxtLink to="/studio/inbox" class="btn-glass">
          <GitPullRequestArrow class="size-4" /> Правки
          <span v-if="totals.suggestions" class="badge">{{ totals.suggestions }}</span>
        </NuxtLink>
        <NuxtLink to="/studio/new" class="btn-chrome">
          <Plus class="size-4" /> Новая инструкция
        </NuxtLink>
      </div>
    </div>

    <div v-if="guides?.length" class="mt-10 grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="glass p-5 rise">
        <div class="label">
          прохождений
        </div>
        <div class="mt-2 display silver text-[40px] leading-none">
          {{ formatNumber(totals.runs) }}
        </div>
      </div>
      <div class="glass p-5 rise" style="--i: 1">
        <div class="label">
          доходят до конца
        </div>
        <div class="mt-2 display silver text-[40px] leading-none">
          {{ percent(totals.rate) }}
        </div>
      </div>
      <div class="glass p-5 rise" style="--i: 2">
        <div class="label">
          открытых правок
        </div>
        <div class="mt-2 display silver text-[40px] leading-none">
          {{ totals.suggestions }}
        </div>
      </div>
      <div class="glass p-5 rise" :class="{ 'glass--lit': totals.hot > 0 }" style="--i: 3">
        <div class="label">
          критичных узких мест
        </div>
        <div class="mt-2 display text-[40px] leading-none" :class="totals.hot ? 'text-[var(--crit)]' : 'silver'">
          {{ totals.hot }}
        </div>
      </div>
    </div>

    <div class="mt-8 space-y-3">
      <template v-if="status === 'pending'">
        <div v-for="i in 3" :key="i" class="skel h-[132px] !rounded-[24px]" />
      </template>

      <article v-for="(g, i) in guides" :key="g.id" class="row glass rise" :style="{ '--i': i }">
        <img :src="`/glass/${g.cover}.webp`" alt="" class="row__cover">
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <span class="tag" :class="statusTag(g).cls">{{ statusTag(g).text }}</span>
            <span class="tag"><CategoryIcon :slug="g.category" class="size-3.5" />{{ g.steps_count || '—' }} шагов</span>
            <span v-if="g.verified" class="tag tag--ok">эксперт ✓</span>
            <span v-if="g.forked_from" class="tag">форк «{{ g.forked_from.title }}»</span>
          </div>
          <NuxtLink :to="`/studio/${g.id}`" class="block mt-2 text-[19px] font-bold leading-snug hover:underline underline-offset-4">
            {{ g.title || 'Без названия' }}
          </NuxtLink>
          <div class="mt-2 flex flex-wrap gap-x-5 gap-y-1 mono text-[12.5px] text-[var(--text-3)]">
            <span>{{ pl(g.runs_count, 'прохождение', 'прохождения', 'прохождений') }}</span>
            <span>до конца {{ percent(g.completion_rate) }}</span>
            <span>★ {{ g.rating?.toFixed(1) ?? '—' }}</span>
            <span>полезность {{ g.usefulness }}</span>
            <span>изменено {{ timeAgo(g.updated_at) }}</span>
          </div>
          <NuxtLink
            v-if="g.hot_step"
            :to="`/studio/${g.id}/analytics`"
            class="hot"
            :class="g.hot_step.level === 'critical' ? 'hot--crit' : 'hot--warn'"
          >
            <AlertTriangle class="size-4 shrink-0" />
            <span class="truncate">Узкое место: «{{ g.hot_step.title }}»</span>
            <span class="mono shrink-0">индекс {{ g.hot_step.score }}</span>
            <ArrowRight class="size-4 shrink-0" />
          </NuxtLink>
        </div>
        <div class="row__actions">
          <NuxtLink :to="`/studio/${g.id}`" class="btn-glass btn-glass--sm">
            <PenLine class="size-4" /> Редактор
          </NuxtLink>
          <NuxtLink v-if="g.status === 'published'" :to="`/studio/${g.id}/analytics`" class="btn-glass btn-glass--sm">
            <ChartNoAxesColumn class="size-4" /> Аналитика
          </NuxtLink>
          <NuxtLink v-if="g.status === 'published'" :to="`/guides/${g.slug}`" class="btn-glass btn-glass--sm" title="Открыть публичную страницу">
            <Eye class="size-4" />
          </NuxtLink>
        </div>
      </article>

      <div v-if="status !== 'pending' && !guides?.length" class="glass glass--lg p-10 text-center">
        <img src="/glass/blob.webp" alt="" class="w-40 mx-auto opacity-80">
        <h3 class="mt-4 text-2xl font-bold">
          Здесь появятся ваши инструкции
        </h3>
        <p class="mt-2 text-[var(--text-3)] max-w-md mx-auto">
          Знаете, как сделать что-то, на чём другие спотыкаются? Опишите задачу — ИИ набросает шаги, а вы доведёте их до ума.
        </p>
        <NuxtLink to="/studio/new" class="btn-chrome mt-6">
          <Sparkles class="size-4" /> Создать первую инструкцию
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.row {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 18px 20px;
  border-radius: 24px;
  overflow: hidden;
}

.row__cover {
  flex: none;
  width: 84px;
  height: 84px;
  object-fit: contain;
  filter: drop-shadow(0 12px 20px rgba(0, 0, 0, .4));
}

.row__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  flex: none;
}

@media (max-width: 760px) {
  .row {
    flex-wrap: wrap;
  }

  .row__cover {
    width: 56px;
    height: 56px;
  }

  .row__actions {
    width: 100%;
    justify-content: flex-start;
  }
}

.hot {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  max-width: 100%;
  margin-top: 12px;
  padding: 7px 12px;
  border-radius: 12px;
  font-size: 13px;
  transition: filter .2s;
}

.hot:hover {
  filter: brightness(1.15);
}

.hot--crit {
  color: var(--crit);
  background: var(--crit-wash);
}

.hot--warn {
  color: var(--warn);
  background: var(--warn-wash);
}

.badge {
  display: inline-grid;
  place-items: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--on-chrome);
  background: var(--chrome);
}
</style>
