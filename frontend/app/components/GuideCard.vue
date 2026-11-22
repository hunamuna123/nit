<script setup lang="ts">
import { BadgeCheck, GitFork } from '@lucide/vue'
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
  <NuxtLink :to="link" class="card panel panel--hover" :class="[compact && 'card--compact', `c-${guide.cover}`]">
    <div class="card__top">
      <span class="card__cat"><span class="dot" />{{ categoryTitle(categories, guide.category) }}</span>
      <span v-if="guide.verified" class="card__flag card__flag--ok" title="Проверено экспертом">
        <BadgeCheck class="size-3.5" />проверено
      </span>
      <span v-if="guide.forked_from" class="card__flag" :title="`Форк: ${guide.forked_from.title}`">
        <GitFork class="size-3.5" />форк
      </span>
    </div>

    <h3 class="card__title">
      <span>{{ guide.title }}</span>
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
      <span>{{ pl(guide.steps_count, 'шаг', 'шага', 'шагов') }}</span>
      <span>{{ formatMinutes(guide.est_minutes) }}</span>
      <span>{{ DIFFICULTY[guide.difficulty]?.toLowerCase() }}</span>
    </div>

    <div class="card__foot">
      <span class="flex items-center gap-2 min-w-0">
        <UserAvatar :id="guide.author.id" :name="guide.author.name" :size="22" />
        <span class="truncate text-[13px] text-[var(--text-3)]">{{ guide.author.name }}</span>
      </span>
      <span class="flex items-baseline gap-3 shrink-0">
        <span v-if="guide.runs_count" class="card__stat tabular-nums" title="Дошли до конца">
          {{ percent(guide.completion_rate) }} до конца
        </span>
        <span class="card__score" title="Индекс полезности: оценки, доля дошедших до конца и «полезно»">
          <span class="num">{{ guide.usefulness }}</span>
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
  min-height: 232px;
  padding: 20px 20px 16px;
}

.card--compact {
  min-height: 180px;
}

.card__top {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 20px;
}

.card__cat {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-width: 0;
  margin-right: auto;
  font-size: 13px;
  color: var(--text-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card__cat .dot {
  color: var(--c, var(--text-4));
}

.card__flag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-3);
  white-space: nowrap;
}

.card__flag--ok {
  color: var(--ok);
}

.card__title {
  margin-top: 2px;
  font-family: var(--font-serif);
  font-optical-sizing: auto;
  font-size: 19px;
  font-weight: 600;
  line-height: 1.28;
  letter-spacing: -.01em;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card__title > span {
  background-image: linear-gradient(var(--thread), var(--thread));
  background-size: 0 1.5px;
  background-position: 0 100%;
  background-repeat: no-repeat;
  transition: background-size .35s var(--ease);
}

.card:hover .card__title > span {
  background-size: 100% 1.5px;
}

.card__summary {
  font-size: 14px;
  line-height: 1.55;
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
  background: var(--thread-wash);
  border-radius: 3px;
}

.card__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 0;
  margin-top: auto;
  padding-top: 2px;
  font-size: 13px;
  color: var(--text-3);
}

.card__meta > span + span::before {
  content: '·';
  margin: 0 8px;
  color: var(--text-4);
}

.card__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px dashed var(--line-2);
}

.card__stat {
  font-size: 12.5px;
  color: var(--text-3);
}

.card__score {
  display: inline-flex;
  align-items: baseline;
  font-size: 18px;
  font-weight: 600;
  line-height: 1;
  color: var(--thread);
}
</style>
