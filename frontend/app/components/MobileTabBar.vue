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
  <nav v-if="!hidden" class="tabbar no-print">
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
  left: 0;
  right: 0;
  bottom: 0;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  height: calc(58px + env(safe-area-inset-bottom, 0px));
  padding-bottom: env(safe-area-inset-bottom, 0px);
  background: var(--background);
  border-top: 1px solid var(--line);
}

@media (min-width: 768px) {
  .tabbar {
    display: none;
  }
}

.tab {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-4);
  transition: color .15s;
}

.tab::before {
  content: '';
  position: absolute;
  top: -1px;
  left: 30%;
  right: 30%;
  height: 2px;
  border-radius: 2px;
  background: transparent;
}

.tab--on {
  color: var(--foreground);
}

.tab--on::before {
  background: var(--thread);
}

.tab--on svg {
  color: var(--thread);
}
</style>
