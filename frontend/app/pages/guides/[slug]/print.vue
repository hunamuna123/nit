<script setup lang="ts">
import { ArrowLeft, Printer } from '@lucide/vue'
import { renderSVG } from 'uqr'
import type { GuideDetail } from '~/types/api'

definePageMeta({ layout: false })

const route = useRoute()
const slug = computed(() => String(route.params.slug))
const { data: guide, error } = await useFetch<GuideDetail>(() => `/api/guides/${slug.value}`, { key: `print-${slug.value}` })
if (error.value) throw createError({ statusCode: 404, statusMessage: 'Инструкция не найдена', fatal: true })
const { data: categories } = useCategories()

const url = computed(() => `${useRequestURL().origin}/guides/${slug.value}`)
const qr = computed(() => renderSVG(url.value, { border: 1, pixelSize: 4, blackColor: '#111', whiteColor: '#fff' }))
const printedAt = new Date().toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })

useHead(() => ({
  title: `${guide.value?.title ?? 'Инструкция'} — PDF`,
  htmlAttrs: { style: 'background:#fff;color-scheme:light' },
  bodyAttrs: { style: 'background:#fff' },
}))

function print() {
  window.print()
}
</script>

<template>
  <div v-if="guide" class="paper">
    <div class="toolbar no-print">
      <NuxtLink :to="`/guides/${guide.slug}`" class="tb-btn">
        <ArrowLeft class="size-4" /> К инструкции
      </NuxtLink>
      <span class="text-[13px] text-[#666] hidden sm:inline">В диалоге печати выберите «Сохранить как PDF»</span>
      <button class="tb-btn tb-btn--primary" @click="print">
        <Printer class="size-4" /> Сохранить как PDF
      </button>
    </div>

    <article class="sheet">
      <header class="head">
        <div class="min-w-0">
          <BrandMark size="sm" />
          <div class="meta tabular-nums mt-6">
            {{ categoryTitle(categories, guide.category) }} · v{{ guide.version.number }}
            <template v-if="guide.verified">
              · проверено экспертом
            </template>
          </div>
          <h1 class="title">
            {{ guide.title }}
          </h1>
          <p class="summary">
            {{ guide.summary }}
          </p>
          <div class="facts tabular-nums">
            <span>{{ pl(guide.steps_count, 'шаг', 'шага', 'шагов') }}</span>
            <span>≈ {{ formatMinutes(guide.est_minutes) }}</span>
            <span>сложность: {{ DIFFICULTY[guide.difficulty]?.toLowerCase() }}</span>
            <span>автор: {{ guide.author.name }}</span>
          </div>
        </div>
        <div class="qr">
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div class="qr__img" v-html="qr" />
          <div class="qr__cap">
            Пройти онлайн<br>с прогрессом
          </div>
        </div>
      </header>

      <ol class="steps">
        <li v-for="(s, i) in guide.steps" :key="s.key" class="step">
          <div class="step__head">
            <span class="step__num">{{ i + 1 }}</span>
            <h2 class="step__title">
              {{ s.title }}
            </h2>
            <span class="step__time tabular-nums">≈ {{ formatMinutes(s.minutes) }}</span>
          </div>
          <MarkdownView :source="s.body" class="step__body" />
          <ul v-if="s.checklist.length" class="checklist">
            <li v-for="c in s.checklist" :key="c.key">
              <span class="box" />{{ c.text }}
            </li>
          </ul>
        </li>
      </ol>

      <footer class="foot tabular-nums">
        <span>Нить · {{ url }}</span>
        <span>{{ printedAt }}</span>
      </footer>
    </article>
  </div>
</template>

<style scoped>
/* бумага: перебиваем токены чтоб печаталось черным по белому */
.paper {
  --foreground: #111214;
  --text-2: #26282d;
  --text-3: #45484f;
  --text-4: #6b6f77;
  --line: #e3e5e9;
  --line-2: #d4d7dc;
  --wash: #f4f5f7;
  --wash-2: #eceef1;
  --ice: #1f5fae;
  --ice-wash: #eef4fb;
  --primary: #2f54eb;
  --primary-foreground: #fff;
  --subtle: #f7f7f8;
  --card: #fff;
  min-height: 100dvh;
  background: #fff;
  color: #111214;
  font-family: var(--font-sans);
}

.toolbar {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  max-width: 860px;
  margin: 0 auto;
  padding: 14px 20px;
  background: rgba(255, 255, 255, .92);
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #eceef1;
}

.tb-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  padding: 0 16px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 600;
  color: #111214;
  background: #f1f2f4;
  transition: background .2s;
}

.tb-btn:hover {
  background: #e6e8eb;
}

.tb-btn--primary {
  color: #fff;
  background: #111214;
}

.tb-btn--primary:hover {
  background: #2a2d33;
}

.sheet {
  max-width: 860px;
  margin: 0 auto;
  padding: 40px 40px 56px;
}

.head {
  display: flex;
  justify-content: space-between;
  gap: 28px;
  padding-bottom: 26px;
  border-bottom: 2px solid #111214;
}

.meta {
  font-size: 11.5px;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: #6b6f77;
}

.title {
  margin-top: 10px;
  font-size: 34px;
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -.03em;
}

.summary {
  margin-top: 10px;
  font-size: 15px;
  line-height: 1.55;
  color: #34373d;
}

.facts {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 18px;
  margin-top: 14px;
  font-size: 12px;
  color: #45484f;
}

.qr {
  flex: none;
  width: 124px;
  text-align: center;
}

.qr__img :deep(svg) {
  width: 116px;
  height: 116px;
  display: block;
  margin: 0 auto;
}

.qr__cap {
  margin-top: 6px;
  font-size: 11px;
  line-height: 1.3;
  color: #6b6f77;
}

.steps {
  margin-top: 8px;
}

.step {
  padding: 22px 0;
  border-bottom: 1px solid #e3e5e9;
  break-inside: avoid;
}

.step__head {
  display: flex;
  align-items: baseline;
  gap: 14px;
}

.step__num {
  font-size: 20px;
  font-weight: 700;
  color: #9a9ea6;
  flex: none;
  width: 36px;
}

.step__title {
  flex: 1;
  font-size: 19px;
  font-weight: 750;
  line-height: 1.25;
  letter-spacing: -.015em;
}

.step__time {
  flex: none;
  font-size: 11.5px;
  color: #6b6f77;
}

.step__body {
  margin: 10px 0 0 50px;
  font-size: 14.5px;
  line-height: 1.6;
}

.step__body :deep(pre) {
  background: #f4f5f7;
  box-shadow: inset 0 0 0 1px #e3e5e9;
}

.step__body :deep(code) {
  background: #f1f2f4;
  box-shadow: none;
}

.step__body :deep(blockquote) {
  background: #f4f6fa;
  box-shadow: inset 3px 0 0 #9aa6b8;
}

.step__body :deep(ul > li::before) {
  background: #45484f;
  box-shadow: none;
}

.checklist {
  margin: 14px 0 0 50px;
  display: grid;
  gap: 8px;
}

.checklist li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 14px;
  line-height: 1.4;
}

.box {
  flex: none;
  width: 16px;
  height: 16px;
  margin-top: 1px;
  border: 1.6px solid #111214;
  border-radius: 4px;
}

.foot {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 26px;
  font-size: 11px;
  color: #6b6f77;
}

@media (max-width: 640px) {
  .sheet {
    padding: 24px 18px 40px;
  }

  .head {
    flex-direction: column;
  }

  .step__body,
  .checklist {
    margin-left: 0;
  }
}

@media print {
  @page {
    size: A4;
    margin: 14mm 14mm 16mm;
  }

  .sheet {
    max-width: none;
    padding: 0;
  }

  .title {
    font-size: 28px;
  }
}
</style>
