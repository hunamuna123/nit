<script setup lang="ts">
import { ArrowRight, BadgeCheck, Bookmark, CheckCircle2, Clock, Compass, GitPullRequest, Hourglass, Play, Save, Sparkles } from '@lucide/vue'
import { toast } from 'vue-sonner'
import type { DashboardOut, UserMe } from '~/types/api'

definePageMeta({ middleware: 'auth' })
useHead({ title: 'Мои прохождения' })

const auth = useAuth()
const { data: categories } = useCategories()
const { data, status } = useFetch<DashboardOut>('/api/me/dashboard', { key: 'dashboard', server: false })

const name = ref(auth.user?.name ?? '')
const bio = ref(auth.user?.bio ?? '')
const saving = ref(false)
const profileDirty = computed(() => name.value.trim() !== (auth.user?.name ?? '') || bio.value.trim() !== (auth.user?.bio ?? ''))
async function saveProfile() {
  saving.value = true
  try {
    await api<UserMe>('/api/me', { method: 'PATCH', body: { name: name.value.trim(), bio: bio.value.trim() } })
    await auth.fetchMe()
    toast.success('Профиль обновлён')
  }
  finally {
    saving.value = false
  }
}

const expertCats = ref<string[]>([])
const expertText = ref('')
const sending = ref(false)
function toggleCat(slug: string) {
  expertCats.value = expertCats.value.includes(slug)
    ? expertCats.value.filter(c => c !== slug)
    : [...expertCats.value, slug].slice(0, 4)
}
async function sendExpertRequest() {
  sending.value = true
  try {
    await api<UserMe>('/api/me/expert-request', { method: 'POST', body: { categories: expertCats.value, text: expertText.value.trim() } })
    await auth.fetchMe()
    toast.success('Заявка отправлена', { description: 'Администратор рассмотрит её и назначит роль эксперта' })
  }
  finally {
    sending.value = false
  }
}

const canRequestExpert = computed(() => auth.user?.role === 'learner' && auth.user?.expert_request_status !== 'pending')
const STATUS: Record<string, { label: string, cls: string }> = {
  open: { label: 'на рассмотрении', cls: 'tag--ice' },
  accepted: { label: 'принята', cls: 'tag--ok' },
  rejected: { label: 'отклонена', cls: 'tag--crit' },
}
const counts = computed(() => ({
  active: data.value?.active.length ?? 0,
  completed: data.value?.completed.length ?? 0,
  bookmarks: data.value?.bookmarks.length ?? 0,
  suggestions: data.value?.suggestions.length ?? 0,
}))
</script>

<template>
  <div class="mx-auto max-w-[1180px] px-5 pt-12">
    <div class="flex flex-wrap items-end justify-between gap-6">
      <div class="scrim flex items-center gap-5">
        <UserAvatar v-if="auth.user" :id="auth.user.id" :name="auth.user.name" :size="72" />
        <div>
          <SectionLabel code>
            личный кабинет
          </SectionLabel>
          <h1 class="mt-3 text-[34px] md:text-[52px] font-extrabold leading-[1.02] tracking-[-0.035em] silver" style="--lh: 1.02em">
            {{ auth.user?.name }}
          </h1>
        </div>
      </div>
      <div class="flex flex-wrap gap-2">
        <NuxtLink v-if="auth.user" :to="`/u/${auth.user.id}`" class="btn-glass btn-glass--sm">
          Публичный профиль
        </NuxtLink>
        <NuxtLink to="/studio" class="btn-chrome btn-chrome--sm">
          <Sparkles class="size-4" /> Студия автора
        </NuxtLink>
      </div>
    </div>

    <div class="mt-8 grid grid-cols-2 md:grid-cols-4 gap-3">
      <div
v-for="(s, i) in [
        { v: counts.active, l: 'в процессе', icon: Hourglass },
        { v: counts.completed, l: 'пройдено', icon: CheckCircle2 },
        { v: counts.bookmarks, l: 'сохранено', icon: Bookmark },
        { v: counts.suggestions, l: 'правок предложено', icon: GitPullRequest },
      ]" :key="s.l" class="tile glass rise" :style="{ '--i': i }"
      >
        <span class="ico size-9"><component :is="s.icon" class="size-4" /></span>
        <span class="display silver text-[34px] leading-none mt-4">{{ s.v }}</span>
        <span class="label mt-2">{{ s.l }}</span>
      </div>
    </div>

    <div class="mt-10 grid gap-10 lg:grid-cols-[1fr_340px]">
      <div class="min-w-0 space-y-12">
        <section>
          <SectionLabel num="01">
            в процессе
          </SectionLabel>
          <div v-if="status === 'pending'" class="mt-5 grid gap-3 sm:grid-cols-2">
            <div v-for="i in 2" :key="i" class="skel h-[170px] !rounded-[24px]" />
          </div>
          <div v-else-if="data?.active.length" class="mt-5 grid gap-3 sm:grid-cols-2">
            <article v-for="(r, i) in data.active" :key="r.run.id" class="run glass glass--hover rise" :style="{ '--i': i }">
              <img :src="`/glass/${r.guide.cover}.webp`" alt="" class="run__blob">
              <div class="flex items-center gap-2 relative">
                <span class="tag"><CategoryIcon :slug="r.guide.category" class="size-3.5" />{{ categoryTitle(categories, r.guide.category) }}</span>
                <span class="text-[12px] text-[var(--text-4)]">{{ timeAgo(r.last_activity_at) }}</span>
              </div>
              <NuxtLink :to="`/guides/${r.guide.slug}`" class="mt-3 block font-bold text-[17px] leading-snug hover:underline underline-offset-4 relative">
                {{ r.guide.title }}
              </NuxtLink>
              <div class="mt-auto pt-5 relative">
                <div class="flex justify-between text-[12.5px] mb-2">
                  <span class="text-[var(--text-3)]">шаг {{ Math.min(r.run.current_step + 1, r.guide.steps_count) }} из {{ r.guide.steps_count }}</span>
                  <span class="mono">{{ percent(r.run.progress) }}</span>
                </div>
                <HairlineBar :value="r.run.progress" />
                <p v-if="r.run.outdated" class="mt-3 text-[12.5px] text-[var(--warn)]">
                  Автор выпустил новую версию — можно начать по ней заново.
                </p>
                <NuxtLink :to="`/guides/${r.guide.slug}/run`" class="btn-chrome btn-chrome--sm mt-4">
                  <Play class="size-4" /> Продолжить
                </NuxtLink>
              </div>
            </article>
          </div>
          <div v-else class="empty glass mt-5">
            <img src="/glass/drop.webp" alt="" class="w-20">
            <div>
              <div class="font-semibold">
                Сейчас ничего не проходите
              </div>
              <p class="text-[14px] text-[var(--text-3)] mt-1">
                Найдите задачу, которую давно откладываете, — и пройдите её шаг за шагом.
              </p>
              <NuxtLink to="/guides" class="btn-chrome btn-chrome--sm mt-4">
                <Compass class="size-4" /> В каталог
              </NuxtLink>
            </div>
          </div>
        </section>

        <section>
          <SectionLabel num="02">
            пройдено
          </SectionLabel>
          <div v-if="data?.completed.length" class="mt-5 glass overflow-hidden">
            <NuxtLink
              v-for="r in data.completed"
              :key="r.run.id"
              :to="`/guides/${r.guide.slug}`"
              class="done-row"
            >
              <span class="done-row__check"><CheckCircle2 class="size-4" /></span>
              <span class="flex-1 min-w-0">
                <span class="block font-semibold truncate">{{ r.guide.title }}</span>
                <span class="block mono text-[12px] text-[var(--text-4)]">
                  {{ pl(r.guide.steps_count, 'шаг', 'шага', 'шагов') }} · {{ formatMinutes(r.guide.est_minutes) }}
                </span>
              </span>
              <span class="text-[12.5px] text-[var(--text-3)] shrink-0">{{ formatDate(r.completed_at) }}</span>
              <ArrowRight class="size-4 text-[var(--text-4)] shrink-0" />
            </NuxtLink>
          </div>
          <p v-else-if="status !== 'pending'" class="mt-4 text-[14px] text-[var(--text-3)]">
            Пока ни одной пройденной инструкции. Первая галочка — самая приятная.
          </p>
        </section>

        <section>
          <SectionLabel num="03">
            сохранённые
          </SectionLabel>
          <div v-if="data?.bookmarks.length" class="mt-5 grid gap-4 sm:grid-cols-2">
            <GuideCard v-for="(g, i) in data.bookmarks" :key="g.id" :guide="g" :index="i" compact />
          </div>
          <p v-else-if="status !== 'pending'" class="mt-4 text-[14px] text-[var(--text-3)]">
            Нажмите «Сохранить» на странице инструкции, чтобы вернуться к ней позже.
          </p>
        </section>

        <section>
          <SectionLabel num="04">
            мои предложения правок
          </SectionLabel>
          <div v-if="data?.suggestions.length" class="mt-5 space-y-3">
            <article v-for="s in data.suggestions" :key="s.id" class="glass p-5">
              <div class="flex flex-wrap items-center gap-2">
                <span class="tag" :class="STATUS[s.status]?.cls">{{ STATUS[s.status]?.label ?? s.status }}</span>
                <span class="text-[12px] text-[var(--text-4)]">{{ timeAgo(s.created_at) }}</span>
              </div>
              <NuxtLink :to="`/guides/${s.guide_slug}`" class="mt-2 block font-semibold hover:underline underline-offset-4">
                {{ s.guide_title }}
              </NuxtLink>
              <p class="mt-1 text-[13.5px] text-[var(--text-3)]">
                Шаг: «{{ s.title ?? s.current_title ?? 'шаг' }}»<template v-if="s.message">
                  · {{ s.message }}
                </template>
              </p>
              <div v-if="s.reply" class="mt-3 p-3 rounded-2xl bg-[var(--wash)] text-[14px]">
                <span class="label mb-1 block">ответ автора</span>
                {{ s.reply }}
              </div>
            </article>
          </div>
          <p v-else-if="status !== 'pending'" class="mt-4 text-[14px] text-[var(--text-3)]">
            Видите, как сделать шаг понятнее? Во время прохождения нажмите «Предложить правку» — автор сможет влить её одной кнопкой.
          </p>
        </section>
      </div>

      <aside class="space-y-4 lg:sticky lg:top-[96px] self-start">
        <form class="glass p-5" @submit.prevent="saveProfile">
          <div class="label label--caps">
            <span class="pearl" />профиль
          </div>
          <label class="block mt-4">
            <span class="label mb-2 block">имя</span>
            <input v-model="name" class="field !h-11 !text-[14.5px]" maxlength="60" required minlength="2">
          </label>
          <label class="block mt-3">
            <span class="label mb-2 block">о себе</span>
            <textarea v-model="bio" class="field !min-h-[90px] !text-[14px]" maxlength="400" placeholder="Чем можете помочь другим? Например: «собрал 5 ПК, помогу с BIOS»" />
          </label>
          <button class="btn-chrome btn-chrome--sm w-full mt-3" :disabled="saving || !profileDirty">
            <Save class="size-4" /> Сохранить
          </button>
          <p class="mt-3 text-[12px] text-[var(--text-4)] truncate">
            {{ auth.user?.email }} · {{ ROLE_LABEL[auth.user?.role ?? 'learner'] }}
          </p>
        </form>

        <div v-if="auth.user?.role !== 'learner'" class="glass p-5">
          <div class="flex items-center gap-3">
            <span class="ico text-[var(--ok)]"><BadgeCheck class="size-5" /></span>
            <div>
              <div class="font-semibold">
                Вы {{ auth.user?.role === 'admin' ? 'администратор' : 'эксперт' }}
              </div>
              <div class="text-[13px] text-[var(--text-3)]">
                <template v-if="auth.user?.expert_categories.length">
                  {{ auth.user.expert_categories.map(c => categoryTitle(categories, c)).join(', ') }}
                </template>
                <template v-else>
                  все категории
                </template>
              </div>
            </div>
          </div>
          <NuxtLink to="/review" class="btn-glass btn-glass--sm w-full mt-4">
            Очередь проверки
          </NuxtLink>
        </div>

        <div v-else-if="auth.user?.expert_request_status === 'pending'" class="glass p-5">
          <div class="flex items-center gap-3">
            <span class="ico"><Clock class="size-5" /></span>
            <div>
              <div class="font-semibold">
                Заявка в эксперты отправлена
              </div>
              <div class="text-[13px] text-[var(--text-3)]">
                Администратор скоро её рассмотрит.
              </div>
            </div>
          </div>
        </div>

        <form v-else-if="canRequestExpert" class="glass p-5" @submit.prevent="sendExpertRequest">
          <div class="label label--caps">
            <span class="pearl" />стать экспертом
          </div>
          <p class="mt-3 text-[13.5px] text-[var(--text-3)] leading-snug">
            Эксперты проверяют инструкции в своих темах — проверенные получают бейдж и выше в каталоге.
          </p>
          <p v-if="auth.user?.expert_request_status === 'rejected'" class="mt-3 text-[12.5px] text-[var(--warn)]">
            Прошлая заявка отклонена — можно подать новую.
          </p>
          <div class="mt-4 flex flex-wrap gap-1.5">
            <button
              v-for="c in categories"
              :key="c.slug"
              type="button"
              class="chip !h-8 !px-3 !text-[13px]"
              :class="expertCats.includes(c.slug) && 'chip--on'"
              @click="toggleCat(c.slug)"
            >
              <CategoryIcon :slug="c.slug" class="size-3.5" />{{ c.title }}
            </button>
          </div>
          <textarea v-model="expertText" class="field mt-3 !min-h-[100px] !text-[14px]" minlength="10" maxlength="1000" placeholder="Расскажите о своём опыте в этих темах" />
          <button class="btn-chrome btn-chrome--sm w-full mt-3" :disabled="sending || !expertCats.length || expertText.trim().length < 10">
            Отправить заявку
          </button>
        </form>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.tile {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 18px;
}

.run {
  display: flex;
  flex-direction: column;
  min-height: 210px;
  padding: 20px;
  overflow: hidden;
}

.run__blob {
  position: absolute;
  z-index: -1;
  width: 130px;
  top: -30px;
  right: -36px;
  opacity: .45;
  pointer-events: none;
}

.empty {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 22px;
}

.done-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  transition: background .15s;
}

.done-row + .done-row {
  box-shadow: inset 0 1px 0 var(--line);
}

.done-row:hover {
  background: var(--wash);
}

.done-row__check {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  color: var(--on-chrome);
  background: var(--chrome);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .8);
  flex: none;
}
</style>
