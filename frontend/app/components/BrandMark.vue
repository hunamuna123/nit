<script setup lang="ts">
withDefaults(defineProps<{ size?: 'sm' | 'md' | 'lg' }>(), { size: 'md' })
const { brand } = useAppConfig()
</script>

<template>
  <span class="brand" :class="`brand--${size}`">
    <svg class="brand__thread" viewBox="0 0 40 24" fill="none" aria-hidden="true">
      <defs>
        <linearGradient id="nit-thread" x1="0" y1="0" x2="40" y2="0" gradientUnits="userSpaceOnUse">
          <stop offset="0" stop-color="currentColor" stop-opacity=".15" />
          <stop offset=".6" stop-color="currentColor" stop-opacity=".7" />
          <stop offset="1" stop-color="currentColor" />
        </linearGradient>
      </defs>
      <path d="M1 17 C 8 3, 14 3, 18 12 S 27 21, 31 9" stroke="url(#nit-thread)" stroke-width="2.2" stroke-linecap="round" />
    </svg>
    <span class="pearl brand__pearl" />
    <span class="brand__word display silver">{{ brand.name.toLowerCase() }}</span>
  </span>
</template>

<style scoped>
.brand {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  color: var(--foreground);
  line-height: 1;
}

.brand__thread {
  width: 30px;
  height: 18px;
  margin-right: -6px;
}

.brand__pearl {
  width: 9px;
  height: 9px;
  margin: 0 8px 0 0;
  transform: translateY(-5px);
}

.brand__word {
  font-size: 21px;
  letter-spacing: -.04em;
  --lh: 1em;
}

.brand--sm .brand__word { font-size: 17px; }
.brand--lg .brand__word { font-size: 30px; }
.brand--lg .brand__thread { width: 42px; height: 26px; }
</style>
