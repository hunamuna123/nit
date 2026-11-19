<script setup lang="ts">
definePageMeta({ layout: 'bare' })
const route = useRoute()
const slug = computed(() => String(route.params.slug))
useHead({ title: 'Прохождение' })
</script>

<template>
  <RunPlayer :key="slug" :slug="slug" />
</template>
