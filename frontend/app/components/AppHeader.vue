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
      <NuxtLink to="/" class="header__brand" aria-label="На главную">
        <BrandMark />
      </NuxtLink>

      <nav class="header__nav">
        <NuxtLink v-for="l in links" :key="l.to" :to="l.to" class="nav-link" :class="isActive(l.to) && 'nav-link--on'">
          {{ l.label }}
        </NuxtLink>
      </nav>

      <div class="flex-1" />

      <button class="search-btn" aria-label="Поиск" @click="searchOpen = true">
        <Search class="size-[17px]" />
        <span class="search-btn__text">Найти инструкцию</span>
        <span class="kbd search-btn__kbd">⌘K</span>
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
          <button class="avatar-btn" aria-label="Меню профиля">
            <UserAvatar :id="auth.user.id" :name="auth.user.name" :size="34" />
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
      <NuxtLink v-else :to="{ path: '/login', query: { next: route.fullPath } }" class="btn-primary btn-sm header__login">
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
  background: var(--background);
  border-bottom: 1px solid var(--line);
}

.header__bar {
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: 1200px;
  height: var(--header-h);
  margin: 0 auto;
  padding: 0 20px;
}

/* ссылка флексом, иначе строчный бокс поднимает логотип над меню */
.header__brand {
  display: flex;
  align-items: center;
  flex: none;
  height: 100%;
  margin-right: 20px;
}

.header__nav {
  display: none;
  align-items: stretch;
  gap: 22px;
  height: 100%;
}

@media (min-width: 768px) {
  .header__nav { display: flex; }
}

.nav-link {
  position: relative;
  display: inline-flex;
  align-items: center;
  font-size: 14.5px;
  font-weight: 500;
  color: var(--text-3);
  transition: color .15s;
}

.nav-link::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 2px;
  border-radius: 2px;
  background: transparent;
  transition: background .15s;
}

.nav-link:hover {
  color: var(--foreground);
}

.nav-link--on {
  color: var(--foreground);
}

.nav-link--on::after {
  background: var(--thread);
}

.search-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  width: 260px;
  padding: 0 7px 0 11px;
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-4);
  background: var(--card);
  border: 1px solid var(--line-2);
  transition: border-color .15s, color .15s;
}

.search-btn__text {
  flex: 1;
  text-align: left;
}

.search-btn:hover {
  color: var(--text-3);
  border-color: var(--text-4);
}

@media (max-width: 1023px) {
  .search-btn {
    width: 36px;
    padding: 0;
    justify-content: center;
    color: var(--text-2);
    background: transparent;
  }

  .search-btn__text,
  .search-btn__kbd {
    display: none;
  }
}

.icon-btn {
  display: inline-grid;
  place-items: center;
  flex: none;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  color: var(--text-2);
  border: 1px solid var(--line-2);
  transition: border-color .15s, color .15s;
}

.icon-btn:hover,
.search-btn:hover {
  color: var(--foreground);
  border-color: var(--text-4);
}

.avatar-btn {
  display: grid;
  place-items: center;
  flex: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
}

.header__login {
  padding: 0 16px;
}
</style>
