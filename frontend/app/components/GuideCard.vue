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
  <NuxtLink :to="link" class="card glass glass--hover rise group" :class="compact && 'card--compact'" :style="{ '--i': index }">
    <img class="card__cover" :src="`/glass/${guide.cover}.webp`" alt="" loading="lazy" decoding="async">

    <div class="flex items-center gap-2 relative z-[1]">
      <span class="tag">
        <CategoryIcon :slug="guide.category" class="size-3.5" />
        {{ categoryTitle(categories, guide.category) }}
      </span>
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

    <div class="card__meta mono">
      <span><ListChecks class="size-3.5" />{{ guide.steps_count }} {{ plural(guide.steps_count, 'шаг', 'шага', 'шагов') }}</span>
      <span><Clock class="size-3.5" />{{ formatMinutes(guide.est_minutes) }}</span>
      <span class="card__diff" :title="DIFFICULTY[guide.difficulty]">
        <i v-for="d in 3" :key="d" :class="d <= guide.difficulty && 'on'" />
      </span>
    </div>

    <div class="card__foot">
      <span class="flex items-center gap-2 min-w-0">
        <UserAvatar :id="guide.author.id" :name="guide.author.name" :size="26" />
        <span class="truncate text-[13px] text-[var(--text-3)]">{{ guide.author.name }}</span>
      </span>
      <span class="flex items-center gap-3 shrink-0">
        <span v-if="guide.runs_count" class="card__stat mono" title="Прошли до конца">
          <Users class="size-3.5" />{{ percent(guide.completion_rate) }}
        </span>
        <span class="card__score mono" title="Индекс полезности: оценки, доля дошедших до конца и «полезно»">
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
  min-height: 262px;
  padding: 20px 20px 18px;
  overflow: hidden;
  border-radius: 26px;
}

.card--compact {
  min-height: 210px;
}

.card__cover {
  position: absolute;
  z-index: -1;
  width: 150px;
  top: -34px;
  right: -40px;
  opacity: .5;
  transform: rotate(-8deg);
  transition: transform .8s var(--ease), opacity .6s var(--ease);
  filter: drop-shadow(0 18px 30px rgba(0, 0, 0, .45));
  pointer-events: none;
}

:root:not(.dark) .card__cover {
  opacity: .32;
}

.card:hover .card__cover {
  transform: rotate(6deg) scale(1.08) translate(-6px, 6px);
  opacity: .8;
}

.card__title {
  position: relative;
  margin-top: 8px;
  font-size: 19px;
  font-weight: 700;
  line-height: 1.22;
  letter-spacing: -.02em;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card__summary {
  font-size: 14px;
  line-height: 1.45;
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
  border-radius: 12px;
  background: var(--wash);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card__snippet mark {
  color: var(--foreground);
  background: var(--ice-wash);
  box-shadow: 0 0 0 2px var(--ice-wash);
  border-radius: 4px;
}

.card__meta {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: auto;
  padding-top: 6px;
  font-size: 12px;
  color: var(--text-3);
}

.card__meta > span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.card__diff {
  gap: 3px !important;
}

.card__diff i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--line-2);
}

.card__diff i.on {
  background: var(--pearl);
  box-shadow: var(--pearl-glow);
}

.card__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding-top: 12px;
  box-shadow: inset 0 1px 0 var(--line);
}

.card__stat {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--text-3);
}

.card__score {
  display: inline-grid;
  place-items: center;
  min-width: 34px;
  height: 26px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--on-chrome);
  background: var(--chrome);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .8), 0 0 14px rgba(200, 215, 255, .14);
}
</style>
