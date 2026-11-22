<script setup lang="ts">
import { ArrowRight, Check, ChartNoAxesColumn, LifeBuoy, RotateCcw } from '@lucide/vue'

const TOTAL = 8
const demo = [
  {
    n: 3,
    title: 'Включите виртуализацию в BIOS',
    text: 'Перезагрузите компьютер и зайдите в BIOS — обычно **Del** или **F2** при включении.',
    items: ['Зашёл в BIOS', 'Включил Intel VT-x или AMD SVM', 'Сохранил настройки и перезагрузился'],
    start: [true, true, false],
  },
  {
    n: 4,
    title: 'Установите WSL 2',
    text: 'Откройте PowerShell от администратора и выполните `wsl --install`.',
    items: ['Команда отработала без ошибок', 'Компьютер перезагружен'],
    start: [false, false],
  },
  {
    n: 5,
    title: 'Установите Docker Desktop',
    text: 'Скачайте установщик с docker.com и оставьте галочку **Use WSL 2**.',
    items: ['Установщик скачан', 'Docker Desktop запустился'],
    start: [false, false],
  },
]

const idx = ref(0)
const finished = ref(false)
const checked = ref<boolean[]>([...demo[0]!.start])
const step = computed(() => demo[idx.value]!)
const ready = computed(() => checked.value.every(Boolean))
const parts = computed(() => Array.from({ length: TOTAL }, (_, i) => finished.value ? i < step.value.n : i < step.value.n - 1))

function toggle(i: number) {
  checked.value[i] = !checked.value[i]
}

function next() {
  if (!ready.value) return
  if (idx.value === demo.length - 1) {
    finished.value = true
    return
  }
  idx.value++
  checked.value = [...step.value.start]
}

function reset() {
  finished.value = false
  idx.value = 0
  checked.value = [...demo[0]!.start]
}

function md(s: string) {
  return s
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
}
</script>

<template>
  <div class="preview">
    <div class="preview__card panel">
      <div class="flex items-center justify-between gap-3">
        <span class="truncate text-[13px] font-medium text-[var(--text-3)]">Установить Docker на Windows 11</span>
        <span class="tag tabular-nums shrink-0">{{ finished ? 'готово' : `шаг ${step.n} из ${TOTAL}` }}</span>
      </div>
      <HairlineBar class="mt-3" :value="0" :parts="parts" :current="finished ? -1 : step.n - 1" />

      <Transition name="swap" mode="out-in">
        <div v-if="finished" key="done" class="py-8 text-center">
          <span class="mx-auto grid size-12 place-items-center rounded-full bg-[var(--ok-wash)] text-[var(--ok)]">
            <Check class="size-6" />
          </span>
          <p class="mt-3 font-semibold text-[16px]">
            Вот так это и работает
          </p>
          <p class="mt-1 text-[13.5px] text-[var(--text-3)]">
            Прогресс сохраняется, даже без регистрации
          </p>
          <button class="btn-secondary btn-sm mt-4" @click="reset">
            <RotateCcw class="size-3.5" /> Ещё раз
          </button>
        </div>

        <div v-else :key="step.n">
          <h3 class="mt-5 text-[19px] font-semibold leading-snug tracking-[-0.015em]">
            {{ step.title }}
          </h3>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <p class="preview__text mt-2 text-[14px] leading-relaxed text-[var(--text-2)]" v-html="md(step.text)" />

          <div class="mt-4 space-y-1.5">
            <button
              v-for="(item, i) in step.items"
              :key="item"
              class="pcheck"
              :class="checked[i] && 'pcheck--on'"
              role="checkbox"
              :aria-checked="checked[i]"
              @click="toggle(i)"
            >
              <span class="pcheck__box"><Check class="size-3.5" /></span>
              <span class="text-left">{{ item }}</span>
            </button>
          </div>

          <div class="mt-4 flex items-center gap-3">
            <span class="inline-flex items-center gap-1.5 text-[12.5px] text-[var(--text-4)]">
              <LifeBuoy class="size-3.5" />31 совет от прошедших
            </span>
            <button class="btn-primary btn-sm ml-auto" :disabled="!ready" @click="next">
              Готово, дальше <ArrowRight class="size-3.5" />
            </button>
          </div>
        </div>
      </Transition>
    </div>

    <div class="preview__note panel" aria-hidden="true">
      <span class="icon-box !size-8 !bg-[var(--crit-wash)] !text-[var(--crit)]"><ChartNoAxesColumn class="size-4" /></span>
      <div class="min-w-0">
        <div class="text-[12.5px] font-semibold">
          Узкое место · шаг 3
        </div>
        <div class="text-[12px] text-[var(--text-3)]">
          бросают 40%, автор уже правит
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.preview {
  position: relative;
}

@media (min-width: 1100px) {
  .preview { padding-bottom: 56px; }
}

.preview__card {
  position: relative;
  z-index: 1;
  padding: 20px;
  box-shadow: 0 24px 48px -24px rgba(16, 16, 20, .18), var(--shadow-sm);
}

.preview__text :deep(strong) {
  color: var(--foreground);
  font-weight: 600;
}

.preview__text :deep(code) {
  font-family: var(--font-mono);
  font-size: .88em;
  padding: .1em .35em;
  border-radius: 5px;
  background: var(--wash);
  border: 1px solid var(--line);
}

.preview__note {
  position: absolute;
  z-index: 2;
  right: -14px;
  bottom: 0;
  display: none;
  align-items: center;
  gap: 10px;
  padding: 10px 14px 10px 10px;
  box-shadow: var(--shadow-md);
}

@media (min-width: 1100px) {
  .preview__note { display: flex; }
}

.pcheck {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 40px;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 14px;
  border: 1px solid var(--line);
  transition: background .15s, border-color .15s, color .15s;
}

.pcheck:hover {
  border-color: var(--line-2);
}

.pcheck__box {
  flex: none;
  display: grid;
  place-items: center;
  width: 18px;
  height: 18px;
  border-radius: 5px;
  color: transparent;
  border: 1.5px solid var(--line-2);
  transition: background .15s, border-color .15s, color .15s;
}

.pcheck--on {
  color: var(--text-3);
  background: var(--subtle);
}

.pcheck--on .pcheck__box {
  color: var(--primary-foreground);
  background: var(--primary);
  border-color: var(--primary);
}

.swap-enter-active,
.swap-leave-active {
  transition: opacity .18s, transform .18s var(--ease);
}

.swap-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.swap-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.dark .preview__card {
  box-shadow: 0 24px 48px -24px rgba(0, 0, 0, .7), var(--shadow-sm);
}
</style>
