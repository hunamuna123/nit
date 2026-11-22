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
  font-weight: 600;
  color: hsl(var(--h) 45% 32%);
  background: hsl(var(--h) 60% 90%);
}

.dark .avatar {
  color: hsl(var(--h) 60% 82%);
  background: hsl(var(--h) 30% 24%);
}
</style>
