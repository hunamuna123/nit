<script setup lang="ts">
withDefaults(defineProps<{ size?: 'sm' | 'md' | 'lg', word?: boolean }>(), { size: 'md', word: true })
const { brand } = useAppConfig()
</script>

<template>
  <span class="brand" :class="`brand--${size}`">
    <svg class="brand__mark" viewBox="0 0 32 32" aria-hidden="true">
      <path
        class="brand__thread"
        pathLength="1"
        d="M3 25c4 0 10-6.5 10-12.2C13 9.9 11.6 8 9.6 8S6.2 9.9 6.4 12.6c.3 4 3.6 7 7.9 10.9L28.5 8"
      />
    </svg>
    <span v-if="word" class="brand__word">{{ brand.name }}</span>
  </span>
</template>

<style scoped>
.brand {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--foreground);
  line-height: 1;
}

.brand__mark {
  width: 26px;
  height: 26px;
  flex: none;
  overflow: visible;
}

.brand__thread {
  fill: none;
  stroke: var(--primary);
  stroke-width: 2.9;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-dasharray: 1;
  stroke-dashoffset: 0;
}

/* на ховер нить перерисовывается заново */
a:hover > .brand .brand__thread,
.brand:hover .brand__thread {
  animation: thread-draw .9s var(--ease) both;
}

@keyframes thread-draw {
  from { stroke-dashoffset: 1; }
  to { stroke-dashoffset: 0; }
}

.brand__word {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -.03em;
}

.brand--sm .brand__mark { width: 22px; height: 22px; }
.brand--sm .brand__word { font-size: 16px; }
.brand--lg .brand__mark { width: 34px; height: 34px; }
.brand--lg .brand__word { font-size: 25px; }
</style>
