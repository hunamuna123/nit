<script setup lang="ts">
import { BookOpen, Compass, House, PenLine } from '@lucide/vue'

const route = useRoute()
const tabs = [
  { to: '/', label: 'Главная', icon: House, exact: true },
  { to: '/guides', label: 'Каталог', icon: Compass },
  { to: '/studio', label: 'Студия', icon: PenLine },
  { to: '/me', label: 'Мои', icon: BookOpen },
]
const hidden = computed(() => route.path.endsWith('/run') || route.path.startsWith('/embed'))
function on(t: (typeof tabs)[number]) {
  return t.exact ? route.path === t.to : route.path.startsWith(t.to)
}
</script>

<template>
  <nav v-if="!hidden" class="tabbar glass glass--pill no-print">
    <NuxtLink v-for="t in tabs" :key="t.to" :to="t.to" class="tab" :class="on(t) && 'tab--on'">
      <component :is="t.icon" class="size-5" />
      <span>{{ t.label }}</span>
    </NuxtLink>
  </nav>
</template>

<style scoped>
.tabbar {
  position: fixed;
  z-index: 40;
  left: 12px;
  right: 12px;
  bottom: calc(10px + env(safe-area-inset-bottom, 0px));
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  height: 64px;
  padding: 6px;
}

@media (min-width: 768px) {
  .tabbar {
    display: none;
  }
}

.tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-4);
  transition: color .2s, background .2s;
}

.tab--on {
  color: var(--foreground);
  background: var(--wash-2);
}
</style>
