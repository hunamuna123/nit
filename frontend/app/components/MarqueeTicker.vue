<script setup lang="ts">
defineProps<{ items: string[] }>()
</script>

<template>
  <div class="marquee">
    <div class="marquee__track">
      <template v-for="n in 2" :key="n">
        <span v-for="(item, i) in items" :key="`${n}-${i}`" class="ticker">
          <span class="pearl pearl--sm" />{{ item }}
        </span>
      </template>
    </div>
  </div>
</template>

<style scoped>
.ticker {
  display: inline-flex;
  align-items: center;
  gap: 28px;
  padding-right: 28px;
  font-family: var(--font-display);
  font-weight: 600;
  font-size: clamp(16px, 2vw, 24px);
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--text-4);
  white-space: nowrap;
}
</style>
