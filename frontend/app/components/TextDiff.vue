<script setup lang="ts">
const props = withDefaults(defineProps<{ before: string, after: string, mode?: 'diff' | 'preview' }>(), { mode: 'diff' })
const lines = computed(() => diffLines(props.before, props.after))
const stats = computed(() => ({
  add: lines.value.filter(l => l.kind === 'add').length,
  del: lines.value.filter(l => l.kind === 'del').length,
}))
</script>

<template>
  <div>
    <div class="flex items-center gap-2 mb-2">
      <span class="tag tag--ok mono">+{{ stats.add }}</span>
      <span class="tag tag--crit mono">−{{ stats.del }}</span>
    </div>
    <div v-if="mode === 'diff'" class="diff mono">
      <div v-for="(l, i) in lines" :key="i" class="diff__line" :class="`diff__line--${l.kind}`">
        <span class="diff__sign">{{ l.kind === 'add' ? '+' : l.kind === 'del' ? '−' : ' ' }}</span>
        <span class="whitespace-pre-wrap break-words">{{ l.text || ' ' }}</span>
      </div>
    </div>
    <div v-else class="grid gap-3 md:grid-cols-2">
      <div class="p-4 rounded-2xl bg-[var(--crit-wash)]">
        <div class="label mb-2">
          было
        </div>
        <MarkdownView :source="before" class="!text-[14px]" />
      </div>
      <div class="p-4 rounded-2xl bg-[var(--ok-wash)]">
        <div class="label mb-2">
          стало
        </div>
        <MarkdownView :source="after" class="!text-[14px]" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.diff {
  max-height: 420px;
  overflow: auto;
  border-radius: 16px;
  font-size: 12.5px;
  line-height: 1.6;
  background: rgba(0, 0, 0, .25);
  box-shadow: inset 0 0 0 1px var(--line);
}

:root:not(.dark) .diff {
  background: rgba(20, 25, 35, .04);
}

.diff__line {
  display: flex;
  gap: 10px;
  padding: 0 12px;
}

.diff__sign {
  flex: none;
  width: 10px;
  color: var(--text-4);
}

.diff__line--add {
  color: var(--ok);
  background: var(--ok-wash);
}

.diff__line--del {
  color: var(--crit);
  background: var(--crit-wash);
  text-decoration: line-through;
  text-decoration-color: color-mix(in srgb, var(--crit) 40%, transparent);
}

.diff__line--same {
  color: var(--text-3);
}
</style>
