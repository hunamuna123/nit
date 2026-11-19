<template>
  <div class="relative min-h-dvh flex flex-col">
    <LiquidBackdrop />
    <AppHeader />
    <main class="flex-1">
      <slot />
    </main>
    <AppFooter />
    <MobileTabBar />
  </div>
</template>
