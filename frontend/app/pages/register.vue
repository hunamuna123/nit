<script setup lang="ts">
import { ChartNoAxesColumn, ListChecks, Sparkles, UserPlus } from '@lucide/vue'

useHead({ title: 'Регистрация' })

const auth = useAuth()
const route = useRoute()
const router = useRouter()

const name = ref('')
const email = ref('')
const password = ref('')
const error = ref<string | null>(null)
const loading = ref(false)

const next = computed(() => {
  const n = typeof route.query.next === 'string' ? route.query.next : ''
  return n.startsWith('/') && !n.startsWith('//') ? n : '/me'
})

async function submit() {
  error.value = null
  if (password.value.length < 6) {
    error.value = 'Пароль — минимум 6 символов'
    return
  }
  loading.value = true
  try {
    await auth.register(name.value.trim(), email.value.trim(), password.value)
    router.replace(next.value)
  }
  catch (e) {
    error.value = apiErrorMessage(e, 'Не удалось зарегистрироваться')
  }
  finally {
    loading.value = false
  }
}

const perks = [
  { icon: ListChecks, text: 'Прогресс на всех устройствах и история прохождений' },
  { icon: Sparkles, text: 'Свои инструкции с ИИ-помощником' },
  { icon: ChartNoAxesColumn, text: 'Аналитика: где ваши ученики спотыкаются' },
]
</script>

<template>
  <div class="auth-wrap">
    <div class="auth-card glass glass--lg rise">
      <BrandMark size="lg" />
      <h1 class="mt-7 text-[34px] font-extrabold leading-[1.05] tracking-[-0.03em] silver" style="--lh: 1.05em">
        Создать аккаунт
      </h1>
      <p class="mt-2 text-[15px] text-[var(--text-3)]">
        Минута — и можно писать свои инструкции, комментировать шаги и предлагать правки.
      </p>

      <form class="mt-7 space-y-3" @submit.prevent="submit">
        <label class="block">
          <span class="label mb-2 block">как вас зовут</span>
          <input v-model="name" autocomplete="name" required minlength="2" maxlength="60" class="field" placeholder="Аня Смирнова">
        </label>
        <label class="block">
          <span class="label mb-2 block">email</span>
          <input v-model="email" type="email" autocomplete="email" required class="field" placeholder="you@example.ru">
        </label>
        <label class="block">
          <span class="label mb-2 block">пароль</span>
          <input v-model="password" type="password" autocomplete="new-password" required minlength="6" class="field" placeholder="минимум 6 символов">
        </label>
        <p v-if="error" class="auth-error" role="alert">
          {{ error }}
        </p>
        <button class="btn-chrome w-full !mt-5" :disabled="loading">
          <UserPlus class="size-4" /> {{ loading ? 'Создаём…' : 'Зарегистрироваться' }}
        </button>
      </form>

      <p class="mt-4 text-[13px] text-[var(--text-4)] leading-snug">
        Уже проходили что-то гостем — прогресс и оценки перенесутся в новый аккаунт автоматически.
      </p>

      <div class="mt-6 pt-5 border-t border-[var(--line)] text-sm text-[var(--text-3)]">
        Уже есть аккаунт?
        <NuxtLink :to="{ path: '/login', query: route.query.next ? { next: route.query.next } : {} }" class="text-foreground underline underline-offset-4">
          Войти
        </NuxtLink>
      </div>
    </div>

    <div class="perks glass rise" style="--i: 2">
      <div class="label label--caps">
        <span class="pearl" />что даёт аккаунт
      </div>
      <ul class="mt-4 space-y-3">
        <li v-for="p in perks" :key="p.text" class="flex items-start gap-3 text-[14.5px] text-[var(--text-2)]">
          <span class="ico size-9 shrink-0"><component :is="p.icon" class="size-4" /></span>
          <span class="pt-1.5 leading-snug">{{ p.text }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.auth-wrap {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 16px;
  max-width: 980px;
  margin: 0 auto;
  padding: 48px 16px 0;
  align-items: start;
}

@media (min-width: 900px) {
  .auth-wrap {
    grid-template-columns: minmax(0, 460px) 340px;
    justify-content: center;
    padding-top: 72px;
  }
}

.auth-card {
  padding: 32px 26px;
}

@media (min-width: 640px) {
  .auth-card {
    padding: 40px 40px 34px;
  }
}

.auth-error {
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 14px;
  color: var(--crit);
  background: var(--crit-wash);
}

.perks {
  padding: 22px;
}
</style>
