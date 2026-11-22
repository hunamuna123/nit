<script setup lang="ts">
withDefaults(defineProps<{ cover: string, category: string, size?: number }>(), { size: 40 })
</script>

<template>
  <span class="cover" :class="`cover--${cover}`" :style="{ width: `${size}px`, height: `${size}px` }">
    <CategoryIcon :slug="category" :style="{ width: `${Math.round(size * 0.48)}px`, height: `${Math.round(size * 0.48)}px` }" />
  </span>
</template>

<style scoped>
.cover {
  flex: none;
  display: inline-grid;
  place-items: center;
  border-radius: 10px;
  color: var(--c);
  background: color-mix(in srgb, var(--c) 12%, transparent);
}

.cover--torus { --c: #2f54eb; }
.cover--peanut { --c: #16a34a; }
.cover--drop { --c: #d97706; }
.cover--blob { --c: #db2777; }
.cover--ring { --c: #7c3aed; }
.cover--infinity { --c: #0d9488; }

.dark .cover--torus { --c: #7b93fb; }
.dark .cover--peanut { --c: #4ade80; }
.dark .cover--drop { --c: #fbbf24; }
.dark .cover--blob { --c: #f472b6; }
.dark .cover--ring { --c: #a78bfa; }
.dark .cover--infinity { --c: #2dd4bf; }
</style>
