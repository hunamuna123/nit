<script setup lang="ts">
import { ArrowLeft, Compass } from '@lucide/vue'
import type { NuxtError } from '#app'

const props = defineProps<{ error: NuxtError }>()

const notFound = computed(() => props.error.statusCode === 404)
const title = computed(() => (notFound.value ? 'Страница не найдена' : 'Что-то пошло не так'))
const message = computed(() =>
  notFound.value
    ? (props.error.statusMessage && !/^page not found/i.test(props.error.statusMessage)
        ? `${props.error.statusMessage}. Возможно, её удалили или ссылка с опечаткой.`
        : 'Такой страницы нет. Возможно, её удалили или ссылка с опечаткой.')
    : 'Мы уже знаем о проблеме. Попробуйте обновить страницу или вернуться на главную.',
)

useHead({ title: notFound.value ? 'Не найдено' : 'Ошибка' })

function go(path: string) {
  clearError({ redirect: path })
}
</script>

<template>
  <div class="min-h-dvh flex flex-col">
    <header class="border-b border-[var(--line)]">
      <div class="mx-auto max-w-[1200px] h-[60px] flex items-center px-5">
        <button aria-label="На главную" @click="go('/')">
          <BrandMark />
        </button>
      </div>
    </header>
    <main class="flex-1 grid place-items-center px-5 py-16">
      <div class="text-center max-w-md">
        <div class="text-[64px] font-bold tracking-[-0.04em] text-[var(--text-4)] tabular-nums leading-none">
          {{ error.statusCode || 500 }}
        </div>
        <h1 class="mt-4 text-[24px] font-bold tracking-[-0.02em]">
          {{ title }}
        </h1>
        <p class="mt-2 text-[15px] text-[var(--text-3)] leading-relaxed">
          {{ message }}
        </p>
        <div class="mt-7 flex flex-wrap justify-center gap-2">
          <button class="btn-primary" @click="go('/')">
            <ArrowLeft class="size-4" /> На главную
          </button>
          <button class="btn-secondary" @click="go('/guides')">
            <Compass class="size-4" /> Каталог
          </button>
        </div>
      </div>
    </main>
  </div>
</template>
