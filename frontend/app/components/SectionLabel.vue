<script setup lang="ts">
defineProps<{ num?: string, code?: boolean }>()
</script>

<template>
  <span class="label label--caps halo">
    <span class="pearl" />
    <template v-if="num"><span>{{ num }}</span><span class="opacity-50">·</span></template>
    <span v-if="code" class="normal-case tracking-normal">&lt;<slot /> /&gt;</span>
    <span v-else><slot /></span>
  </span>
</template>
