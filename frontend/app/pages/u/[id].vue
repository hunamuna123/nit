<script setup lang="ts">
import { BadgeCheck, CalendarDays, CheckCircle2, GitPullRequest, MessageSquare, PenLine, Users } from '@lucide/vue'
import type { ProfileOut } from '~/types/api'

const route = useRoute()
const id = computed(() => String(route.params.id))
const { data: categories } = useCategories()

const { data: profile, error } = await useFetch<ProfileOut>(() => `/api/users/${id.value}`, { key: `user-${id.value}` })
if (error.value) throw createError({ statusCode: 404, statusMessage: 'Пользователь не найден', fatal: true })

useHead(() => ({ title: profile.value?.user.name ?? 'Профиль' }))

const p = computed(() => profile.value!)
const tiles = computed(() => [
  { v: p.value.stats.authored, l: 'Инструкций написано', icon: PenLine },
  { v: p.value.stats.learners_helped, l: 'Прошли до конца', icon: Users },
  { v: p.value.stats.completed, l: 'Инструкций пройдено', icon: CheckCircle2 },
  { v: p.value.stats.accepted_suggestions, l: 'Правок принято', icon: GitPullRequest },
  { v: p.value.stats.comments, l: 'Комментариев', icon: MessageSquare },
])
const since = computed(() => new Date(p.value.created_at).toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' }))
</script>

<template>
  <div v-if="profile" class="mx-auto max-w-[1200px] px-5 pt-10">
    <section class="hero">
      <div class="flex flex-col md:flex-row md:items-center gap-5">
        <UserAvatar :id="p.user.id" :name="p.user.name" :size="72" />
        <div class="min-w-0">
          <div class="flex flex-wrap items-center gap-2">
            <span class="tag" :class="p.user.role !== 'learner' && 'tag--ok'">
              <BadgeCheck v-if="p.user.role !== 'learner'" class="size-3.5" />{{ ROLE_LABEL[p.user.role] }}
            </span>
            <span v-for="c in p.user.expert_categories" :key="c" class="tag">
              <CategoryIcon :slug="c" class="size-3.5" />{{ categoryTitle(categories, c) }}
            </span>
            <span class="tag"><CalendarDays class="size-3.5" />с {{ since }}</span>
          </div>
          <h1 class="mt-3 page-title">
            {{ p.user.name }}
          </h1>
          <p v-if="p.bio" class="mt-2 max-w-[640px] text-[15.5px] leading-relaxed text-[var(--text-3)]">
            {{ p.bio }}
          </p>
        </div>
      </div>
    </section>

    <div class="mt-8 grid grid-cols-2 md:grid-cols-5 gap-3">
      <div v-for="t in tiles" :key="t.l" class="tile panel">
        <span class="label"><component :is="t.icon" class="size-4" />{{ t.l }}</span>
        <span class="num text-[28px] font-semibold leading-none mt-3">{{ formatNumber(t.v) }}</span>
      </div>
    </div>

    <section class="mt-12">
      <h2 class="section-title">
        Инструкции автора
      </h2>
      <div v-if="p.guides.length" class="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <GuideCard v-for="(g, i) in p.guides" :key="g.id" :guide="g" :index="i" />
      </div>
      <p v-else class="mt-4 text-[var(--text-3)]">
        {{ p.user.name }} пока не публиковал инструкций.
      </p>
    </section>
  </div>
</template>

<style scoped>
.tile {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 16px;
}

.tile .label {
  white-space: normal;
}
</style>
