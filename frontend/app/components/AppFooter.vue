<script setup lang="ts">
import { ArrowUpRight } from '@lucide/vue'

const columns = [
  {
    title: 'Ученикам',
    links: [
      { to: '/guides', label: 'Каталог инструкций' },
      { to: '/me', label: 'Мои прохождения' },
      { to: '/about', label: 'Как это устроено' },
    ],
  },
  {
    title: 'Авторам',
    links: [
      { to: '/studio/new', label: 'Написать инструкцию' },
      { to: '/studio', label: 'Студия и аналитика' },
      { to: '/studio/inbox', label: 'Предложенные правки' },
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
    <div class="footer__seam" aria-hidden="true" />
    <div class="mx-auto max-w-[1200px] px-5">
      <div class="footer__top">
        <div class="max-w-[320px]">
          <NuxtLink to="/" class="inline-flex" aria-label="На главную">
            <BrandMark />
          </NuxtLink>
          <p class="footer__lead">
            Инструкции, по которым задачу делают с первого раза: шаг за шагом, с чек-листом и советами тех, кто уже прошёл.
          </p>
          <NuxtLink to="/studio/new" class="btn-secondary btn-sm mt-5">
            Написать инструкцию
          </NuxtLink>
        </div>

        <nav class="footer__cols" aria-label="Навигация по сайту">
          <div v-for="c in columns" :key="c.title">
            <h3 class="footer__h">
              {{ c.title }}
            </h3>
            <ul class="mt-3.5 space-y-2.5">
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
        <span>© 2026 «Нить» · хакатон, трек «Веб-разработка»</span>
        <span>ИИ — GigaChat</span>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  position: relative;
  margin-top: 112px;
  padding-bottom: calc(58px + env(safe-area-inset-bottom, 0px));
  background: var(--subtle);
}

@media (min-width: 768px) {
  .footer { padding-bottom: 0; }
}

.footer__seam {
  height: 2px;
  background-image: linear-gradient(90deg, var(--thread) 0 12px, transparent 12px 20px);
  background-size: 20px 2px;
  background-repeat: repeat-x;
  opacity: .85;
}

.footer__top {
  display: grid;
  gap: 40px;
  padding: 52px 0 44px;
}

@media (min-width: 768px) {
  .footer__top {
    grid-template-columns: 1fr auto;
    gap: 64px;
  }
}

.footer__lead {
  margin-top: 14px;
  font-size: 14.5px;
  line-height: 1.6;
  color: var(--text-3);
}

.footer__cols {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 32px 24px;
}

@media (min-width: 640px) {
  .footer__cols {
    grid-template-columns: repeat(3, minmax(150px, 1fr));
    gap: 48px;
  }
}

.footer__h {
  font-family: var(--font-serif);
  font-size: 15px;
  font-weight: 600;
  color: var(--foreground);
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
  color: var(--thread);
}

.footer__bottom {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 8px 24px;
  padding: 18px 0 24px;
  border-top: 1px solid var(--line-2);
  font-size: 13px;
  color: var(--text-4);
}
</style>
