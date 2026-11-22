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
        d="M2.5 21.5c3.5 0 6.6-2.4 8.4-5.8 1.6-3 1.6-6.6-.9-7.4-2.6-.8-4.1 2.6-2.2 5.6l6.7 9.6L28.8 8.2"
      />
    </svg>
    <span v-if="word" class="brand__word">{{ brand.name }}</span>
  </span>
</template>

<style scoped>
.brand {
  display: inline-flex;
  align-items: center;
  gap: 8px;
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
  stroke: var(--thread);
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
  font-family: var(--font-serif);
  font-optical-sizing: auto;
  font-size: 21px;
  font-weight: 600;
  letter-spacing: -.01em;
  /* у литераты базовая линия низкая, чуть поднимаем под ось меню */
  transform: translateY(-1px);
}

.brand--sm .brand__mark { width: 22px; height: 22px; }
.brand--sm .brand__word { font-size: 17px; }
.brand--lg .brand__mark { width: 34px; height: 34px; }
.brand--lg .brand__word { font-size: 27px; }
</style>
