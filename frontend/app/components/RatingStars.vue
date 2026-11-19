<script setup lang="ts">
import { Star } from '@lucide/vue'

const props = withDefaults(defineProps<{ value?: number | null, interactive?: boolean, size?: number }>(), {
  value: 0,
  interactive: false,
  size: 16,
})
const emit = defineEmits<{ select: [value: number] }>()
const hover = ref(0)
const shown = computed(() => hover.value || props.value || 0)
</script>

<template>
  <span class="inline-flex items-center gap-0.5" :class="interactive && 'cursor-pointer'" @mouseleave="hover = 0">
    <component
      :is="interactive ? 'button' : 'span'"
      v-for="i in 5"
      :key="i"
      type="button"
      class="star"
      :class="{ 'star--on': i <= Math.round(shown), 'star--btn': interactive }"
      :aria-label="interactive ? `${i} из 5` : undefined"
      @mouseenter="interactive && (hover = i)"
      @click="interactive && emit('select', i)"
    >
      <Star :style="{ width: `${size}px`, height: `${size}px` }" />
    </component>
  </span>
</template>

<style scoped>
.star {
  display: inline-grid;
  color: var(--text-4);
  transition: transform .2s var(--spring), color .2s;
}

.star :deep(svg) {
  fill: transparent;
}

.star--on {
  color: var(--foreground);
}

.star--on :deep(svg) {
  fill: currentColor;
  filter: drop-shadow(0 0 6px rgba(220, 230, 255, .35));
}

.star--btn:hover {
  transform: scale(1.18);
}
</style>
