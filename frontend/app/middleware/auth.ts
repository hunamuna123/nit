export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuth()
  if (!auth.loaded) await auth.fetchMe()
  if (!auth.user) return navigateTo({ path: '/login', query: { next: to.fullPath } })
})
