<script setup lang="ts">
const props = withDefaults(defineProps<{ name: string, id?: number, size?: number }>(), { id: 0, size: 32 })
const hue = computed(() => (props.id * 47) % 360)
</script>

<template>
  <span
    class="avatar"
    :style="{ width: `${size}px`, height: `${size}px`, fontSize: `${Math.round(size * 0.38)}px`, '--h': hue }"
    :title="name"
  >{{ initials(name) }}</span>
</template>

<style scoped>
.avatar {
  flex: none;
  display: inline-grid;
  place-items: center;
  border-radius: 50%;
  font-weight: 700;
  letter-spacing: -.02em;
  color: #0b0c0e;
  background:
    radial-gradient(circle at 32% 28%, rgba(255, 255, 255, .95) 0%, rgba(255, 255, 255, .4) 28%, transparent 60%),
    linear-gradient(140deg, hsl(var(--h) 60% 86%), hsl(calc(var(--h) + 40) 30% 62%));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .8), 0 0 0 1px rgba(255, 255, 255, .12), 0 4px 12px rgba(0, 0, 0, .3);
}
</style>
