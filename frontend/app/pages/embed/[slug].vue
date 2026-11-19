<script setup lang="ts">
definePageMeta({ layout: 'bare' })
const route = useRoute()
const slug = computed(() => String(route.params.slug))
useHead({ title: 'Виджет', meta: [{ name: 'robots', content: 'noindex' }] })
</script>

<template>
  <RunPlayer :key="slug" :slug="slug" embedded />
</template>
