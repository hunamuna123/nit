<script setup lang="ts">
const { brand } = useAppConfig()
</script>

<template>
  <footer class="no-print mt-24 pb-28 md:pb-10">
    <div class="py-5 border-y border-[var(--line)] bg-[var(--wash)]">
      <MarqueeTicker :items="['чек-листы', 'шаг за шагом', 'узкие места', 'форки', 'эксперты', 'офлайн', 'pdf', 'встраивание', 'ии-редактор', 'умный поиск']" />
    </div>
    <div class="mx-auto max-w-[1180px] px-5 pt-8 flex flex-col md:flex-row gap-6 md:items-center justify-between">
      <div class="flex items-center gap-4">
        <BrandMark size="sm" />
        <span class="text-sm text-[var(--text-4)]">{{ brand.tagline }}</span>
      </div>
      <nav class="flex flex-wrap gap-x-6 gap-y-2 text-sm text-[var(--text-3)]">
        <NuxtLink to="/guides" class="hover:text-foreground">Каталог</NuxtLink>
        <NuxtLink to="/studio/new" class="hover:text-foreground">Написать инструкцию</NuxtLink>
        <NuxtLink to="/about" class="hover:text-foreground">Как это работает</NuxtLink>
        <a href="/api/docs" target="_blank" class="hover:text-foreground mono">API</a>
      </nav>
    </div>
  </footer>
</template>
