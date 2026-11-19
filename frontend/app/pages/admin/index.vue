<script setup lang="ts">
import { Activity, BadgeCheck, Bot, BookOpen, Coins, Search, ShieldAlert, UserCheck, Users, X } from '@lucide/vue'
import { toast } from 'vue-sonner'
import type { AdminStats, AdminUser } from '~/types/api'

definePageMeta({ middleware: 'auth' })
useHead({ title: 'Админка' })

const auth = useAuth()
const { data: categories } = useCategories()

const { data: stats, refresh: refreshStats } = useFetch<AdminStats>('/api/admin/stats', { key: 'admin-stats', server: false, immediate: auth.isAdmin })
const { data: pending, refresh: refreshPending } = useFetch<AdminUser[]>('/api/admin/users', {
  key: 'admin-pending',
  query: { pending: true },
  server: false,
  immediate: auth.isAdmin,
  default: () => [],
})

const q = ref('')
const debounced = ref('')
let timer: ReturnType<typeof setTimeout> | undefined
watch(q, (v) => {
  clearTimeout(timer)
  timer = setTimeout(() => (debounced.value = v.trim()), 250)
})
const { data: users, status: usersStatus, refresh: refreshUsers } = useFetch<AdminUser[]>('/api/admin/users', {
  key: 'admin-users',
  query: computed(() => (debounced.value ? { q: debounced.value } : {})),
  server: false,
  immediate: auth.isAdmin,
  default: () => [],
})

const tiles = computed(() => stats.value
  ? [
      { v: formatNumber(stats.value.users), l: 'пользователей', icon: Users },
      { v: formatNumber(stats.value.guides), l: 'инструкций', icon: BookOpen },
      { v: formatNumber(stats.value.runs), l: 'прохождений', icon: Activity },
      { v: formatNumber(stats.value.events), l: 'событий аналитики', icon: Activity },
      { v: formatNumber(stats.value.ai_calls_24h), l: 'вызовов ИИ за сутки', icon: Bot },
      { v: `$${stats.value.ai_cost_24h.toFixed(4)}`, l: 'расход ИИ за сутки', icon: Coins },
      { v: `$${stats.value.ai_cost_total.toFixed(4)}`, l: 'расход ИИ всего', icon: Coins },
      { v: formatNumber(stats.value.pending_expert_requests), l: 'заявок в эксперты', icon: UserCheck },
    ]
  : [])

const busy = ref<number | null>(null)
async function patchUser(u: AdminUser, role: string, cats?: string[]) {
  busy.value = u.id
  try {
    const updated = await api<AdminUser>(`/api/admin/users/${u.id}`, {
      method: 'PATCH',
      body: { role, expert_categories: cats ?? u.expert_categories },
    })
    Object.assign(u, updated)
    toast.success(`${u.name}: ${ROLE_LABEL[role]?.toLowerCase()}`)
    return updated
  }
  finally {
    busy.value = null
  }
}

async function approve(u: AdminUser) {
  await patchUser(u, 'expert', u.expert_request_categories)
  await Promise.all([refreshPending(), refreshStats(), refreshUsers()])
}

async function reject(u: AdminUser) {
  busy.value = u.id
  try {
    await api(`/api/admin/users/${u.id}/reject-expert`, { method: 'POST' })
    toast('Заявка отклонена')
    await Promise.all([refreshPending(), refreshStats()])
  }
  finally {
    busy.value = null
  }
}

async function changeRole(u: AdminUser, role: unknown) {
  if (typeof role !== 'string' || role === u.role) return
  await patchUser(u, role)
  refreshStats()
}
</script>

<template>
  <div class="mx-auto max-w-[1180px] px-5 pt-12">
    <div v-if="!auth.isAdmin" class="glass glass--lg mx-auto mt-10 max-w-xl p-10 text-center rise">
      <span class="ico mx-auto size-14"><ShieldAlert class="size-6" /></span>
      <h1 class="mt-5 text-[28px] font-extrabold silver">
        Только для администраторов
      </h1>
      <p class="mt-3 text-[var(--text-3)]">
        Здесь управляют ролями, заявками в эксперты и следят за расходом ИИ.
      </p>
      <NuxtLink to="/" class="btn-chrome mt-6">
        На главную
      </NuxtLink>
    </div>

    <template v-else>
      <div class="scrim">
        <SectionLabel code>
          админка
        </SectionLabel>
        <h1 class="mt-4 text-[38px] md:text-[56px] font-extrabold leading-[1.02] tracking-[-0.035em] silver" style="--lh: 1.02em">
          Пульт платформы
        </h1>
      </div>

      <div class="mt-8 grid grid-cols-2 md:grid-cols-4 gap-3">
        <template v-if="!stats">
          <div v-for="i in 8" :key="i" class="skel h-[128px] !rounded-[24px]" />
        </template>
        <div v-for="(t, i) in tiles" :key="t.l" class="tile glass rise" :style="{ '--i': i }">
          <span class="ico size-9"><component :is="t.icon" class="size-4" /></span>
          <span class="display silver text-[28px] md:text-[32px] leading-none mt-4">{{ t.v }}</span>
          <span class="mt-2 text-[12.5px] text-[var(--text-3)]">{{ t.l }}</span>
        </div>
      </div>

      <section class="mt-14">
        <SectionLabel num="01">
          заявки в эксперты
        </SectionLabel>
        <div v-if="pending?.length" class="mt-5 grid gap-3 md:grid-cols-2">
          <article v-for="u in pending" :key="u.id" class="glass p-5">
            <div class="flex items-center gap-3">
              <UserAvatar :id="u.id" :name="u.name" :size="40" />
              <div class="min-w-0">
                <NuxtLink :to="`/u/${u.id}`" class="font-semibold hover:underline underline-offset-4">
                  {{ u.name }}
                </NuxtLink>
                <div class="text-[12.5px] text-[var(--text-4)] truncate">
                  {{ u.email }}
                </div>
              </div>
            </div>
            <div class="mt-4 flex flex-wrap gap-1.5">
              <span v-for="c in u.expert_request_categories" :key="c" class="tag tag--ice">
                <CategoryIcon :slug="c" class="size-3.5" />{{ categoryTitle(categories, c) }}
              </span>
            </div>
            <p class="mt-3 text-[14.5px] leading-relaxed text-[var(--text-2)] whitespace-pre-line">
              {{ u.expert_request_text }}
            </p>
            <div class="mt-4 flex gap-2 justify-end">
              <button class="btn-glass btn-glass--sm" :disabled="busy === u.id" @click="reject(u)">
                <X class="size-4" /> Отклонить
              </button>
              <button class="btn-chrome btn-chrome--sm" :disabled="busy === u.id" @click="approve(u)">
                <BadgeCheck class="size-4" /> Назначить экспертом
              </button>
            </div>
          </article>
        </div>
        <p v-else class="mt-4 text-[14px] text-[var(--text-3)]">
          Новых заявок нет.
        </p>
      </section>

      <section class="mt-14">
        <div class="flex flex-wrap items-end justify-between gap-4">
          <SectionLabel num="02">
            пользователи
          </SectionLabel>
          <div class="relative w-full sm:w-80">
            <Search class="absolute left-4 top-1/2 -translate-y-1/2 size-4 text-[var(--text-3)] z-[3] pointer-events-none" />
            <input v-model="q" type="search" class="field !h-11 !pl-11 !rounded-full !text-[14.5px]" placeholder="Имя или email">
          </div>
        </div>
        <div class="mt-5 glass overflow-hidden">
          <div class="users-head">
            <span>пользователь</span><span class="users-col--hide">инструкций</span><span class="users-col--hide">с нами</span><span>роль</span>
          </div>
          <div class="max-h-[620px] overflow-y-auto">
          <template v-if="usersStatus === 'pending' && !users?.length">
            <div v-for="i in 6" :key="i" class="px-5 py-3">
              <div class="skel h-10" />
            </div>
          </template>
          <div v-for="u in users" :key="u.id" class="users-row">
            <span class="flex items-center gap-3 min-w-0">
              <UserAvatar :id="u.id" :name="u.name" :size="32" />
              <span class="min-w-0">
                <NuxtLink :to="`/u/${u.id}`" class="block font-medium truncate hover:underline underline-offset-4">{{ u.name }}</NuxtLink>
                <span class="block text-[12px] text-[var(--text-4)] truncate">{{ u.email }}</span>
              </span>
            </span>
            <span class="mono text-[13px] text-[var(--text-3)] users-col--hide">{{ u.guides_count }}</span>
            <span class="text-[13px] text-[var(--text-3)] users-col--hide">{{ formatDate(u.created_at) }}</span>
            <span>
              <Select :model-value="u.role" :disabled="busy === u.id || u.id === auth.user?.id" @update:model-value="v => changeRole(u, v)">
                <SelectTrigger class="h-9 rounded-full px-3 w-full bg-[var(--wash)] text-[13px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent class="rounded-2xl">
                  <SelectItem value="learner">Ученик</SelectItem>
                  <SelectItem value="expert">Эксперт</SelectItem>
                  <SelectItem value="admin">Админ</SelectItem>
                </SelectContent>
              </Select>
            </span>
          </div>
          <p v-if="usersStatus !== 'pending' && !users?.length" class="p-6 text-center text-[var(--text-3)]">
            Никого не нашли.
          </p>
          </div>
        </div>
        <p class="mt-3 text-[12.5px] text-[var(--text-4)]">
          Показаны последние 200 пользователей — используйте поиск, чтобы найти нужного.
        </p>
      </section>
    </template>
  </div>
</template>

<style scoped>
.tile {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 18px;
}

.users-head,
.users-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 140px;
  align-items: center;
  gap: 16px;
  padding: 12px 20px;
}

@media (min-width: 768px) {
  .users-head,
  .users-row {
    grid-template-columns: minmax(0, 1fr) 110px 130px 160px;
  }
}

.users-col--hide {
  display: none;
}

@media (min-width: 768px) {
  .users-col--hide {
    display: block;
  }
}

.users-head {
  font-family: var(--font-mono);
  font-size: 11.5px;
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--text-4);
  box-shadow: inset 0 -1px 0 var(--line);
}

.users-row + .users-row {
  box-shadow: inset 0 1px 0 var(--line);
}
</style>
