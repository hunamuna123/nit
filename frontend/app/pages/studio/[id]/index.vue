<script setup lang="ts">
import {
  ArrowLeft, ChartNoAxesColumn, Check, ChevronDown, CloudUpload, Copy, Eye, GitPullRequestArrow, GripVertical,
  ListChecks, MoreHorizontal, Plus, RotateCcw, ScanSearch, Sparkles, Trash2, Wand2, X,
} from '@lucide/vue'
import { VueDraggable } from 'vue-draggable-plus'
import { toast } from 'vue-sonner'
import type { AiImproveOut, AiReviewOut, EditorDoc } from '~/types/api'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const router = useRouter()
const id = Number(route.params.id)
const { data: categories } = useCategories()

interface FormStep { key: string, title: string, body: string, minutes: number, checklist: { key: string, text: string }[] }
interface Form { title: string, summary: string, category: string, tags: string[], difficulty: number, cover: string, steps: FormStep[] }

const doc = ref<EditorDoc | null>(null)
const form = ref<Form | null>(null)
const openKey = ref<string | null>(null)
const saveState = ref<'saved' | 'dirty' | 'saving' | 'error'>('saved')
const loadError = ref('')

useHead(() => ({ title: form.value?.title ? `Редактор · ${form.value.title}` : 'Редактор' }))

const newKey = () => crypto.randomUUID()
const itemKey = () => crypto.randomUUID().slice(0, 8)

function toForm(d: EditorDoc): Form {
  return {
    title: d.title,
    summary: d.summary,
    category: d.category,
    tags: [...d.tags],
    difficulty: d.difficulty,
    cover: d.cover,
    steps: d.steps.map(s => ({ key: s.key, title: s.title, body: s.body, minutes: s.minutes, checklist: s.checklist.map(c => ({ ...c })) })),
  }
}

async function load() {
  try {
    doc.value = await api<EditorDoc>(`/api/studio/guides/${id}`, { silent: true })
    skipNext = true
    form.value = toForm(doc.value)
    if (!form.value.steps.length) addStep()
    else openKey.value = form.value.steps[0]!.key
    await nextTick()
    saveState.value = 'saved'
  }
  catch (e) {
    loadError.value = apiErrorMessage(e, 'Не удалось открыть инструкцию')
  }
}
onMounted(load)

let timer: ReturnType<typeof setTimeout> | undefined
let skipNext = false
watch(form, () => {
  if (skipNext) {
    skipNext = false
    return
  }
  saveState.value = 'dirty'
  clearTimeout(timer)
  timer = setTimeout(save, 1200)
}, { deep: true })

async function save() {
  if (!form.value) return
  clearTimeout(timer)
  saveState.value = 'saving'
  try {
    const payload = {
      ...form.value,
      steps: form.value.steps.map(s => ({ ...s, checklist: s.checklist.filter(c => c.text.trim()) })),
    }
    doc.value = await api<EditorDoc>(`/api/studio/guides/${id}`, { method: 'PUT', body: payload, silent: true })
    saveState.value = 'saved'
  }
  catch (e) {
    saveState.value = 'error'
    toast.error(apiErrorMessage(e, 'Не удалось сохранить'))
  }
}

onBeforeRouteLeave(async () => {
  if (saveState.value === 'dirty' || saveState.value === 'error') await save()
})

function addStep(title = '') {
  if (!form.value) return
  const s: FormStep = { key: newKey(), title, body: '', minutes: 5, checklist: [{ key: itemKey(), text: '' }] }
  form.value.steps.push(s)
  openKey.value = s.key
}
function duplicateStep(i: number) {
  const s = form.value!.steps[i]!
  const copy = { ...s, key: newKey(), title: `${s.title} (копия)`, checklist: s.checklist.map(c => ({ key: itemKey(), text: c.text })) }
  form.value!.steps.splice(i + 1, 0, copy)
  openKey.value = copy.key
}
function removeStep(i: number) {
  const [s] = form.value!.steps.splice(i, 1)
  toast('Шаг удалён', { action: { label: 'Вернуть', onClick: () => form.value!.steps.splice(i, 0, s!) } })
}
function addItem(s: FormStep) {
  s.checklist.push({ key: itemKey(), text: '' })
}

const tagInput = ref('')
function addTag() {
  const t = tagInput.value.trim().toLowerCase().replace(/^#/, '')
  if (t && form.value && !form.value.tags.includes(t) && form.value.tags.length < 8) form.value.tags.push(t)
  tagInput.value = ''
}

const MODES = [
  { v: 'clarify', l: 'Сделать понятнее для новичка' },
  { v: 'simplify', l: 'Упростить и сократить' },
  { v: 'checklist', l: 'Составить чек-лист' },
  { v: 'expand', l: 'Добавить частые ошибки и проверку' },
] as const
const improving = ref<string | null>(null)
const proposal = ref<{ step: FormStep, out: AiImproveOut } | null>(null)
const customOpen = ref(false)
const customStep = ref<FormStep | null>(null)
const customText = ref('')
const diffMode = ref<'diff' | 'preview'>('preview')

async function improve(s: FormStep, mode: string, instruction = '') {
  improving.value = s.key
  try {
    const out = await api<AiImproveOut>('/api/ai/improve-step', {
      method: 'POST',
      body: {
        guide_title: form.value!.title,
        step: { title: s.title, body: s.body, checklist: s.checklist.map(c => c.text).filter(Boolean) },
        mode,
        instruction,
      },
    })
    proposal.value = { step: s, out }
  }
  finally {
    improving.value = null
  }
}
function askCustom(s: FormStep) {
  customStep.value = s
  customText.value = ''
  customOpen.value = true
}
function applyProposal() {
  if (!proposal.value) return
  const { step, out } = proposal.value
  step.title = out.title
  step.body = out.body
  step.checklist = out.checklist.map(text => ({ key: step.checklist.find(c => c.text === text)?.key ?? itemKey(), text }))
  proposal.value = null
  toast.success('Правка ИИ применена — не забудьте проверить факты')
}

const review = ref<AiReviewOut | null>(null)
const reviewing = ref(false)
async function runReview() {
  if (!form.value) return
  reviewing.value = true
  try {
    review.value = await api<AiReviewOut>('/api/ai/review', {
      method: 'POST',
      body: {
        title: form.value.title,
        summary: form.value.summary,
        steps: form.value.steps.map(s => ({ title: s.title, body: s.body, checklist: s.checklist.map(c => c.text).filter(Boolean) })),
      },
    })
  }
  finally {
    reviewing.value = false
  }
}
function goToStep(i: number) {
  const s = form.value?.steps[i]
  if (!s) return
  openKey.value = s.key
  nextTick(() => document.getElementById(`step-${s.key}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' }))
}

const publishOpen = ref(false)
const changelog = ref('')
const publishing = ref(false)
const nextVersion = computed(() => (doc.value?.published_version?.number ?? 0) + 1)
async function publish() {
  await save()
  publishing.value = true
  try {
    doc.value = await api<EditorDoc>(`/api/studio/guides/${id}/publish`, { method: 'POST', body: { changelog: changelog.value } })
    publishOpen.value = false
    changelog.value = ''
    toast.success(`Опубликована версия v${doc.value.published_version?.number}`, {
      action: { label: 'Открыть', onClick: () => router.push(`/guides/${doc.value!.slug}`) },
    })
  }
  finally {
    publishing.value = false
  }
}
async function discard() {
  doc.value = await api<EditorDoc>(`/api/studio/guides/${id}/discard`, { method: 'POST' })
  skipNext = true
  form.value = toForm(doc.value)
  toast('Черновик откатан к опубликованной версии')
}
async function archive() {
  await api(`/api/studio/guides/${id}`, { method: 'DELETE' })
  toast('Инструкция убрана из каталога')
  router.push('/studio')
}

const totalMinutes = computed(() => form.value?.steps.reduce((a, s) => a + (Number(s.minutes) || 0), 0) ?? 0)
const SAVE_LABEL = { saved: 'Сохранено', dirty: 'Есть изменения…', saving: 'Сохраняем…', error: 'Ошибка сохранения' }
const SEVERITY: Record<string, string> = { high: 'tag--crit', medium: 'tag--warn', low: 'tag' }
const COVERS_LIST = ['torus', 'peanut', 'drop', 'blob', 'ring', 'infinity']
</script>

<template>
  <div class="mx-auto max-w-[1240px] px-5 pt-8">
    <div v-if="loadError" class="glass glass--lg p-10 text-center mt-10">
      <p class="text-lg font-semibold">
        {{ loadError }}
      </p>
      <NuxtLink to="/studio" class="btn-chrome mt-5">
        В студию
      </NuxtLink>
    </div>

    <template v-else-if="form && doc">
      <div class="topbar glass glass--pill">
        <NuxtLink to="/studio" class="icon-btn" aria-label="Назад в студию">
          <ArrowLeft class="size-5" />
        </NuxtLink>
        <div class="min-w-0 flex-1">
          <div class="truncate font-semibold text-[14.5px]">
            {{ form.title || 'Без названия' }}
          </div>
          <div class="mono text-[11.5px]" :class="saveState === 'error' ? 'text-[var(--crit)]' : 'text-[var(--text-4)]'">
            {{ SAVE_LABEL[saveState] }}
            <template v-if="doc.published_version"> · опубликована v{{ doc.published_version.number }}</template>
            <template v-else> · ещё не опубликовано</template>
          </div>
        </div>
        <button class="btn-glass btn-glass--sm hidden sm:inline-flex" :disabled="reviewing" @click="runReview">
          <ScanSearch class="size-4" :class="reviewing && 'animate-pulse'" /> {{ reviewing ? 'Проверяем…' : 'ИИ-проверка' }}
        </button>
        <button class="btn-chrome btn-chrome--sm" :disabled="!doc.has_unpublished_changes && !!doc.published_version" @click="publishOpen = true">
          <CloudUpload class="size-4" /> Опубликовать
        </button>
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <button class="icon-btn" aria-label="Ещё">
              <MoreHorizontal class="size-5" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" class="w-60 rounded-2xl p-1.5">
            <DropdownMenuItem v-if="doc.published_version" as-child>
              <NuxtLink :to="`/guides/${doc.slug}`"><Eye /> Публичная страница</NuxtLink>
            </DropdownMenuItem>
            <DropdownMenuItem v-if="doc.published_version" as-child>
              <NuxtLink :to="`/studio/${doc.id}/analytics`"><ChartNoAxesColumn /> Аналитика</NuxtLink>
            </DropdownMenuItem>
            <DropdownMenuItem class="sm:hidden" @click="runReview">
              <ScanSearch /> ИИ-проверка
            </DropdownMenuItem>
            <DropdownMenuItem v-if="doc.published_version && doc.has_unpublished_changes" @click="discard">
              <RotateCcw /> Откатить к опубликованной
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem class="text-destructive" @click="archive">
              <Trash2 /> {{ doc.published_version ? 'Снять с публикации' : 'Удалить черновик' }}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div class="mt-6 grid gap-6 lg:grid-cols-[1fr_320px]">
        <div class="min-w-0 space-y-4">
          <section class="glass glass--lg p-6 md:p-8">
            <div v-if="doc.forked_from" class="mb-4 tag">
              форк «{{ doc.forked_from.title }}» · {{ doc.forked_from.author_name }}
            </div>
            <input v-model="form.title" class="title-input" placeholder="Название: глагол + результат" maxlength="160">
            <textarea v-model="form.summary" class="summary-input" rows="2" placeholder="Что человек получит в конце? Одно-два предложения" maxlength="600" />

            <div class="mt-5 grid gap-4 md:grid-cols-2">
              <div>
                <div class="label mb-2">
                  категория
                </div>
                <Select v-model="form.category">
                  <SelectTrigger class="h-11 w-full rounded-2xl bg-[var(--wash)]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent class="rounded-2xl">
                    <SelectItem v-for="c in categories" :key="c.slug" :value="c.slug">
                      {{ c.title }}
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <div class="label mb-2">
                  сложность
                </div>
                <div class="seg">
                  <button v-for="d in [1, 2, 3]" :key="d" class="seg__btn" :class="form.difficulty === d && 'seg__btn--on'" @click="form.difficulty = d">
                    {{ DIFFICULTY[d] }}
                  </button>
                </div>
              </div>
              <div>
                <div class="label mb-2">
                  теги
                </div>
                <div class="tags">
                  <span v-for="t in form.tags" :key="t" class="tag tag--lit">#{{ t }}<button :aria-label="`Удалить ${t}`" @click="form.tags = form.tags.filter(x => x !== t)"><X class="size-3" /></button></span>
                  <input v-model="tagInput" class="flex-1 min-w-[90px] bg-transparent outline-none text-[14px]" placeholder="+ тег, Enter" @keydown.enter.prevent="addTag" @blur="addTag">
                </div>
              </div>
              <div>
                <div class="label mb-2">
                  обложка
                </div>
                <div class="flex gap-2">
                  <button v-for="c in COVERS_LIST" :key="c" class="cover" :class="form.cover === c && 'cover--on'" :aria-label="c" @click="form.cover = c">
                    <img :src="`/glass/${c}.webp`" alt="">
                  </button>
                </div>
              </div>
            </div>
          </section>

          <div class="flex items-center justify-between px-1 pt-2">
            <SectionLabel>шаги · {{ form.steps.length }} · ≈ {{ formatMinutes(totalMinutes) }}</SectionLabel>
            <span class="label hidden sm:inline-flex">перетаскивайте за <GripVertical class="size-3.5" /></span>
          </div>

          <VueDraggable v-model="form.steps" handle=".handle" :animation="200" ghost-class="ghost" class="space-y-3">
            <article v-for="(s, i) in form.steps" :id="`step-${s.key}`" :key="s.key" class="step glass" :class="openKey === s.key && 'step--open'">
              <div class="step__head">
                <button class="handle" aria-label="Перетащить шаг">
                  <GripVertical class="size-4" />
                </button>
                <span class="display text-[20px] text-[var(--text-4)] w-9 shrink-0">{{ String(i + 1).padStart(2, '0') }}</span>
                <input v-model="s.title" class="step__title" :placeholder="`Шаг ${i + 1}: что сделать`" @focus="openKey = s.key">
                <label class="minutes" title="Минут на шаг">
                  <input v-model.number="s.minutes" type="number" min="1" max="600">мин
                </label>
                <DropdownMenu>
                  <DropdownMenuTrigger as-child>
                    <button class="ai-btn" :disabled="improving === s.key" title="Улучшить шаг с ИИ">
                      <Wand2 class="size-4" :class="improving === s.key && 'animate-spin'" />
                      <span class="hidden md:inline">{{ improving === s.key ? 'Думаю…' : 'ИИ' }}</span>
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" class="w-72 rounded-2xl p-1.5">
                    <DropdownMenuLabel class="text-xs text-muted-foreground">
                      Улучшить шаг с ИИ
                    </DropdownMenuLabel>
                    <DropdownMenuItem v-for="m in MODES" :key="m.v" @click="improve(s, m.v)">
                      <Sparkles /> {{ m.l }}
                    </DropdownMenuItem>
                    <DropdownMenuItem @click="askCustom(s)">
                      <Wand2 /> Своя просьба…
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                <DropdownMenu>
                  <DropdownMenuTrigger as-child>
                    <button class="icon-btn !size-9" aria-label="Действия с шагом">
                      <MoreHorizontal class="size-4" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" class="rounded-2xl p-1.5">
                    <DropdownMenuItem @click="duplicateStep(i)">
                      <Copy /> Дублировать
                    </DropdownMenuItem>
                    <DropdownMenuItem class="text-destructive" @click="removeStep(i)">
                      <Trash2 /> Удалить шаг
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                <button class="icon-btn !size-9" :aria-expanded="openKey === s.key" aria-label="Развернуть" @click="openKey = openKey === s.key ? null : s.key">
                  <ChevronDown class="size-4 transition-transform" :class="openKey === s.key && 'rotate-180'" />
                </button>
              </div>

              <div v-if="openKey === s.key" class="step__body">
                <MarkdownEditor v-model="s.body" />
                <div class="mt-5">
                  <div class="label mb-2">
                    <ListChecks class="size-3.5" /> чек-лист — что ученик должен проверить
                  </div>
                  <div class="space-y-2">
                    <div v-for="(c, ci) in s.checklist" :key="c.key" class="flex items-center gap-2">
                      <span class="size-5 rounded-md shrink-0 shadow-[inset_0_0_0_1.5px_var(--line-2)]" />
                      <input v-model="c.text" class="field !h-11 !rounded-xl !text-[14.5px]" placeholder="Проверяемый результат: «в выводе видно версию 2»" @keydown.enter.prevent="addItem(s)">
                      <button class="icon-btn !size-9 shrink-0" aria-label="Удалить пункт" @click="s.checklist.splice(ci, 1)">
                        <X class="size-4" />
                      </button>
                    </div>
                  </div>
                  <button class="chip !h-9 mt-3" @click="addItem(s)">
                    <Plus class="size-4" /> пункт
                  </button>
                </div>
              </div>
            </article>
          </VueDraggable>

          <button class="add-step" @click="addStep()">
            <Plus class="size-5" /> Добавить шаг
          </button>
        </div>

        <aside class="space-y-4 lg:sticky lg:top-[96px] self-start">
          <div class="glass p-5">
            <div class="label">
              статус
            </div>
            <div class="mt-2 flex items-center gap-2 font-semibold">
              <span class="size-2.5 rounded-full" :class="doc.has_unpublished_changes ? 'bg-[var(--warn)]' : 'bg-[var(--ok)]'" />
              {{ !doc.published_version ? 'Черновик' : doc.has_unpublished_changes ? 'Есть неопубликованные правки' : 'Всё опубликовано' }}
            </div>
            <p class="mt-2 text-[13px] text-[var(--text-3)] leading-snug">
              Ученики проходят опубликованную версию. Каждая публикация — новая версия, аналитику можно сравнить «до / после».
            </p>
            <div v-if="doc.versions.length" class="mt-4 space-y-1.5">
              <div v-for="v in doc.versions.slice(0, 4)" :key="v.id" class="flex items-start gap-2 text-[13px]">
                <span class="tag !h-5 shrink-0">v{{ v.number }}</span>
                <span class="text-[var(--text-3)] line-clamp-1">{{ v.changelog || 'без описания' }}</span>
              </div>
            </div>
            <div class="mt-4 flex flex-col gap-2">
              <NuxtLink v-if="doc.open_suggestions" to="/studio/inbox" class="btn-glass btn-glass--sm justify-start">
                <GitPullRequestArrow class="size-4" /> {{ pl(doc.open_suggestions, 'правка ждёт', 'правки ждут', 'правок ждут') }} решения
              </NuxtLink>
              <NuxtLink v-if="doc.published_version" :to="`/studio/${doc.id}/analytics`" class="btn-glass btn-glass--sm justify-start">
                <ChartNoAxesColumn class="size-4" /> Аналитика узких мест
              </NuxtLink>
            </div>
          </div>

          <div class="glass p-5">
            <div class="flex items-center justify-between">
              <div class="label">
                <ScanSearch class="size-3.5" /> ии-проверка
              </div>
              <button class="text-[12.5px] text-[var(--text-3)] hover:text-foreground" :disabled="reviewing" @click="runReview">
                {{ review ? 'ещё раз' : 'запустить' }}
              </button>
            </div>
            <div v-if="reviewing" class="mt-4 space-y-2">
              <div class="skel h-10 w-20" /><div class="skel h-4" /><div class="skel h-4 w-4/5" />
            </div>
            <template v-else-if="review">
              <div class="mt-3 flex items-end gap-2">
                <span class="display silver text-[44px] leading-none">{{ review.score }}</span>
                <span class="mb-1 text-[13px] text-[var(--text-3)]">/ 100</span>
              </div>
              <p class="mt-2 text-[13.5px] text-[var(--text-2)]">
                {{ review.verdict }}
              </p>
              <div class="mt-3 space-y-2">
                <button v-for="(it, k) in review.issues" :key="k" class="issue" @click="it.step_index >= 0 && goToStep(it.step_index)">
                  <span class="tag !h-5 shrink-0" :class="SEVERITY[it.severity]">{{ it.step_index >= 0 ? `шаг ${it.step_index + 1}` : 'общее' }}</span>
                  <span class="text-left text-[13px] leading-snug">{{ it.message }}</span>
                </button>
              </div>
              <div v-if="review.missing_steps.length" class="mt-4">
                <div class="label mb-2">
                  не хватает шагов
                </div>
                <button v-for="m in review.missing_steps" :key="m" class="issue" @click="addStep(m)">
                  <Plus class="size-4 shrink-0" /><span class="text-left text-[13px]">{{ m }}</span>
                </button>
              </div>
            </template>
            <p v-else class="mt-3 text-[13px] text-[var(--text-3)] leading-snug">
              ИИ-редактор найдёт пропущенные шаги, неясные места и шаги без проверки результата.
            </p>
          </div>
        </aside>
      </div>
    </template>

    <div v-else class="space-y-4 mt-4">
      <div class="skel h-[60px] !rounded-full" /><div class="skel h-[260px]" /><div class="skel h-[80px]" />
    </div>

    <Dialog :open="!!proposal" @update:open="v => !v && (proposal = null)">
      <DialogContent class="sm:max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle class="flex items-center gap-2">
            <Sparkles class="size-5" /> Вариант от ИИ
          </DialogTitle>
          <DialogDescription>{{ proposal?.out.note }}</DialogDescription>
        </DialogHeader>
        <template v-if="proposal">
          <div v-if="proposal.out.title !== proposal.step.title" class="text-[14px]">
            <span class="label">заголовок:</span>
            <span class="line-through text-[var(--crit)] ml-2">{{ proposal.step.title }}</span>
            <span class="text-[var(--ok)] ml-2">{{ proposal.out.title }}</span>
          </div>
          <div class="flex gap-1">
            <button class="chip !h-8 !text-[13px]" :class="diffMode === 'preview' && 'chip--on'" @click="diffMode = 'preview'">
              было / стало
            </button>
            <button class="chip !h-8 !text-[13px]" :class="diffMode === 'diff' && 'chip--on'" @click="diffMode = 'diff'">
              построчно
            </button>
          </div>
          <TextDiff :before="proposal.step.body" :after="proposal.out.body" :mode="diffMode" />
          <div v-if="proposal.out.checklist.length">
            <div class="label mb-2">
              чек-лист
            </div>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="c in proposal.out.checklist" :key="c" class="tag tag--ok">☐ {{ c }}</span>
            </div>
          </div>
          <div class="flex justify-end gap-2">
            <button class="btn-glass btn-glass--sm" @click="proposal = null">
              Оставить как было
            </button>
            <button class="btn-chrome btn-chrome--sm" @click="applyProposal">
              <Check class="size-4" /> Применить
            </button>
          </div>
        </template>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="customOpen">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Что сделать с шагом?</DialogTitle>
          <DialogDescription>«{{ customStep?.title }}»</DialogDescription>
        </DialogHeader>
        <textarea v-model="customText" class="field !min-h-[100px]" placeholder="Например: добавь вариант для macOS и предупреждение про права администратора" />
        <button class="btn-chrome btn-chrome--sm" :disabled="!customText.trim()" @click="customOpen = false; customStep && improve(customStep, 'custom', customText)">
          <Wand2 class="size-4" /> Попросить ИИ
        </button>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="publishOpen">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Опубликовать v{{ nextVersion }}</DialogTitle>
          <DialogDescription>
            {{ nextVersion === 1 ? 'Инструкция появится в каталоге и поиске.' : 'Новые ученики пойдут по новой версии, а аналитику можно будет сравнить с предыдущей.' }}
          </DialogDescription>
        </DialogHeader>
        <input v-model="changelog" class="field" :placeholder="nextVersion === 1 ? 'Первая версия' : 'Что изменилось? «Разбил шаг про BIOS на два»'" maxlength="500" @keydown.enter="publish">
        <div class="flex justify-end gap-2">
          <button class="btn-glass btn-glass--sm" @click="publishOpen = false">
            Отмена
          </button>
          <button class="btn-chrome btn-chrome--sm" :disabled="publishing" @click="publish">
            <CloudUpload class="size-4" /> {{ publishing ? 'Публикуем…' : 'Опубликовать' }}
          </button>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<style scoped>
.topbar {
  position: sticky;
  top: 80px;
  z-index: 30;
  display: flex;
  align-items: center;
  gap: 8px;
  height: 60px;
  padding: 0 10px 0 8px;
}

.icon-btn {
  display: inline-grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  color: var(--text-2);
  transition: background .2s;
}

.icon-btn:hover {
  background: var(--wash);
}

.title-input {
  width: 100%;
  background: transparent;
  outline: none;
  font-size: clamp(26px, 3.4vw, 38px);
  font-weight: 800;
  letter-spacing: -.03em;
  line-height: 1.1;
}

.title-input::placeholder,
.summary-input::placeholder {
  color: var(--text-4);
}

.summary-input {
  width: 100%;
  margin-top: 10px;
  resize: none;
  background: transparent;
  outline: none;
  font-size: 16px;
  line-height: 1.5;
  color: var(--text-2);
}

.seg {
  display: flex;
  padding: 4px;
  gap: 2px;
  border-radius: 16px;
  background: var(--wash);
  box-shadow: inset 0 0 0 1px var(--line);
}

.seg__btn {
  flex: 1;
  height: 35px;
  border-radius: 12px;
  font-size: 13.5px;
  color: var(--text-3);
  transition: all .2s;
}

.seg__btn--on {
  color: var(--on-chrome);
  background: var(--chrome);
}

.tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  min-height: 44px;
  padding: 6px 10px;
  border-radius: 16px;
  background: var(--wash);
  box-shadow: inset 0 0 0 1px var(--line);
}

.tags .tag button {
  margin-left: 2px;
  opacity: .6;
}

.cover {
  width: 44px;
  height: 44px;
  padding: 4px;
  border-radius: 14px;
  background: var(--wash);
  box-shadow: inset 0 0 0 1px var(--line);
  transition: all .2s var(--ease);
}

.cover img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.cover--on {
  background: var(--wash-2);
  box-shadow: inset 0 0 0 1.5px rgba(255, 255, 255, .55), 0 0 16px rgba(200, 215, 255, .2);
  transform: scale(1.06);
}

.step {
  border-radius: 22px;
}

.step--open::before {
  background: var(--rim-strong);
}

.step__head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 10px 10px 8px;
}

.handle {
  display: grid;
  place-items: center;
  width: 28px;
  height: 36px;
  border-radius: 8px;
  color: var(--text-4);
  cursor: grab;
}

.handle:active {
  cursor: grabbing;
}

.step__title {
  flex: 1;
  min-width: 0;
  height: 40px;
  padding: 0 4px;
  background: transparent;
  outline: none;
  font-size: 16.5px;
  font-weight: 650;
}

.minutes {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 34px;
  padding: 0 10px;
  border-radius: 999px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-3);
  background: var(--wash);
  box-shadow: inset 0 0 0 1px var(--line);
}

.minutes input {
  width: 34px;
  background: transparent;
  outline: none;
  text-align: right;
  color: var(--foreground);
}

.minutes input::-webkit-inner-spin-button {
  appearance: none;
}

.ai-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  color: var(--ice);
  background: var(--ice-wash);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--ice) 30%, transparent);
  transition: filter .2s;
}

.ai-btn:hover {
  filter: brightness(1.2);
}

.step__body {
  padding: 4px 18px 20px 18px;
}

@media (min-width: 768px) {
  .step__body { padding-left: 82px; }
}

.ghost {
  opacity: .4;
}

.add-step {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  height: 64px;
  border-radius: 22px;
  font-weight: 600;
  color: var(--text-3);
  border: 1.5px dashed var(--line-2);
  transition: all .2s;
}

.add-step:hover {
  color: var(--foreground);
  background: var(--wash);
}

.issue {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  width: 100%;
  padding: 9px 10px;
  border-radius: 12px;
  background: var(--wash);
  transition: background .2s;
}

.issue:hover {
  background: var(--wash-2);
}
</style>
