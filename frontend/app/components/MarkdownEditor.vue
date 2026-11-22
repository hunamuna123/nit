<script setup lang="ts">
import { Bold, Code, Heading3, ImagePlus, Italic, Link2, List, ListOrdered, Quote, SquareCode, Strikethrough } from '@lucide/vue'
import Image from '@tiptap/extension-image'
import { Placeholder } from '@tiptap/extensions'
import { Markdown } from '@tiptap/markdown'
import StarterKit from '@tiptap/starter-kit'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import { toast } from 'vue-sonner'
import type { UploadOut } from '~/types/api'

const model = defineModel<string>({ default: '' })
const props = withDefaults(defineProps<{ placeholder?: string }>(), { placeholder: 'Опишите, что сделать на этом шаге…' })

const editor = useEditor({
  content: model.value,
  contentType: 'markdown',
  extensions: [
    StarterKit.configure({ heading: { levels: [3] }, link: { openOnClick: false } }),
    Markdown,
    Image,
    Placeholder.configure({ placeholder: props.placeholder }),
  ],
  editorProps: { attributes: { class: 'md md-editor' } },
  onUpdate: ({ editor }) => {
    model.value = editor.getMarkdown()
  },
})

// поменяли снаружи (ии, правка) - кидаем в редактор
watch(model, (value) => {
  const e = editor.value
  if (e && value !== e.getMarkdown()) e.commands.setContent(value, { contentType: 'markdown', emitUpdate: false })
})

onBeforeUnmount(() => editor.value?.destroy())

function setLink() {
  const e = editor.value
  if (!e) return
  const prev = e.getAttributes('link').href as string | undefined
  const url = window.prompt('Ссылка', prev ?? 'https://')
  if (url === null) return
  if (!url) e.chain().focus().unsetLink().run()
  else e.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
}

const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
async function upload(ev: Event) {
  const file = (ev.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    const r = await api<UploadOut>('/api/uploads/image', { method: 'POST', body: form })
    editor.value?.chain().focus().setImage({ src: r.url, alt: file.name }).run()
    toast.success('Картинка добавлена')
  }
  finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

type Btn = { icon: Component, label: string, run: () => void, active?: () => boolean }
const buttons = computed<Btn[]>(() => {
  const e = editor.value
  if (!e) return []
  const c = () => e.chain().focus()
  return [
    { icon: Bold, label: 'Жирный', run: () => c().toggleBold().run(), active: () => e.isActive('bold') },
    { icon: Italic, label: 'Курсив', run: () => c().toggleItalic().run(), active: () => e.isActive('italic') },
    { icon: Strikethrough, label: 'Зачёркнутый', run: () => c().toggleStrike().run(), active: () => e.isActive('strike') },
    { icon: Code, label: 'Код в строке', run: () => c().toggleCode().run(), active: () => e.isActive('code') },
    { icon: Heading3, label: 'Подзаголовок', run: () => c().toggleHeading({ level: 3 }).run(), active: () => e.isActive('heading') },
    { icon: List, label: 'Список', run: () => c().toggleBulletList().run(), active: () => e.isActive('bulletList') },
    { icon: ListOrdered, label: 'Нумерованный список', run: () => c().toggleOrderedList().run(), active: () => e.isActive('orderedList') },
    { icon: Quote, label: 'Подсказка (цитата)', run: () => c().toggleBlockquote().run(), active: () => e.isActive('blockquote') },
    { icon: SquareCode, label: 'Блок кода / команда', run: () => c().toggleCodeBlock().run(), active: () => e.isActive('codeBlock') },
    { icon: Link2, label: 'Ссылка', run: setLink, active: () => e.isActive('link') },
  ]
})
</script>

<template>
  <div class="editor">
    <div class="editor__bar">
      <button
        v-for="b in buttons"
        :key="b.label"
        type="button"
        class="editor__btn"
        :class="b.active?.() && 'editor__btn--on'"
        :title="b.label"
        :aria-label="b.label"
        @click="b.run"
      >
        <component :is="b.icon" class="size-4" />
      </button>
      <span class="w-px h-5 bg-[var(--line-2)] mx-1" />
      <button type="button" class="editor__btn" title="Загрузить картинку" :disabled="uploading" @click="fileInput?.click()">
        <ImagePlus class="size-4" :class="uploading && 'animate-pulse'" />
      </button>
      <input ref="fileInput" type="file" accept="image/png,image/jpeg,image/webp,image/gif" class="hidden" @change="upload">
    </div>
    <EditorContent :editor="editor" class="editor__body" />
  </div>
</template>

<style scoped>
.editor {
  border-radius: 10px;
  background: var(--card);
  border: 1px solid var(--input);
  transition: border-color .15s, box-shadow .15s;
}

.editor:focus-within {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ring) 18%, transparent);
}

.editor__bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px;
  padding: 4px;
  border-bottom: 1px solid var(--line);
  background: var(--subtle);
  border-radius: 10px 10px 0 0;
}

.editor__btn {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 6px;
  color: var(--text-3);
  transition: background .15s, color .15s;
}

.editor__btn:hover {
  color: var(--foreground);
  background: var(--wash-2);
}

.editor__btn--on {
  color: var(--foreground);
  background: var(--wash-2);
}

.editor__body :deep(.md-editor) {
  min-height: 150px;
  padding: 14px 18px 18px;
  outline: none;
  font-size: 15px;
}

.editor__body :deep(p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  height: 0;
  color: var(--text-4);
  pointer-events: none;
}
</style>
