export default defineNuxtPlugin(async () => {
  const auth = useAuth()
  if (!auth.loaded) await auth.fetchMe()
})
