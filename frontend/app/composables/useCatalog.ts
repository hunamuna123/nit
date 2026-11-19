import type { CategoryOut } from '~/types/api'

export const COVERS = ['torus', 'peanut', 'drop', 'blob', 'ring', 'infinity'] as const

export function useCategories() {
  return useFetch<CategoryOut[]>('/api/meta/categories', { key: 'categories', default: () => [] })
}

export function categoryTitle(list: CategoryOut[] | null | undefined, slug: string): string {
  return list?.find(c => c.slug === slug)?.title ?? slug
}
