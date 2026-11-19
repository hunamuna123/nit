<script setup lang="ts">
import { BookOpen, ClipboardCheck, LayoutDashboard, LogOut, Moon, PenLine, Search, Shield, Sun, User } from '@lucide/vue'

const auth = useAuth()
const route = useRoute()
const router = useRouter()
const colorMode = useColorMode()
const searchOpen = ref(false)

const links = [
  { to: '/guides', label: 'Каталог' },
  { to: '/studio', label: 'Студия' },
  { to: '/me', label: 'Мои прохождения' },
]

function isActive(to: string) {
  return route.path === to || route.path.startsWith(`${to}/`)
}

function toggleTheme() {
  colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
}

async function logout() {
  await auth.logout()
  router.push('/')
}

const scrolled = ref(false)
onMounted(() => {
  const onScroll = () => (scrolled.value = window.scrollY > 8)
  onScroll()
  window.addEventListener('scroll', onScroll, { passive: true })
  onBeforeUnmount(() => window.removeEventListener('scroll', onScroll))
})
</script>

<template>
  <header class="header no-print" :class="scrolled && 'header--scrolled'">
    <div class="header__bar glass glass--pill">
      <NuxtLink to="/" class="px-2 shrink-0" aria-label="На главную">
        <BrandMark />
      </NuxtLink>

      <nav class="hidden md:flex items-center gap-1 ml-3">
        <NuxtLink v-for="l in links" :key="l.to" :to="l.to" class="nav-link" :class="isActive(l.to) && 'nav-link--on'">
          {{ l.label }}
        </NuxtLink>
      </nav>

      <div class="flex-1" />

      <button class="search-btn" aria-label="Поиск" @click="searchOpen = true">
        <Search class="size-4" />
        <span class="hidden lg:inline">Найти инструкцию</span>
        <span class="kbd hidden lg:inline-grid">⌘K</span>
      </button>

      <button class="icon-btn" :aria-label="colorMode.value === 'dark' ? 'Светлая тема' : 'Тёмная тема'" @click="toggleTheme">
        <ClientOnly>
          <Sun v-if="colorMode.value === 'dark'" class="size-[18px]" />
          <Moon v-else class="size-[18px]" />
          <template #fallback>
            <Sun class="size-[18px]" />
          </template>
        </ClientOnly>
      </button>

      <DropdownMenu v-if="auth.user">
        <DropdownMenuTrigger as-child>
          <button class="rounded-full ml-1" aria-label="Меню профиля">
            <UserAvatar :id="auth.user.id" :name="auth.user.name" :size="36" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" class="w-60 rounded-2xl p-1.5">
          <DropdownMenuLabel class="px-2 py-2">
            <div class="font-semibold">
              {{ auth.user.name }}
            </div>
            <div class="text-xs text-muted-foreground font-normal truncate">
              {{ auth.user.email }} · {{ ROLE_LABEL[auth.user.role] }}
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem as-child>
            <NuxtLink :to="`/u/${auth.user.id}`"><User /> Профиль</NuxtLink>
          </DropdownMenuItem>
          <DropdownMenuItem as-child>
            <NuxtLink to="/me"><BookOpen /> Мои прохождения</NuxtLink>
          </DropdownMenuItem>
          <DropdownMenuItem as-child>
            <NuxtLink to="/studio"><LayoutDashboard /> Студия автора</NuxtLink>
          </DropdownMenuItem>
          <DropdownMenuItem as-child>
            <NuxtLink to="/studio/new"><PenLine /> Новая инструкция</NuxtLink>
          </DropdownMenuItem>
          <DropdownMenuItem v-if="auth.isExpert" as-child>
            <NuxtLink to="/review"><ClipboardCheck /> Проверка экспертом</NuxtLink>
          </DropdownMenuItem>
          <DropdownMenuItem v-if="auth.isAdmin" as-child>
            <NuxtLink to="/admin"><Shield /> Админка</NuxtLink>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem @click="logout">
            <LogOut /> Выйти
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <NuxtLink v-else :to="{ path: '/login', query: { next: route.fullPath } }" class="btn-chrome btn-chrome--sm ml-1">
        Войти
      </NuxtLink>
    </div>
    <SearchPalette v-model:open="searchOpen" />
  </header>
</template>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: 40;
  padding: 14px 16px 0;
  transition: padding .3s var(--ease);
}

.header__bar {
  display: flex;
  align-items: center;
  gap: 6px;
  max-width: 1180px;
  height: 58px;
  margin: 0 auto;
  padding: 0 8px 0 12px;
}

.header--scrolled .header__bar {
  box-shadow: var(--glass-hi), var(--glass-shadow);
}

.nav-link {
  height: 38px;
  display: inline-flex;
  align-items: center;
  padding: 0 14px;
  border-radius: 999px;
  font-size: 14.5px;
  font-weight: 500;
  color: var(--text-3);
  transition: color .2s, background .2s;
}

.nav-link:hover {
  color: var(--foreground);
  background: var(--wash);
}

.nav-link--on {
  color: var(--foreground);
  background: var(--wash-2);
  box-shadow: inset 0 0 0 1px var(--line);
}

.search-btn {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  height: 40px;
  padding: 0 8px 0 13px;
  border-radius: 999px;
  font-size: 14px;
  color: var(--text-3);
  background: var(--wash);
  box-shadow: inset 0 0 0 1px var(--line);
  transition: background .2s, color .2s;
}

.search-btn:hover {
  color: var(--foreground);
  background: var(--wash-2);
}

@media (max-width: 1023px) {
  .search-btn {
    width: 40px;
    padding: 0;
    justify-content: center;
  }
}

.icon-btn {
  display: inline-grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  color: var(--text-2);
  transition: background .2s, transform .16s var(--ease);
}

.icon-btn:hover {
  background: var(--wash);
}

.icon-btn:active {
  transform: scale(.9);
}
</style>
