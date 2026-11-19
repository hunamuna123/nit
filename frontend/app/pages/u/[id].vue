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
  { v: p.value.stats.authored, l: 'инструкций написано', icon: PenLine },
  { v: p.value.stats.learners_helped, l: 'учеников прошли до конца', icon: Users },
  { v: p.value.stats.completed, l: 'инструкций пройдено', icon: CheckCircle2 },
  { v: p.value.stats.accepted_suggestions, l: 'правок принято авторами', icon: GitPullRequest },
  { v: p.value.stats.comments, l: 'советов и комментариев', icon: MessageSquare },
])
const since = computed(() => new Date(p.value.created_at).toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' }))
</script>

<template>
  <div v-if="profile" class="mx-auto max-w-[1180px] px-5 pt-12">
    <section class="hero glass glass--lg rise">
      <img src="/glass/blob.webp" alt="" class="hero__blob">
      <div class="flex flex-col md:flex-row md:items-center gap-6">
        <UserAvatar :id="p.user.id" :name="p.user.name" :size="112" />
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
          <h1 class="mt-4 text-[36px] md:text-[56px] font-extrabold leading-[1.02] tracking-[-0.035em] silver" style="--lh: 1.02em">
            {{ p.user.name }}
          </h1>
          <p v-if="p.bio" class="mt-3 max-w-[640px] text-[16px] leading-relaxed text-[var(--text-2)]">
            {{ p.bio }}
          </p>
        </div>
      </div>
    </section>

    <div class="mt-4 grid grid-cols-2 md:grid-cols-5 gap-3">
      <div v-for="(t, i) in tiles" :key="t.l" class="tile glass rise" :style="{ '--i': i + 1 }">
        <span class="ico size-9"><component :is="t.icon" class="size-4" /></span>
        <span class="display silver text-[36px] leading-none mt-4">{{ formatNumber(t.v) }}</span>
        <span class="mt-2 text-[12.5px] text-[var(--text-3)] leading-snug">{{ t.l }}</span>
      </div>
    </div>

    <section class="mt-14">
      <SectionLabel num="01">
        инструкции автора
      </SectionLabel>
      <div v-if="p.guides.length" class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <GuideCard v-for="(g, i) in p.guides" :key="g.id" :guide="g" :index="i" />
      </div>
      <p v-else class="mt-4 text-[var(--text-3)]">
        {{ p.user.name }} пока не публиковал инструкций.
      </p>
    </section>
  </div>
</template>

<style scoped>
.hero {
  padding: 32px 26px;
  overflow: hidden;
}

@media (min-width: 768px) {
  .hero {
    padding: 44px 48px;
  }
}

.hero__blob {
  position: absolute;
  z-index: -1;
  width: 320px;
  right: -60px;
  top: -70px;
  opacity: .55;
  pointer-events: none;
}

.tile {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 18px;
}
</style>
