<script setup lang="ts">
import { ArrowLeft, Check, GitMerge, GitPullRequestArrow, X } from '@lucide/vue'
import { toast } from 'vue-sonner'
import type { SuggestionOut } from '~/types/api'

definePageMeta({ middleware: 'auth' })
useHead({ title: 'Предложенные правки' })

type Tab = 'open' | 'accepted' | 'rejected'
const tab = ref<Tab>('open')
const { data: items, status, refresh } = useFetch<SuggestionOut[]>('/api/studio/suggestions', {
  query: computed(() => ({ status: tab.value })),
  default: () => [],
})

const replies = reactive<Record<number, string>>({})
const modes = reactive<Record<number, 'diff' | 'preview'>>({})
const busy = ref<number | null>(null)

async function resolve(s: SuggestionOut, action: 'accept' | 'reject') {
  busy.value = s.id
  try {
    await api(`/api/studio/suggestions/${s.id}/${action}`, { method: 'POST', body: { reply: replies[s.id] ?? '' } })
    toast.success(action === 'accept' ? 'Правка влита в черновик' : 'Правка отклонена', {
      description: action === 'accept' ? 'Опубликуйте новую версию, когда будете готовы' : undefined,
      action: action === 'accept' ? { label: 'В редактор', onClick: () => navigateTo(`/studio/${s.guide_id}`) } : undefined,
    })
    refresh()
  }
  finally {
    busy.value = null
  }
}

const TABS: { v: Tab, l: string }[] = [
  { v: 'open', l: 'Ждут решения' },
  { v: 'accepted', l: 'Влиты' },
  { v: 'rejected', l: 'Отклонены' },
]
</script>

<template>
  <div class="mx-auto max-w-[1000px] px-5 pt-10">
    <NuxtLink to="/studio" class="label hover:text-foreground">
      <ArrowLeft class="size-3.5" /> студия
    </NuxtLink>
    <div class="scrim mt-4">
      <h1 class="text-[38px] md:text-[54px] font-extrabold leading-[1.04] silver" style="--lh: 1.04em">
        Предложенные правки
      </h1>
      <p class="mt-3 text-[var(--text-3)] max-w-[600px]">
        Ученики и эксперты предлагают улучшения шагов — как pull request. Примите правку, и она войдёт в черновик следующей версии.
      </p>
    </div>

    <div class="mt-8 flex gap-2">
      <button v-for="t in TABS" :key="t.v" class="chip" :class="tab === t.v && 'chip--on'" @click="tab = t.v">
        {{ t.l }}
      </button>
    </div>

    <div class="mt-6 space-y-4">
      <template v-if="status === 'pending' && !items?.length">
        <div v-for="i in 2" :key="i" class="skel h-64 !rounded-[26px]" />
      </template>

      <article v-for="(s, i) in items" :key="s.id" class="glass glass--lg p-5 md:p-7 rise" :style="{ '--i': i }">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="flex items-start gap-3 min-w-0">
            <UserAvatar :id="s.user.id" :name="s.user.name" :size="40" />
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2 text-[14px]">
                <span class="font-semibold">{{ s.user.name }}</span>
                <span v-if="s.user.role === 'expert'" class="tag tag--ok">эксперт</span>
                <span class="text-[var(--text-4)]">{{ timeAgo(s.created_at) }}</span>
              </div>
              <NuxtLink :to="`/guides/${s.guide_slug}`" class="block mt-1 text-[13.5px] text-[var(--text-3)] hover:underline truncate">
                {{ s.guide_title }}
              </NuxtLink>
            </div>
          </div>
          <span class="tag" :class="s.status === 'open' ? 'tag--ice' : s.status === 'accepted' ? 'tag--ok' : 'tag--crit'">
            <GitPullRequestArrow v-if="s.status === 'open'" class="size-3.5" />
            <GitMerge v-else-if="s.status === 'accepted'" class="size-3.5" />
            <X v-else class="size-3.5" />
            {{ s.status === 'open' ? 'открыта' : s.status === 'accepted' ? 'влита' : 'отклонена' }}
          </span>
        </div>

        <h2 class="mt-5 text-[20px] font-bold leading-snug">
          <span class="text-[var(--text-4)] font-normal">Шаг:</span>
          {{ s.current_title ?? 'шаг удалён из черновика' }}
          <template v-if="s.title && s.title !== s.current_title">
            <span class="text-[var(--text-4)] font-normal"> → </span><span class="text-[var(--ok)]">{{ s.title }}</span>
          </template>
        </h2>
        <p v-if="s.message" class="mt-3 p-3 rounded-2xl bg-[var(--wash)] text-[14.5px] text-[var(--text-2)]">
          «{{ s.message }}»
        </p>

        <div class="mt-5 flex gap-1">
          <button class="chip !h-8 !text-[13px]" :class="(modes[s.id] ?? 'preview') === 'preview' && 'chip--on'" @click="modes[s.id] = 'preview'">
            было / стало
          </button>
          <button class="chip !h-8 !text-[13px]" :class="modes[s.id] === 'diff' && 'chip--on'" @click="modes[s.id] = 'diff'">
            построчно
          </button>
        </div>
        <TextDiff class="mt-3" :before="s.current_body ?? ''" :after="s.body" :mode="modes[s.id] ?? 'preview'" />

        <template v-if="s.status === 'open'">
          <input v-model="replies[s.id]" class="field mt-5" placeholder="Ответ автору правки (необязательно)">
          <div class="mt-4 flex flex-wrap justify-end gap-2">
            <button class="btn-glass btn-glass--sm" :disabled="busy === s.id" @click="resolve(s, 'reject')">
              <X class="size-4" /> Отклонить
            </button>
            <button class="btn-chrome btn-chrome--sm" :disabled="busy === s.id" @click="resolve(s, 'accept')">
              <Check class="size-4" /> Влить в черновик
            </button>
          </div>
        </template>
        <p v-else-if="s.reply" class="mt-4 text-[14px] text-[var(--text-3)]">
          Ваш ответ: «{{ s.reply }}»
        </p>
      </article>

      <div v-if="status !== 'pending' && !items?.length" class="glass glass--lg p-10 text-center">
        <img src="/glass/ring.webp" alt="" class="w-32 mx-auto opacity-80">
        <p class="mt-4 text-lg font-semibold">
          {{ tab === 'open' ? 'Новых правок нет' : 'Здесь пока пусто' }}
        </p>
        <p class="mt-1 text-[var(--text-3)]">
          Ученики могут предложить правку прямо во время прохождения — кнопка «Предложить правку» под шагом.
        </p>
      </div>
    </div>
  </div>
</template>
