<script setup lang="ts">
import { BadgeCheck, Clock, GitFork, ListChecks, Users } from '@lucide/vue'
import type { GuideCard } from '~/types/api'

const props = withDefaults(defineProps<{ guide: GuideCard, index?: number, compact?: boolean, to?: string }>(), {
  index: 0,
  compact: false,
  to: undefined,
})
const { data: categories } = useCategories()
const link = computed(() => props.to ?? `/guides/${props.guide.slug}`)
</script>

<template>
  <NuxtLink :to="link" class="card panel panel--hover" :class="compact && 'card--compact'">
    <div class="flex items-center gap-2.5">
      <GuideCover :cover="guide.cover" :category="guide.category" :size="32" />
      <span class="text-[13px] text-[var(--text-3)] truncate">{{ categoryTitle(categories, guide.category) }}</span>
      <span class="flex-1" />
      <span v-if="guide.verified" class="tag tag--ok" title="Проверено экспертом">
        <BadgeCheck class="size-3.5" /> эксперт
      </span>
      <span v-if="guide.forked_from" class="tag" :title="`Форк: ${guide.forked_from.title}`">
        <GitFork class="size-3.5" /> форк
      </span>
    </div>

    <h3 class="card__title">
      {{ guide.title }}
    </h3>
    <p v-if="!compact" class="card__summary">
      {{ guide.summary }}
    </p>
    <p v-if="guide.snippet" class="card__snippet">
      <template v-for="(part, i) in snippetParts(guide.snippet)" :key="i">
        <mark v-if="part.hit">{{ part.text }}</mark><span v-else>{{ part.text }}</span>
      </template>
    </p>

    <div class="card__meta tabular-nums">
      <span><ListChecks class="size-3.5" />{{ guide.steps_count }} {{ plural(guide.steps_count, 'шаг', 'шага', 'шагов') }}</span>
      <span><Clock class="size-3.5" />{{ formatMinutes(guide.est_minutes) }}</span>
      <span :title="DIFFICULTY[guide.difficulty]">{{ DIFFICULTY[guide.difficulty] }}</span>
    </div>

    <div class="card__foot">
      <span class="flex items-center gap-2 min-w-0">
        <UserAvatar :id="guide.author.id" :name="guide.author.name" :size="22" />
        <span class="truncate text-[13px] text-[var(--text-3)]">{{ guide.author.name }}</span>
      </span>
      <span class="flex items-center gap-3 shrink-0">
        <span v-if="guide.runs_count" class="card__stat tabular-nums" title="Прошли до конца">
          <Users class="size-3.5" />{{ percent(guide.completion_rate) }}
        </span>
        <span class="card__score tabular-nums" title="Индекс полезности: оценки, доля дошедших до конца и «полезно»">
          {{ guide.usefulness }}
        </span>
      </span>
    </div>
  </NuxtLink>
</template>

<style scoped>
.card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 236px;
  padding: 18px;
}

.card--compact {
  min-height: 190px;
}

.card:hover .card__title {
  color: var(--primary);
}

.card__title {
  transition: color .15s;
  margin-top: 4px;
  font-size: 17px;
  font-weight: 650;
  line-height: 1.3;
  letter-spacing: -.015em;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card__summary {
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-3);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card__snippet {
  font-size: 13px;
  line-height: 1.45;
  color: var(--text-3);
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--wash);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card__snippet mark {
  color: var(--foreground);
  background: var(--ice-wash);
  border-radius: 3px;
}

.card__meta {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: auto;
  padding-top: 4px;
  font-size: 12.5px;
  color: var(--text-3);
}

.card__meta > span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.card__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}

.card__stat {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12.5px;
  color: var(--text-3);
}

.card__score {
  display: inline-grid;
  place-items: center;
  min-width: 30px;
  height: 22px;
  padding: 0 7px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--ice);
  background: var(--ice-wash);
}
</style>
