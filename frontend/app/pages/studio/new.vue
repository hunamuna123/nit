<script setup lang="ts">
import { ArrowRight, ClipboardPaste, FilePlus2, RefreshCw, Sparkles, Wand2 } from '@lucide/vue'
import type { AiStatus, CreatedOut, GuideDraft } from '~/types/api'

definePageMeta({ middleware: 'auth' })
useHead({ title: 'Новая инструкция' })

const route = useRoute()
const router = useRouter()
const { data: categories } = useCategories()
const { data: aiStatus } = useFetch<AiStatus>('/api/ai/status')

type Mode = 'ai' | 'import' | 'blank'
const mode = ref<Mode>(typeof route.query.topic === 'string' || !route.query.mode ? 'ai' : (route.query.mode as Mode))
const topic = ref(typeof route.query.topic === 'string' ? route.query.topic : '')
const details = ref('')
const text = ref('')
const title = ref('')

const draft = ref<GuideDraft | null>(null)
const generating = ref(false)
const creating = ref(false)
const genError = ref('')

const ideas = ['Как оформить академическую справку для военкомата', 'Как перенести Windows на новый SSD без переустановки', 'Как подготовиться к первому собеседованию на стажировку', 'Как развернуть сайт на VPS через Docker']

async function generate() {
  genError.value = ''
  generating.value = true
  draft.value = null
  try {
    draft.value = mode.value === 'ai'
      ? await api<GuideDraft>('/api/ai/draft', { method: 'POST', body: { topic: topic.value, details: details.value }, silent: true })
      : await api<GuideDraft>('/api/ai/import', { method: 'POST', body: { text: text.value }, silent: true })
  }
  catch (e) {
    genError.value = apiErrorMessage(e, 'ИИ не ответил, попробуйте ещё раз')
  }
  finally {
    generating.value = false
  }
}

async function create(fromDraft: boolean) {
  creating.value = true
  try {
    const r = await api<CreatedOut>('/api/studio/guides', {
      method: 'POST',
      body: fromDraft && draft.value ? { draft: draft.value } : { title: title.value || 'Новая инструкция' },
    })
    router.push(`/studio/${r.id}`)
  }
  finally {
    creating.value = false
  }
}

const canGenerate = computed(() => (mode.value === 'ai' ? topic.value.trim().length >= 3 : text.value.trim().length >= 20))
const totalMinutes = computed(() => draft.value?.steps.reduce((a, s) => a + s.minutes, 0) ?? 0)

const modes = [
  { v: 'ai' as const, icon: Sparkles, title: 'ИИ по теме', text: 'Опишите задачу — получите черновик шагов с чек-листами' },
  { v: 'import' as const, icon: ClipboardPaste, title: 'Импорт из текста', text: 'Вставьте пост с форума или конспект — ИИ структурирует' },
  { v: 'blank' as const, icon: FilePlus2, title: 'С чистого листа', text: 'Пишите сами, ИИ поможет в редакторе' },
]
</script>

<template>
  <div class="mx-auto max-w-[1000px] px-5 pt-12">
    <div class="scrim">
      <SectionLabel code>
        новая инструкция
      </SectionLabel>
      <h1 class="mt-4 text-[38px] md:text-[56px] font-extrabold leading-[1.04] silver" style="--lh: 1.04em">
        С чего начнём?
      </h1>
    </div>

    <div class="mt-8 grid gap-3 sm:grid-cols-3">
      <button
        v-for="(m, i) in modes"
        :key="m.v"
        class="mode glass glass--hover rise text-left"
        :class="mode === m.v && 'mode--on glass--lit'"
        :style="{ '--i': i }"
        @click="mode = m.v; draft = null"
      >
        <span class="ico"><component :is="m.icon" class="size-[18px]" /></span>
        <span class="mt-4 block font-bold text-[17px]">{{ m.title }}</span>
        <span class="mt-1 block text-[13.5px] text-[var(--text-3)] leading-snug">{{ m.text }}</span>
      </button>
    </div>

    <div v-if="mode !== 'blank'" class="mt-6 glass glass--lg p-6 md:p-8">
      <p v-if="aiStatus && !aiStatus.enabled" class="mb-4 text-sm text-[var(--warn)]">
        ИИ на сервере не настроен — начните с чистого листа.
      </p>
      <template v-if="mode === 'ai'">
        <label class="label">о чём инструкция</label>
        <input v-model="topic" class="field mt-2 !text-[17px] !h-14" placeholder="Например: как получить налоговый вычет за обучение" @keydown.enter="canGenerate && generate()">
        <div class="mt-3 flex flex-wrap gap-2">
          <button v-for="idea in ideas" :key="idea" class="chip !h-8 !text-[13px]" @click="topic = idea">
            {{ idea }}
          </button>
        </div>
        <label class="label mt-6 block">уточнения (необязательно)</label>
        <textarea v-model="details" class="field mt-2 !min-h-[90px]" placeholder="Для кого, какие условия, что важно не забыть: «для студентов очной формы, через Госуслуги»" />
      </template>
      <template v-else>
        <label class="label">исходный текст</label>
        <textarea v-model="text" class="field mt-2 !min-h-[240px] !text-[14.5px]" placeholder="Вставьте сюда пост с форума, расшифровку видео, заметки из чата — ИИ выделит шаги, команды и проверки" />
        <div class="mt-2 mono text-[12px] text-[var(--text-4)]">
          {{ formatNumber(text.length) }} / 30 000 символов
        </div>
      </template>

      <div class="mt-6 flex flex-wrap items-center gap-3">
        <button class="btn-chrome" :disabled="!canGenerate || generating || aiStatus?.enabled === false" @click="generate">
          <Wand2 class="size-4" :class="generating && 'animate-spin'" />
          {{ generating ? 'ИИ пишет шаги…' : mode === 'ai' ? 'Сгенерировать черновик' : 'Структурировать текст' }}
        </button>
        <span v-if="aiStatus?.enabled" class="mono text-[12px] text-[var(--text-4)]">{{ aiStatus.model }} · осталось {{ aiStatus.remaining_hour }} запросов в час</span>
      </div>
      <p v-if="genError" class="mt-3 text-sm text-[var(--crit)]">
        {{ genError }}
      </p>
    </div>

    <div v-if="generating" class="mt-6 glass p-6 space-y-3">
      <div class="skel h-8 w-2/3" />
      <div class="skel h-4 w-1/2" />
      <div v-for="i in 5" :key="i" class="skel h-14" />
    </div>

    <div v-if="draft" class="mt-6 glass glass--lg p-6 md:p-8 rise">
      <div class="flex flex-wrap items-center gap-2">
        <span class="tag tag--ice"><Sparkles class="size-3.5" />черновик ИИ</span>
        <span class="tag">{{ categoryTitle(categories, draft.category) }}</span>
        <span class="tag">{{ pl(draft.steps.length, 'шаг', 'шага', 'шагов') }} · {{ formatMinutes(totalMinutes) }}</span>
        <span v-for="t in draft.tags" :key="t" class="tag">#{{ t }}</span>
      </div>
      <h2 class="mt-4 text-[28px] font-extrabold leading-tight">
        {{ draft.title }}
      </h2>
      <p class="mt-2 text-[var(--text-2)]">
        {{ draft.summary }}
      </p>
      <ol class="mt-6 space-y-2">
        <li v-for="(s, i) in draft.steps" :key="i" class="flex gap-4 p-4 rounded-2xl bg-[var(--wash)]">
          <span class="display text-[18px] text-[var(--text-4)] w-8 shrink-0">{{ String(i + 1).padStart(2, '0') }}</span>
          <div class="min-w-0">
            <div class="font-semibold">
              {{ s.title }} <span class="mono text-[12px] text-[var(--text-4)] font-normal">· {{ s.minutes }} мин</span>
            </div>
            <div class="mt-1 text-[13.5px] text-[var(--text-3)] line-clamp-2">
              {{ stripMarkdown(s.body) }}
            </div>
            <div v-if="s.checklist.length" class="mt-2 flex flex-wrap gap-1.5">
              <span v-for="c in s.checklist" :key="c" class="tag !h-6 !text-[11px]">☐ {{ c }}</span>
            </div>
          </div>
        </li>
      </ol>
      <div class="mt-6 flex flex-wrap gap-3">
        <button class="btn-chrome" :disabled="creating" @click="create(true)">
          Открыть в редакторе <ArrowRight class="size-4" />
        </button>
        <button class="btn-glass" :disabled="generating" @click="generate">
          <RefreshCw class="size-4" /> Другой вариант
        </button>
      </div>
      <p class="mt-3 text-[12.5px] text-[var(--text-4)]">
        Черновик не публикуется автоматически: проверьте факты и шаги в редакторе.
      </p>
    </div>

    <div v-if="mode === 'blank'" class="mt-6 glass glass--lg p-6 md:p-8">
      <label class="label">название</label>
      <input v-model="title" class="field mt-2 !text-[17px] !h-14" placeholder="Глагол + результат: «Заселиться в общежитие»" @keydown.enter="create(false)">
      <button class="btn-chrome mt-6" :disabled="creating" @click="create(false)">
        Создать и открыть редактор <ArrowRight class="size-4" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.mode {
  padding: 20px;
  border-radius: 24px;
}

.mode--on {
  background: var(--glass-fill-strong);
}
</style>
