<script setup lang="ts">
import 'vue-sonner/style.css'
import { Toaster } from '@/components/ui/sonner'

const colorMode = useColorMode()
useHead({
  meta: [{ name: 'theme-color', content: () => (colorMode.value === 'light' ? '#eef0f4' : '#0a0a0b') }],
})
</script>

<template>
  <NuxtRouteAnnouncer />
  <NuxtPwaManifest />
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
  <Toaster position="top-center" :theme="colorMode.value === 'light' ? 'light' : 'dark'" />
</template>
