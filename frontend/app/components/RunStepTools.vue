<script setup lang="ts">
import { LifeBuoy, MessageSquare, PencilLine, Sparkles, ThumbsDown, ThumbsUp } from '@lucide/vue'
import { toast } from 'vue-sonner'
import type { CommentOut, HelpOut, StepOut, VoteOut } from '~/types/api'

const props = withDefaults(defineProps<{
  slug: string
  step: StepOut
  help: (q: string) => Promise<HelpOut | null>
  stats?: { up: number, down: number, my_vote: number | null }
  embedded?: boolean
}>(), { embedded: false, stats: undefined })

const auth = useAuth()
const route = useRoute()

const vote = ref<VoteOut | null>(null)
watch(() => props.step.key, () => (vote.value = null))
const myVote = computed(() => (vote.value ? vote.value.my_vote : props.stats?.my_vote ?? null))
const up = computed(() => vote.value?.up ?? props.stats?.up ?? 0)
const down = computed(() => vote.value?.down ?? props.stats?.down ?? 0)
async function castVote(value: 1 | -1) {
  vote.value = await api<VoteOut>(`/api/guides/${props.slug}/votes`, {
    method: 'POST',
    body: { step_key: props.step.key, value: myVote.value === value ? 0 : value },
  })
  if (value === -1 && myVote.value === -1) toast('Спасибо! Автор увидит, что шаг стоит улучшить')
}

const stuckOpen = ref(false)
const question = ref('')
const helpData = ref<HelpOut | null>(null)
const helpLoading = ref(false)
async function askHelp() {
  helpLoading.value = true
  try {
    helpData.value = await props.help(question.value)
    if (!helpData.value) toast('Нет сети — сигнал сохранён и уйдёт автору позже')
  }
  finally {
    helpLoading.value = false
  }
}
async function openStuck() {
  stuckOpen.value = true
  helpData.value = null
  question.value = ''
  await askHelp()
}

const commentsOpen = ref(false)
const comments = ref<CommentOut[]>([])
const body = ref('')
const kind = ref<'question' | 'tip' | 'comment'>('tip')
async function openComments() {
  commentsOpen.value = true
  comments.value = await api<CommentOut[]>(`/api/guides/${props.slug}/comments`, { query: { step_key: props.step.key } })
}
async function sendComment() {
  if (!body.value.trim()) return
  const c = await api<CommentOut>(`/api/guides/${props.slug}/comments`, {
    method: 'POST',
    body: { step_key: props.step.key, body: body.value, kind: kind.value },
  })
  comments.value.push(c)
  body.value = ''
}

const suggestOpen = ref(false)
const sTitle = ref('')
const sBody = ref('')
const sMessage = ref('')
function openSuggest() {
  sTitle.value = props.step.title
  sBody.value = props.step.body
  sMessage.value = ''
  suggestOpen.value = true
}
async function sendSuggest() {
  await api(`/api/guides/${props.slug}/suggestions`, {
    method: 'POST',
    body: {
      step_key: props.step.key,
      title: sTitle.value !== props.step.title ? sTitle.value : null,
      body: sBody.value,
      message: sMessage.value,
    },
  })
  suggestOpen.value = false
  toast.success('Правка отправлена автору', { description: 'Если он её примет — она войдёт в новую версию' })
}

const loginLink = computed(() => ({ path: '/login', query: { next: route.fullPath } }))
const KIND: Record<string, string> = { question: 'вопрос', tip: 'совет', comment: 'комментарий' }
defineExpose({ openStuck })
</script>

<template>
  <div class="tools">
    <div class="flex items-center gap-1.5">
      <span class="text-[13px] text-[var(--text-3)] mr-1">Шаг полезен?</span>
      <button class="vote" :class="myVote === 1 && 'vote--on'" aria-label="Полезно" @click="castVote(1)">
        <ThumbsUp class="size-4" /><span class="mono">{{ up || '' }}</span>
      </button>
      <button class="vote" :class="myVote === -1 && 'vote--bad'" aria-label="Не полезно" @click="castVote(-1)">
        <ThumbsDown class="size-4" /><span class="mono">{{ down || '' }}</span>
      </button>
    </div>
    <div class="flex flex-wrap gap-2">
      <button class="btn-glass btn-glass--sm stuck" @click="openStuck">
        <LifeBuoy class="size-4" /> Застрял
      </button>
      <button class="btn-glass btn-glass--sm" @click="openComments">
        <MessageSquare class="size-4" /> Обсуждение
      </button>
      <button v-if="!embedded" class="btn-glass btn-glass--sm" @click="openSuggest">
        <PencilLine class="size-4" /> Предложить правку
      </button>
    </div>

    <Sheet v-model:open="stuckOpen">
      <SheetContent class="sm:max-w-md w-full overflow-y-auto">
        <SheetHeader>
          <SheetTitle class="text-xl">
            Застряли на шаге?
          </SheetTitle>
          <SheetDescription>«{{ step.title }}» — вот что помогло другим.</SheetDescription>
        </SheetHeader>
        <div class="px-4 pb-6 space-y-5">
          <div class="glass p-4">
            <div class="label mb-2">
              <Sparkles class="size-3.5" /> подсказка ии
            </div>
            <div v-if="helpLoading" class="space-y-2">
              <div class="skel h-4 w-11/12" /><div class="skel h-4 w-9/12" /><div class="skel h-4 w-10/12" />
            </div>
            <MarkdownView v-else-if="helpData?.hint" :source="helpData.hint" class="!text-[14.5px]" />
            <p v-else class="text-sm text-[var(--text-3)]">
              Подсказка сейчас недоступна. Загляните в советы ниже или задайте вопрос.
            </p>
          </div>
          <form class="space-y-2" @submit.prevent="askHelp">
            <textarea v-model="question" class="field !min-h-[88px] !text-[14.5px]" placeholder="Опишите, что не получается: «в BIOS нет пункта SVM»" />
            <button class="btn-chrome btn-chrome--sm w-full" :disabled="helpLoading">
              <Sparkles class="size-4" /> Спросить ИИ с учётом вопроса
            </button>
          </form>
          <div v-if="helpData?.tips.length">
            <div class="label mb-2">
              советы учеников и экспертов
            </div>
            <div class="space-y-2">
              <div v-for="t in helpData.tips" :key="t.id" class="p-3 rounded-2xl bg-[var(--wash)]">
                <div class="flex items-center gap-2 text-[12px]">
                  <UserAvatar :id="t.user.id" :name="t.user.name" :size="22" />
                  <span class="font-semibold">{{ t.user.name }}</span>
                  <span v-if="t.user.role === 'expert'" class="tag tag--ok !h-5">эксперт</span>
                  <span class="tag !h-5" :class="t.kind === 'tip' && 'tag--ice'">{{ KIND[t.kind] }}</span>
                </div>
                <p class="mt-1.5 text-[14px] text-[var(--text-2)] whitespace-pre-line">
                  {{ t.body }}
                </p>
              </div>
            </div>
          </div>
          <p class="text-[12px] text-[var(--text-4)]">
            Автор инструкции увидит, что на этом шаге застревают, — и сможет его улучшить.
          </p>
        </div>
      </SheetContent>
    </Sheet>

    <Sheet v-model:open="commentsOpen">
      <SheetContent class="sm:max-w-md w-full overflow-y-auto">
        <SheetHeader>
          <SheetTitle class="text-xl">
            Обсуждение шага
          </SheetTitle>
          <SheetDescription>{{ step.title }}</SheetDescription>
        </SheetHeader>
        <div class="px-4 pb-6 space-y-3">
          <p v-if="!comments.length" class="text-sm text-[var(--text-3)]">
            Пока никто не писал. Будьте первым — ваш совет поможет следующим.
          </p>
          <div v-for="c in comments" :key="c.id" class="p-3 rounded-2xl bg-[var(--wash)]">
            <div class="flex flex-wrap items-center gap-2 text-[12px]">
              <UserAvatar :id="c.user.id" :name="c.user.name" :size="22" />
              <span class="font-semibold">{{ c.user.name }}</span>
              <span v-if="c.user.role === 'expert'" class="tag tag--ok !h-5">эксперт</span>
              <span v-if="c.is_author" class="tag tag--lit !h-5">автор</span>
              <span class="tag !h-5" :class="c.kind === 'tip' && 'tag--ice'">{{ KIND[c.kind] }}</span>
              <span class="text-[var(--text-4)]">{{ timeAgo(c.created_at) }}</span>
            </div>
            <p class="mt-1.5 text-[14px] text-[var(--text-2)] whitespace-pre-line">
              {{ c.body }}
            </p>
          </div>
          <form v-if="auth.user" class="pt-2 space-y-2" @submit.prevent="sendComment">
            <div class="flex gap-1.5">
              <button v-for="k in (['tip', 'question', 'comment'] as const)" :key="k" type="button" class="chip !h-8 !text-[13px]" :class="kind === k && 'chip--on'" @click="kind = k">
                {{ KIND[k] }}
              </button>
            </div>
            <textarea v-model="body" class="field !min-h-[90px] !text-[14.5px]" placeholder="Например: «у MSI пункт называется SVM Mode»" />
            <button class="btn-chrome btn-chrome--sm w-full" :disabled="!body.trim()">
              Отправить
            </button>
          </form>
          <p v-else class="text-sm text-[var(--text-3)] pt-2">
            <NuxtLink :to="loginLink" class="underline text-foreground">Войдите</NuxtLink>, чтобы оставить совет. Прогресс прохождения сохранится.
          </p>
        </div>
      </SheetContent>
    </Sheet>

    <Dialog v-model:open="suggestOpen">
      <DialogContent class="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Предложить правку шага</DialogTitle>
          <DialogDescription>Автор сравнит вашу версию с текущей и сможет влить её одной кнопкой.</DialogDescription>
        </DialogHeader>
        <template v-if="auth.user">
          <input v-model="sTitle" class="field" placeholder="Заголовок шага">
          <textarea v-model="sBody" class="field mono !text-[13.5px] !min-h-[260px]" />
          <input v-model="sMessage" class="field" placeholder="Почему так лучше? (коротко)">
          <div class="flex justify-end gap-2">
            <button class="btn-glass btn-glass--sm" @click="suggestOpen = false">
              Отмена
            </button>
            <button class="btn-chrome btn-chrome--sm" :disabled="!sBody.trim() || sBody === step.body && sTitle === step.title" @click="sendSuggest">
              Отправить автору
            </button>
          </div>
        </template>
        <p v-else class="text-sm text-[var(--text-3)]">
          <NuxtLink :to="loginLink" class="underline text-foreground">Войдите</NuxtLink>, чтобы предлагать правки.
        </p>
      </DialogContent>
    </Dialog>
  </div>
</template>

<style scoped>
.tools {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.vote {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  min-width: 36px;
  padding: 0 11px;
  border-radius: 999px;
  font-size: 12.5px;
  color: var(--text-3);
  background: var(--wash);
  box-shadow: inset 0 0 0 1px var(--line);
  transition: all .2s var(--ease);
}

.vote:hover {
  color: var(--foreground);
}

.vote:active {
  transform: scale(.92);
}

.vote--on {
  color: var(--ok);
  background: var(--ok-wash);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--ok) 40%, transparent);
}

.vote--bad {
  color: var(--crit);
  background: var(--crit-wash);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--crit) 40%, transparent);
}

.stuck:hover {
  color: var(--warn);
}
</style>
