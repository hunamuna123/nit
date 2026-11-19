<script setup lang="ts">
import { ArrowRight, BadgeCheck, LogIn, PenLine, Shield } from '@lucide/vue'

useHead({ title: 'Вход' })

const auth = useAuth()
const route = useRoute()
const router = useRouter()

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
  loading.value = true
  try {
    await auth.login(email.value.trim(), password.value)
    router.replace(next.value)
  }
  catch (e) {
    error.value = apiErrorMessage(e, 'Не удалось войти')
  }
  finally {
    loading.value = false
  }
}

const demos = [
  { email: 'demo@nit.demo', role: 'Автор', hint: '4 инструкции, аналитика и входящие правки', icon: PenLine },
  { email: 'igor.vlasov@nit.demo', role: 'Эксперт', hint: 'проверка инструкций по IT и железу', icon: BadgeCheck },
  { email: 'admin@nit.demo', role: 'Админ', hint: 'роли, заявки в эксперты, расход ИИ', icon: Shield },
]

async function demoLogin(addr: string) {
  email.value = addr
  password.value = 'demo1234'
  await submit()
}
</script>

<template>
  <div class="auth-wrap">
    <div class="auth-card glass glass--lg rise">
      <BrandMark size="lg" />
      <h1 class="mt-7 text-[34px] font-extrabold leading-[1.05] tracking-[-0.03em] silver" style="--lh: 1.05em">
        С возвращением
      </h1>
      <p class="mt-2 text-[15px] text-[var(--text-3)]">
        Войдите, чтобы писать инструкции, комментировать и видеть прогресс на всех устройствах.
      </p>

      <form class="mt-7 space-y-3" @submit.prevent="submit">
        <label class="block">
          <span class="label mb-2 block">email</span>
          <input v-model="email" type="email" autocomplete="email" required class="field" placeholder="you@example.ru">
        </label>
        <label class="block">
          <span class="label mb-2 block">пароль</span>
          <input v-model="password" type="password" autocomplete="current-password" required class="field" placeholder="••••••••">
        </label>
        <p v-if="error" class="auth-error" role="alert">
          {{ error }}
        </p>
        <button class="btn-chrome w-full !mt-5" :disabled="loading">
          <LogIn class="size-4" /> {{ loading ? 'Входим…' : 'Войти' }}
        </button>
      </form>

      <p class="mt-4 text-[13px] text-[var(--text-4)] leading-snug">
        Проходили инструкции гостем? После входа прогресс, оценки и голоса перенесутся в аккаунт.
      </p>

      <div class="mt-6 pt-5 border-t border-[var(--line)] text-sm text-[var(--text-3)]">
        Нет аккаунта?
        <NuxtLink :to="{ path: '/register', query: route.query.next ? { next: route.query.next } : {} }" class="text-foreground underline underline-offset-4">
          Зарегистрироваться
        </NuxtLink>
      </div>
    </div>

    <div class="demo glass rise" style="--i: 2">
      <div class="label label--caps">
        <span class="pearl" />демо-вход
      </div>
      <p class="mt-2 text-[13.5px] text-[var(--text-3)]">
        Для жюри: готовые аккаунты с данными. Пароль у всех — <span class="mono text-foreground">demo1234</span>.
      </p>
      <div class="mt-4 space-y-2">
        <button
          v-for="d in demos"
          :key="d.email"
          class="demo__btn"
          :disabled="loading"
          @click="demoLogin(d.email)"
        >
          <span class="ico size-9"><component :is="d.icon" class="size-4" /></span>
          <span class="flex-1 min-w-0 text-left">
            <span class="block font-semibold text-[14.5px]">{{ d.role }}</span>
            <span class="block text-[12.5px] text-[var(--text-4)] truncate">{{ d.hint }}</span>
          </span>
          <ArrowRight class="size-4 text-[var(--text-3)]" />
        </button>
      </div>
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

.demo {
  padding: 22px;
}

.demo__btn {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 10px 12px;
  border-radius: 16px;
  background: var(--wash);
  box-shadow: inset 0 0 0 1px var(--line);
  transition: background .2s, transform .16s var(--ease);
}

.demo__btn:hover {
  background: var(--wash-2);
}

.demo__btn:active {
  transform: scale(.98);
}
</style>
