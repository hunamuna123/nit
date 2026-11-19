<script setup lang="ts">
// фон с каплями, .glass поверх его блюрит. анимации только transform иначе лагает
const route = useRoute()

const scene = computed(() => {
  const p = route.path
  if (p === '/') return 'hero'
  if (p.endsWith('/run') || p.startsWith('/embed')) return 'quiet'
  if (p.startsWith('/guides/')) return 'guide'
  if (p.startsWith('/guides')) return 'catalog'
  if (p.startsWith('/studio') || p.startsWith('/review') || p.startsWith('/admin')) return 'studio'
  if (p.startsWith('/login') || p.startsWith('/register')) return 'auth'
  return 'app'
})
</script>

<template>
  <div class="liquid" :class="`liquid--${scene}`" aria-hidden="true">
    <div class="liquid__glow liquid__glow--a" />
    <div class="liquid__glow liquid__glow--b" />
    <img class="blob blob--1" src="/glass/torus.webp" alt="" decoding="async" fetchpriority="low">
    <img class="blob blob--2" src="/glass/peanut.webp" alt="" decoding="async" fetchpriority="low">
    <img class="blob blob--3" src="/glass/drop.webp" alt="" decoding="async" fetchpriority="low">
    <div class="liquid__grain" />
  </div>
</template>

<style scoped>
.liquid {
  position: fixed;
  inset: 0;
  z-index: -1;
  overflow: hidden;
  pointer-events: none;
  background: radial-gradient(120% 80% at 50% 0%, var(--bg-2) 0%, var(--background) 60%);
}

.liquid__glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(10px);
}

.liquid__glow--a {
  width: 110vmax;
  height: 110vmax;
  top: -60vmax;
  right: -52vmax;
  background: radial-gradient(circle, var(--glow) 0%, transparent 62%);
}

.liquid__glow--b {
  width: 90vmax;
  height: 90vmax;
  bottom: -58vmax;
  left: -50vmax;
  background: radial-gradient(circle, var(--glow-2) 0%, transparent 64%);
}

.liquid__grain {
  position: absolute;
  inset: 0;
  opacity: var(--grain-opacity);
  mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}

.blob {
  position: absolute;
  display: block;
  height: auto;
  opacity: var(--blob-opacity);
  will-change: transform;
  transition: top 1.4s var(--ease), left 1.4s var(--ease), right 1.4s var(--ease), bottom 1.4s var(--ease),
    width 1.4s var(--ease), opacity 1s var(--ease);
  filter: drop-shadow(0 30px 50px rgba(0, 0, 0, .45));
}

:root:not(.dark) .blob {
  filter: drop-shadow(0 24px 40px rgba(40, 50, 75, .18)) saturate(.9);
}

.blob--1 {
  width: clamp(260px, 30vw, 460px);
  top: 90px;
  right: -6vw;
  animation: drift-a 34s ease-in-out infinite alternate;
}

.blob--2 {
  width: clamp(200px, 22vw, 340px);
  top: 58vh;
  left: -8vw;
  animation: drift-b 41s ease-in-out infinite alternate;
}

.blob--3 {
  width: clamp(140px, 14vw, 240px);
  bottom: 4vh;
  right: 6vw;
  animation: drift-c 29s ease-in-out infinite alternate;
}

.liquid--hero .blob--1 { top: 70px; right: -2vw; width: clamp(320px, 42vw, 720px); opacity: min(1, calc(var(--blob-opacity) * 1.3)); }
.liquid--hero .blob--2 { top: 72vh; left: -10vw; }
.liquid--hero .blob--3 { bottom: -6vh; right: 30vw; }
.liquid--catalog .blob--1 { top: -6vh; right: -10vw; }
.liquid--catalog .blob--2 { top: 64vh; }
.liquid--guide .blob--1 { top: 12vh; right: -14vw; width: clamp(260px, 34vw, 520px); }
.liquid--guide .blob--3 { bottom: 8vh; right: auto; left: 4vw; }
.liquid--quiet .blob { opacity: calc(var(--blob-opacity) * .45); }
.liquid--quiet .blob--1 { top: 6vh; right: -16vw; }
.liquid--studio .blob--1 { top: -10vh; right: -12vw; width: clamp(220px, 26vw, 400px); }
.liquid--studio .blob--2 { top: 70vh; left: -12vw; opacity: calc(var(--blob-opacity) * .7); }
.liquid--studio .blob--3 { opacity: 0; }
.liquid--auth .blob--1 { top: 18vh; right: 8vw; width: clamp(280px, 34vw, 560px); opacity: min(1, calc(var(--blob-opacity) * 1.3)); }
.liquid--auth .blob--2 { top: 8vh; left: 6vw; width: clamp(140px, 14vw, 220px); }

@keyframes drift-a {
  0% { transform: translate3d(0, 0, 0) rotate(0deg) scale(1); }
  50% { transform: translate3d(-3vw, 3vh, 0) rotate(14deg) scale(1.06); }
  100% { transform: translate3d(-1vw, 6vh, 0) rotate(-8deg) scale(.97); }
}

@keyframes drift-b {
  0% { transform: translate3d(0, 0, 0) rotate(0deg) scale(1); }
  50% { transform: translate3d(4vw, -4vh, 0) rotate(-18deg) scale(1.08); }
  100% { transform: translate3d(2vw, 5vh, 0) rotate(10deg) scale(.95); }
}

@keyframes drift-c {
  0% { transform: translate3d(0, 0, 0) rotate(0deg); }
  100% { transform: translate3d(-4vw, -5vh, 0) rotate(24deg); }
}

@media (max-width: 768px) {
  .blob--1 { width: 72vw; right: -22vw; }
  .liquid--hero .blob--1 { width: 96vw; top: 80px; right: -30vw; opacity: .85; }
  .blob--2 { width: 56vw; left: -24vw; }
  .blob--3 { width: 40vw; }
}

@media (prefers-reduced-motion: reduce) {
  .blob { animation: none; }
}
</style>
