<script setup lang="ts">
import { ArrowLeft, Compass } from '@lucide/vue'
import type { NuxtError } from '#app'

const props = defineProps<{ error: NuxtError }>()

const notFound = computed(() => props.error.statusCode === 404)
const title = computed(() => (notFound.value ? 'Нить оборвалась' : 'Что-то пошло не так'))
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
  <div class="relative min-h-dvh flex flex-col">
    <LiquidBackdrop />
    <header class="px-4 pt-4">
      <div class="glass glass--pill mx-auto max-w-[1180px] h-[58px] flex items-center px-4">
        <button aria-label="На главную" @click="go('/')">
          <BrandMark />
        </button>
      </div>
    </header>
    <main class="flex-1 grid place-items-center px-5 py-16">
      <div class="text-center max-w-xl">
        <img src="/glass/ring.webp" alt="" class="err__blob">
        <div class="display silver halo text-[110px] md:text-[168px] leading-[.9]" style="--lh: .9em">
          {{ error.statusCode || 500 }}
        </div>
        <h1 class="mt-4 text-[28px] md:text-[36px] font-extrabold tracking-[-0.03em]">
          {{ title }}
        </h1>
        <p class="mt-3 text-[16px] text-[var(--text-3)] leading-relaxed">
          {{ message }}
        </p>
        <div class="mt-8 flex flex-wrap justify-center gap-3">
          <button class="btn-chrome" @click="go('/')">
            <ArrowLeft class="size-4" /> На главную
          </button>
          <button class="btn-glass" @click="go('/guides')">
            <Compass class="size-4" /> Каталог инструкций
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.err__blob {
  width: min(260px, 60vw);
  margin: 0 auto -60px;
  opacity: .9;
  animation: float 7s ease-in-out infinite alternate;
  filter: drop-shadow(0 30px 50px rgba(0, 0, 0, .45));
}

@keyframes float {
  to { transform: translateY(-14px) rotate(-8deg); }
}
</style>
