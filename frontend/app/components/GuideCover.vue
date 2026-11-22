<script setup lang="ts">
withDefaults(defineProps<{ cover: string, category: string, size?: number }>(), { size: 40 })
</script>

<template>
  <span class="cover" :class="`c-${cover}`" :style="{ width: `${Math.round(size * 0.8)}px`, height: `${size}px` }">
    <CategoryIcon :slug="category" :style="{ width: `${Math.round(size * 0.42)}px`, height: `${Math.round(size * 0.42)}px` }" />
  </span>
</template>

<style scoped>
.cover {
  flex: none;
  display: inline-grid;
  place-items: center;
  padding-left: 2px;
  border-radius: 3px 7px 7px 3px;
  color: #f7f3ec;
  background: var(--c, #6b655c);
  box-shadow: inset 3px 0 0 rgba(0, 0, 0, .16), inset 0 0 0 1px rgba(0, 0, 0, .06);
}

.dark .cover {
  color: #1a1816;
}
</style>
