// @ts-check
import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt(
  {
    // shadcn не трогаем
    files: ['app/components/ui/**/*.vue'],
    rules: {
      'vue/require-default-prop': 'off',
    },
  },
)
