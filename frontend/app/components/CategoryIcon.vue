<script setup lang="ts">
import { Briefcase, Code, Cpu, FileText, GraduationCap, House, Layers, Wallet } from '@lucide/vue'

const props = defineProps<{ slug: string }>()
const icons = { study: GraduationCap, docs: FileText, hardware: Cpu, dev: Code, home: House, career: Briefcase, money: Wallet }
const icon = computed(() => icons[props.slug as keyof typeof icons] ?? Layers)
</script>

<template>
  <component :is="icon" />
</template>
