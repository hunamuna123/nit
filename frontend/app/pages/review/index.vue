<script setup lang="ts">
import { BadgeCheck, ClipboardCheck, Clock, ListChecks, MessageSquareWarning, ShieldAlert, Users } from '@lucide/vue'
import { toast } from 'vue-sonner'
import type { GuideDetail, ReviewQueueItem } from '~/types/api'

definePageMeta({ middleware: 'auth' })
useHead({ title: 'Проверка экспертом' })

const auth = useAuth()
const { data: categories } = useCategories()
const { data: queue, status } = useFetch<ReviewQueueItem[]>('/api/review/queue', {
  key: 'review-queue',
  server: false,
  immediate: auth.isExpert,
  default: () => [],
})

const REASON: Record<string, { label: string, cls: string, hint: string }> = {
  new: { label: 'новая', cls: 'tag--ice', hint: 'Ещё не проверялась' },
  updated: { label: 'обновлена', cls: 'tag--warn', hint: 'Автор выпустил новую версию после проверки' },
  changes_requested: { label: 'ждёт правок', cls: 'tag--crit', hint: 'Вы просили доработать — версия та же' },
}

const open = ref(false)
const current = ref<ReviewQueueItem | null>(null)
const detail = ref<GuideDetail | null>(null)
const loadingDetail = ref(false)
const note = ref('')
const submitting = ref(false)

async function startReview(item: ReviewQueueItem) {
  current.value = item
  detail.value = null
  note.value = ''
  open.value = true
  loadingDetail.value = true
  try {
    detail.value = await api<GuideDetail>(`/api/guides/${item.guide.slug}`)
  }
  finally {
    loadingDetail.value = false
  }
}

async function submit(verdict: 'approved' | 'changes') {
  if (!current.value) return
  if (verdict === 'changes' && !note.value.trim()) {
    toast.error('Напишите, что именно доработать — автор увидит заметку')
    return
  }
  submitting.value = true
  try {
    await api(`/api/review/guides/${current.value.guide.id}`, { method: 'POST', body: { verdict, note: note.value.trim() } })
    const id = current.value.guide.id
    queue.value = (queue.value ?? []).filter(q => q.guide.id !== id)
    open.value = false
    toast.success(verdict === 'approved' ? 'Инструкция отмечена как проверенная' : 'Замечания отправлены автору')
  }
  finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-[1180px] px-5 pt-12">
    <div v-if="!auth.isExpert" class="glass glass--lg mx-auto mt-10 max-w-xl p-10 text-center rise">
      <span class="ico mx-auto size-14"><ShieldAlert class="size-6" /></span>
      <h1 class="mt-5 text-[28px] font-extrabold silver">
        Раздел для экспертов
      </h1>
      <p class="mt-3 text-[var(--text-3)]">
        Эксперты проверяют инструкции в своих категориях. Подайте заявку в личном кабинете — администратор назначит роль.
      </p>
      <NuxtLink to="/me" class="btn-chrome mt-6">
        Подать заявку
      </NuxtLink>
    </div>

    <template v-else>
      <div class="flex flex-wrap items-end justify-between gap-6">
        <div class="scrim">
          <SectionLabel code>
            экспертиза
          </SectionLabel>
          <h1 class="mt-4 text-[38px] md:text-[56px] font-extrabold leading-[1.02] tracking-[-0.035em] silver" style="--lh: 1.02em">
            Очередь проверки
          </h1>
          <p class="mt-3 max-w-[620px] text-[var(--text-3)]">
            Проверенные инструкции получают бейдж «эксперт» и бонус в индексе полезности. Ваши категории:
            <b class="text-foreground">{{ auth.isAdmin ? 'все (админ)' : auth.user?.expert_categories.map(c => categoryTitle(categories, c)).join(', ') }}</b>.
          </p>
        </div>
        <div class="glass glass--pill h-11 px-5 inline-flex items-center gap-2 text-sm">
          <ClipboardCheck class="size-4" /> {{ pl(queue?.length ?? 0, 'инструкция ждёт', 'инструкции ждут', 'инструкций ждут') }}
        </div>
      </div>

      <div v-if="status === 'pending'" class="mt-8 space-y-3">
        <div v-for="i in 3" :key="i" class="skel h-[96px] !rounded-[22px]" />
      </div>

      <div v-else-if="queue?.length" class="mt-8 space-y-3">
        <article v-for="(q, i) in queue" :key="q.guide.id" class="row glass rise" :style="{ '--i': i }">
          <img :src="`/glass/${q.guide.cover}.webp`" alt="" class="size-16 object-contain shrink-0 hidden sm:block">
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <span class="tag" :class="REASON[q.reason]?.cls" :title="REASON[q.reason]?.hint">{{ REASON[q.reason]?.label }}</span>
              <span class="tag"><CategoryIcon :slug="q.guide.category" class="size-3.5" />{{ categoryTitle(categories, q.guide.category) }}</span>
              <span class="tag">v{{ q.version_number }}</span>
            </div>
            <NuxtLink :to="`/guides/${q.guide.slug}`" target="_blank" class="mt-2 block font-bold text-[17px] leading-snug hover:underline underline-offset-4">
              {{ q.guide.title }}
            </NuxtLink>
            <div class="mt-1.5 flex flex-wrap gap-x-4 gap-y-1 mono text-[12px] text-[var(--text-4)]">
              <span>{{ q.guide.author.name }}</span>
              <span class="inline-flex items-center gap-1"><ListChecks class="size-3.5" />{{ q.guide.steps_count }} шагов</span>
              <span class="inline-flex items-center gap-1"><Users class="size-3.5" />{{ formatNumber(q.guide.runs_count) }} прохождений</span>
              <span>дошли {{ percent(q.guide.completion_rate) }}</span>
            </div>
          </div>
          <button class="btn-chrome btn-chrome--sm shrink-0" @click="startReview(q)">
            Проверить
          </button>
        </article>
      </div>

      <div v-else class="glass glass--lg mt-8 p-10 text-center">
        <img src="/glass/ring.webp" alt="" class="w-32 mx-auto opacity-80">
        <h3 class="mt-4 text-2xl font-bold">
          Очередь пуста
        </h3>
        <p class="mt-2 text-[var(--text-3)]">
          Все инструкции в ваших категориях проверены. Загляните позже — авторы выпускают новые версии.
        </p>
      </div>
    </template>

    <Dialog v-model:open="open">
      <DialogContent class="sm:max-w-3xl max-h-[92vh] flex flex-col gap-0 p-0 overflow-hidden">
        <DialogHeader class="p-6 pb-4 border-b border-[var(--line)]">
          <DialogTitle class="text-xl pr-8">
            {{ current?.guide.title }}
          </DialogTitle>
          <DialogDescription>
            v{{ current?.version_number }} · {{ current?.guide.author.name }} · проверьте точность, полноту и безопасность шагов
          </DialogDescription>
        </DialogHeader>
        <div class="flex-1 overflow-y-auto p-6 space-y-4">
          <template v-if="loadingDetail">
            <div v-for="i in 3" :key="i" class="skel h-28" />
          </template>
          <template v-else-if="detail">
            <p class="text-[15px] text-[var(--text-2)]">
              {{ detail.summary }}
            </p>
            <div v-for="(s, i) in detail.steps" :key="s.key" class="p-5 rounded-[20px] bg-[var(--wash)] shadow-[inset_0_0_0_1px_var(--line)]">
              <div class="flex items-start gap-3">
                <span class="display text-[20px] text-[var(--text-4)] w-9 shrink-0">{{ String(i + 1).padStart(2, '0') }}</span>
                <div class="min-w-0 flex-1">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="font-semibold text-[16px]">{{ s.title }}</span>
                    <span class="tag"><Clock class="size-3" />{{ formatMinutes(s.minutes) }}</span>
                    <span v-if="detail.step_stats[s.key]?.down" class="tag tag--crit" title="Ученики отметили «не полезно»">
                      <MessageSquareWarning class="size-3" />{{ detail.step_stats[s.key]!.down }}
                    </span>
                  </div>
                  <MarkdownView :source="s.body" class="mt-3 !text-[14.5px]" />
                  <ul v-if="s.checklist.length" class="mt-3 space-y-1.5">
                    <li v-for="c in s.checklist" :key="c.key" class="flex items-start gap-2 text-[14px] text-[var(--text-2)]">
                      <span class="mt-0.5 size-4 rounded-[5px] shrink-0 shadow-[inset_0_0_0_1.5px_var(--line-2)]" />{{ c.text }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </template>
        </div>
        <div class="p-5 border-t border-[var(--line)] space-y-3">
          <textarea v-model="note" class="field !min-h-[72px] !text-[14px]" maxlength="1500" placeholder="Заметка автору: что проверили, что стоит уточнить (обязательно, если просите доработать)" />
          <div class="flex flex-wrap justify-end gap-2">
            <button class="btn-glass btn-glass--sm" :disabled="submitting" @click="submit('changes')">
              Нужны правки
            </button>
            <button class="btn-chrome btn-chrome--sm" :disabled="submitting || loadingDetail" @click="submit('approved')">
              <BadgeCheck class="size-4" /> Одобрить
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<style scoped>
.row {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 16px 20px;
  border-radius: 22px;
}
</style>
