<script setup lang="ts">
import { ArrowRight, Check, LifeBuoy, RotateCcw } from '@lucide/vue'

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
const passed = (i: number) => finished.value || i < step.value.n

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
    <div class="preview__card">
      <div class="flex items-center justify-between gap-3">
        <span class="truncate text-[13px] text-[var(--text-3)]">Установить Docker на Windows 11</span>
        <span class="shrink-0 tabular-nums text-[12.5px] text-[var(--text-4)]">{{ finished ? 'готово' : `шаг ${step.n} из ${TOTAL}` }}</span>
      </div>

      <div class="sthread" aria-hidden="true">
        <template v-for="i in TOTAL" :key="i">
          <span class="sthread__node num" :class="{ 'is-done': passed(i), 'is-now': !finished && i === step.n }">
            <Check v-if="passed(i)" class="size-3" :stroke-width="3" />
            <template v-else>{{ i }}</template>
          </span>
          <span class="sthread__seg" :class="passed(i + 1) || (i < step.n && !finished) ? 'is-done' : ''" />
        </template>
        <svg class="sthread__knot" :class="finished && 'is-done'" viewBox="0 0 32 32">
          <path d="M2.5 21.5c3.5 0 6.6-2.4 8.4-5.8 1.6-3 1.6-6.6-.9-7.4-2.6-.8-4.1 2.6-2.2 5.6l6.7 9.6L28.8 8.2" />
        </svg>
      </div>

      <Transition name="swap" mode="out-in">
        <div v-if="finished" key="done" class="py-7 text-center">
          <p class="serif text-[22px] font-semibold">
            Нить завязана
          </p>
          <p class="mt-1.5 text-[14px] text-[var(--text-3)]">
            Так и проходят инструкции. Прогресс сохраняется даже без регистрации.
          </p>
          <button class="btn-secondary btn-sm mt-5" @click="reset">
            <RotateCcw class="size-3.5" /> Ещё раз
          </button>
        </div>

        <div v-else :key="step.n">
          <h3 class="mt-5 serif text-[22px] font-semibold leading-snug tracking-[-0.01em]">
            {{ step.title }}
          </h3>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <p class="preview__text mt-2 text-[14.5px] leading-relaxed text-[var(--text-2)]" v-html="md(step.text)" />

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
              <span class="pcheck__box"><Check class="size-3.5" :stroke-width="3" /></span>
              <span class="text-left">{{ item }}</span>
            </button>
          </div>

          <div class="mt-5 flex items-center gap-3">
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

    <div class="preview__note" aria-hidden="true">
      <div class="text-[12.5px] font-semibold">
        Автору: шаг 3 — узкое место
      </div>
      <div class="text-[12px] text-[var(--text-3)]">
        бросают 40%, советов больше всего
      </div>
    </div>
  </div>
</template>

<style scoped>
.preview {
  position: relative;
}

@media (min-width: 1100px) {
  .preview { padding-bottom: 46px; }
}

.preview__card {
  position: relative;
  z-index: 1;
  padding: 22px;
  border-radius: 16px;
  background: var(--card);
  border: 1px solid var(--line);
  box-shadow: var(--shadow-lg);
}

.preview__text :deep(strong) {
  color: var(--foreground);
  font-weight: 600;
}

.preview__text :deep(code) {
  font-family: var(--font-mono);
  font-size: .86em;
  padding: .1em .35em;
  border-radius: 5px;
  background: var(--wash);
  border: 1px solid var(--line);
}

.sthread {
  display: flex;
  align-items: center;
  margin-top: 14px;
}

.sthread__node {
  flex: none;
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--text-4);
  background: var(--card);
  border: 1.5px solid var(--line-2);
  transition: background .25s, border-color .25s, color .25s;
}

.sthread__node.is-done {
  color: #fff;
  background: var(--thread);
  border-color: var(--thread);
}

.sthread__node.is-now {
  color: var(--thread);
  border-color: var(--thread);
  box-shadow: 0 0 0 3px var(--thread-wash);
}

.sthread__seg {
  flex: 1;
  height: 2px;
  min-width: 4px;
  background-image: linear-gradient(90deg, var(--line-2) 0 4px, transparent 4px 7px);
  background-size: 7px 2px;
  background-repeat: repeat-x;
}

.sthread__seg.is-done {
  background: var(--thread);
}

.sthread__knot {
  flex: none;
  width: 22px;
  height: 22px;
  margin-left: 2px;
  overflow: visible;
}

.sthread__knot path {
  fill: none;
  stroke: var(--line-2);
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: stroke .3s;
}

.sthread__knot.is-done path {
  stroke: var(--thread);
}

.preview__note {
  position: absolute;
  z-index: 2;
  right: -18px;
  bottom: 0;
  display: none;
  padding: 10px 14px;
  border-radius: 10px;
  background: var(--card);
  border: 1px solid var(--line);
  border-left: 3px solid var(--thread);
  box-shadow: var(--shadow-md);
  transform: rotate(-1.2deg);
}

@media (min-width: 1100px) {
  .preview__note { display: block; }
}

.pcheck {
  display: flex;
  align-items: center;
  gap: 11px;
  width: 100%;
  min-height: 42px;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 14.5px;
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
  width: 19px;
  height: 19px;
  border-radius: 5px;
  color: transparent;
  border: 1.5px solid var(--line-2);
  transition: background .15s, border-color .15s, color .15s;
}

.pcheck--on {
  color: var(--text-3);
  background: var(--background);
}

.pcheck--on > span:last-child {
  text-decoration: line-through;
  text-decoration-color: color-mix(in srgb, var(--thread) 60%, transparent);
}

.pcheck--on .pcheck__box {
  color: #fff;
  background: var(--thread);
  border-color: var(--thread);
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
</style>
