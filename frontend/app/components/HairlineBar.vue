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
  height: 3px;
  border-radius: 3px;
  overflow: hidden;
  background-image: linear-gradient(90deg, var(--line-2) 0 6px, transparent 6px 10px);
  background-size: 10px 3px;
  background-repeat: repeat-x;
}

.track__fill {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: inherit;
  background: var(--thread);
  transition: width .4s var(--ease);
}

.stitches {
  display: flex;
  align-items: center;
  gap: 5px;
  height: 4px;
}

.stitch {
  flex: 1;
  height: 2px;
  border-radius: 2px;
  background: var(--line-2);
  transition: background .3s var(--ease), height .3s var(--ease);
}

.stitch--on {
  height: 3px;
  background: var(--thread);
}

.stitch--now {
  height: 3px;
  background: color-mix(in srgb, var(--thread) 35%, var(--line-2));
}
</style>
