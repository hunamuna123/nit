<script setup lang="ts">
const props = withDefaults(defineProps<{ value: number, parts?: boolean[], current?: number }>(), {
  parts: undefined,
  current: -1,
})
const v = computed(() => Math.min(1, Math.max(0, props.value)))
</script>

<template>
  <div
    v-if="parts?.length"
    class="stitches"
    role="progressbar"
    :aria-valuenow="Math.round(v * 100)"
    aria-valuemin="0"
    aria-valuemax="100"
  >
    <span
      v-for="(on, i) in parts"
      :key="i"
      class="stitch"
      :class="{ 'stitch--on': on, 'stitch--now': i === current && !on }"
    />
  </div>
  <div v-else class="track" role="progressbar" :aria-valuenow="Math.round(v * 100)" aria-valuemin="0" aria-valuemax="100">
    <span class="track__fill" :style="{ width: `${v * 100}%` }" />
  </div>
</template>

<style scoped>
.track {
  position: relative;
  height: 4px;
  border-radius: 4px;
  overflow: hidden;
  background: var(--wash-2);
}

.track__fill {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: inherit;
  background: var(--primary);
  transition: width .4s var(--ease);
}

.stitches {
  display: flex;
  gap: 3px;
  height: 4px;
}

.stitch {
  flex: 1;
  border-radius: 4px;
  background: var(--wash-2);
  transition: background .3s var(--ease);
}

.stitch--on {
  background: var(--primary);
}

.stitch--now {
  background: color-mix(in srgb, var(--primary) 30%, var(--wash-2));
}
</style>
