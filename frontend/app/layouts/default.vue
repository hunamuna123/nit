<template>
  <div class="min-h-dvh flex flex-col">
    <AppHeader />
    <main class="flex-1">
      <slot />
    </main>
    <AppFooter />
    <MobileTabBar />
  </div>
</template>
