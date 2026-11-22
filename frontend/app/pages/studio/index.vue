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
  if (g.has_unpublished_changes) return { cls: 'tag--info', text: 'есть неопубликованные правки' }
  return { cls: 'tag--ok', text: 'опубликовано' }
}
</script>

<template>
  <div class="mx-auto max-w-[1200px] px-5 pt-10">
    <div class="flex flex-wrap items-end justify-between gap-6">
      <div>
        <h1 class="page-title">
          Ваши инструкции
        </h1>
        <p class="mt-2 text-[var(--text-3)] max-w-[560px]">
          Пишите, публикуйте версии и смотрите, на каком шаге люди застревают.
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <NuxtLink to="/studio/inbox" class="btn-secondary">
          <GitPullRequestArrow class="size-4" /> Правки
          <span v-if="totals.suggestions" class="badge">{{ totals.suggestions }}</span>
        </NuxtLink>
        <NuxtLink to="/studio/new" class="btn-primary">
          <Plus class="size-4" /> Новая инструкция
        </NuxtLink>
      </div>
    </div>

    <div v-if="guides?.length" class="mt-8 grid grid-cols-2 lg:grid-cols-4 gap-3">
      <div class="panel p-5">
        <div class="label">
          Прохождений
        </div>
        <div class="mt-2 text-[28px] font-semibold tabular-nums leading-none">
          {{ formatNumber(totals.runs) }}
        </div>
      </div>
      <div class="panel p-5">
        <div class="label">
          Доходят до конца
        </div>
        <div class="mt-2 text-[28px] font-semibold tabular-nums leading-none">
          {{ percent(totals.rate) }}
        </div>
      </div>
      <div class="panel p-5">
        <div class="label">
          Открытых правок
        </div>
        <div class="mt-2 text-[28px] font-semibold tabular-nums leading-none">
          {{ totals.suggestions }}
        </div>
      </div>
      <div class="panel p-5">
        <div class="label">
          Критичных узких мест
        </div>
        <div class="mt-2 text-[28px] font-semibold tabular-nums leading-none" :class="totals.hot ? 'text-[var(--crit)]' : ''">
          {{ totals.hot }}
        </div>
      </div>
    </div>

    <div class="mt-8 space-y-3">
      <template v-if="status === 'pending'">
        <div v-for="i in 3" :key="i" class="skel h-[132px]" />
      </template>

      <article v-for="g in guides" :key="g.id" class="row panel">
        <GuideCover :cover="g.cover" :category="g.category" :size="44" class="row__cover" />
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <span class="tag" :class="statusTag(g).cls">{{ statusTag(g).text }}</span>
            <span class="tag">{{ g.steps_count || '—' }} шагов</span>
            <span v-if="g.verified" class="tag tag--ok">эксперт</span>
            <span v-if="g.forked_from" class="tag">форк «{{ g.forked_from.title }}»</span>
          </div>
          <NuxtLink :to="`/studio/${g.id}`" class="block mt-2 text-[16.5px] font-semibold leading-snug hover:underline underline-offset-4">
            {{ g.title || 'Без названия' }}
          </NuxtLink>
          <div class="mt-2 flex flex-wrap gap-x-5 gap-y-1 tabular-nums text-[12.5px] text-[var(--text-3)]">
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
            <span class="tabular-nums shrink-0">индекс {{ g.hot_step.score }}</span>
            <ArrowRight class="size-4 shrink-0" />
          </NuxtLink>
        </div>
        <div class="row__actions">
          <NuxtLink :to="`/studio/${g.id}`" class="btn-secondary btn-sm">
            <PenLine class="size-4" /> Редактор
          </NuxtLink>
          <NuxtLink v-if="g.status === 'published'" :to="`/studio/${g.id}/analytics`" class="btn-secondary btn-sm">
            <ChartNoAxesColumn class="size-4" /> Аналитика
          </NuxtLink>
          <NuxtLink v-if="g.status === 'published'" :to="`/guides/${g.slug}`" class="btn-secondary btn-sm" title="Открыть публичную страницу">
            <Eye class="size-4" />
          </NuxtLink>
        </div>
      </article>

      <div v-if="status !== 'pending' && !guides?.length" class="panel p-10 text-center">
        <h3 class="text-lg font-semibold">
          Здесь появятся ваши инструкции
        </h3>
        <p class="mt-2 text-[var(--text-3)] max-w-md mx-auto">
          Опишите задачу, и ИИ набросает шаги. Останется проверить их и опубликовать.
        </p>
        <NuxtLink to="/studio/new" class="btn-primary mt-6">
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
  gap: 16px;
  padding: 16px 18px;
}

.row__cover {
  align-self: flex-start;
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
  padding: 6px 10px;
  border-radius: 8px;
  font-size: 13px;
}

.hot:hover {
  text-decoration: underline;
  text-underline-offset: 3px;
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
  font-size: 11px;
  font-weight: 600;
  color: var(--primary-foreground);
  background: var(--primary);
}
</style>
