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
  letter-spacing: .01em;
  color: hsl(var(--h) 32% 30%);
  background: hsl(var(--h) 34% 87%);
  box-shadow: inset 0 0 0 1px hsl(var(--h) 25% 78%);
}

.dark .avatar {
  color: hsl(var(--h) 40% 82%);
  background: hsl(var(--h) 20% 24%);
  box-shadow: inset 0 0 0 1px hsl(var(--h) 18% 32%);
}
</style>
