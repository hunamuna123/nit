<script setup lang="ts">
import { ArrowUpRight, Sparkles } from '@lucide/vue'

const { brand } = useAppConfig()

const columns = [
  {
    title: 'Продукт',
    links: [
      { to: '/guides', label: 'Каталог' },
      { to: '/me', label: 'Мои прохождения' },
      { to: '/about', label: 'Как это работает' },
    ],
  },
  {
    title: 'Авторам',
    links: [
      { to: '/studio/new', label: 'Написать инструкцию' },
      { to: '/studio', label: 'Студия и аналитика' },
      { to: '/studio/inbox', label: 'Входящие правки' },
    ],
  },
  {
    title: 'Проект',
    links: [
      { to: '/about', label: 'О проекте' },
      { href: '/api/docs', label: 'API' },
      { href: 'https://github.com/hunamuna123/nit', label: 'GitHub' },
    ],
  },
]
</script>

<template>
  <footer class="footer no-print">
    <div class="mx-auto max-w-[1200px] px-5">
      <div class="footer__top">
        <div class="max-w-[300px]">
          <NuxtLink to="/" aria-label="На главную">
            <BrandMark />
          </NuxtLink>
          <p class="mt-3 text-[14px] leading-relaxed text-[var(--text-3)]">
            {{ brand.tagline }}. Чек-листы, прогресс без регистрации и аналитика для авторов.
          </p>
          <NuxtLink to="/studio/new" class="btn-secondary btn-sm mt-5">
            Написать инструкцию
          </NuxtLink>
        </div>

        <nav class="footer__cols" aria-label="Навигация по сайту">
          <div v-for="c in columns" :key="c.title">
            <h3 class="text-[13px] font-semibold text-[var(--foreground)]">
              {{ c.title }}
            </h3>
            <ul class="mt-3 space-y-2.5">
              <li v-for="l in c.links" :key="l.label">
                <a v-if="l.href" :href="l.href" target="_blank" rel="noopener" class="footer__link">
                  {{ l.label }}<ArrowUpRight class="size-3.5 opacity-60" />
                </a>
                <NuxtLink v-else :to="l.to!" class="footer__link">
                  {{ l.label }}
                </NuxtLink>
              </li>
            </ul>
          </div>
        </nav>
      </div>

      <div class="footer__bottom">
        <span>© 2026 «{{ brand.name }}»</span>
        <span class="inline-flex items-center gap-1.5">
          <Sparkles class="size-3.5" />ИИ — GigaChat
        </span>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  margin-top: 96px;
  padding-bottom: calc(58px + env(safe-area-inset-bottom, 0px));
  border-top: 1px solid var(--line);
  background: var(--subtle);
}

@media (min-width: 768px) {
  .footer { padding-bottom: 0; }
}

.footer__top {
  display: grid;
  gap: 40px;
  padding: 48px 0 40px;
}

@media (min-width: 768px) {
  .footer__top {
    grid-template-columns: 1fr auto;
    gap: 64px;
  }
}

.footer__cols {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 32px 24px;
}

@media (min-width: 640px) {
  .footer__cols {
    grid-template-columns: repeat(3, minmax(140px, 1fr));
    gap: 48px;
  }
}

.footer__link {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 14px;
  color: var(--text-3);
  transition: color .15s;
}

.footer__link:hover {
  color: var(--foreground);
}

.footer__bottom {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 8px 24px;
  padding: 18px 0 22px;
  border-top: 1px solid var(--line);
  font-size: 13px;
  color: var(--text-4);
}
</style>
