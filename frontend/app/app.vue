<script setup lang="ts">
import 'vue-sonner/style.css'
import { Toaster } from '@/components/ui/sonner'

const colorMode = useColorMode()
useHead({
  meta: [{ name: 'theme-color', content: () => (colorMode.value === 'dark' ? '#1a1816' : '#f7f3ec') }],
})
</script>

<template>
  <NuxtRouteAnnouncer />
  <NuxtPwaManifest />
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
  <Toaster position="top-center" :theme="colorMode.value === 'dark' ? 'dark' : 'light'" />
</template>
