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
</script>

<template>
  <header class="header no-print">
    <div class="header__bar">
      <NuxtLink to="/" class="shrink-0 mr-4" aria-label="На главную">
        <BrandMark />
      </NuxtLink>

      <nav class="hidden md:flex items-center gap-1">
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
            <UserAvatar :id="auth.user.id" :name="auth.user.name" :size="32" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" class="w-60">
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
      <NuxtLink v-else :to="{ path: '/login', query: { next: route.fullPath } }" class="btn-primary btn-sm ml-1">
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
  background: color-mix(in srgb, var(--background) 92%, transparent);
  border-bottom: 1px solid var(--line);
  -webkit-backdrop-filter: saturate(140%) blur(8px);
  backdrop-filter: saturate(140%) blur(8px);
}

.header__bar {
  display: flex;
  align-items: center;
  gap: 4px;
  max-width: 1200px;
  height: var(--header-h);
  margin: 0 auto;
  padding: 0 20px;
}

.nav-link {
  height: 34px;
  display: inline-flex;
  align-items: center;
  padding: 0 10px;
  border-radius: 7px;
  font-size: 14.5px;
  font-weight: 500;
  color: var(--text-3);
  transition: color .15s, background .15s;
}

.nav-link:hover {
  color: var(--foreground);
  background: var(--wash);
}

.nav-link--on {
  color: var(--foreground);
}

.search-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 34px;
  min-width: 240px;
  padding: 0 6px 0 10px;
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-4);
  background: var(--subtle);
  border: 1px solid var(--line);
  transition: border-color .15s, color .15s;
}

.search-btn > span:nth-child(2) {
  flex: 1;
  text-align: left;
}

.search-btn:hover {
  color: var(--text-3);
  border-color: var(--line-2);
}

@media (max-width: 1023px) {
  .search-btn {
    min-width: 0;
    width: 34px;
    padding: 0;
    justify-content: center;
  }
}

.icon-btn {
  display: inline-grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  color: var(--text-3);
  transition: background .15s, color .15s;
}

.icon-btn:hover {
  color: var(--foreground);
  background: var(--wash);
}
</style>
