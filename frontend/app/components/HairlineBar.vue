<script setup lang="ts">
const props = withDefaults(defineProps<{ value: number, head?: boolean }>(), { head: true })
const v = computed(() => Math.min(1, Math.max(0, props.value)))
</script>

<template>
  <div class="hairline" role="progressbar" :aria-valuenow="Math.round(v * 100)" aria-valuemin="0" aria-valuemax="100">
    <span class="hairline__fill" :style="{ transform: `scaleX(${v})` }" />
    <span v-if="head && v > 0" class="hairline__head" :style="{ left: `${v * 100}%` }" />
  </div>
</template>
