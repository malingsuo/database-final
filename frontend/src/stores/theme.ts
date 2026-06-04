import { defineStore } from 'pinia'

export type ThemeName = 'ocean' | 'forest' | 'sunset' | 'grape'

export type ThemeOption = {
  name: ThemeName
  label: string
  color: string
}

const fallbackOption: ThemeOption = { name: 'ocean', label: '海洋藍', color: '#2563eb' }

export const themeOptions: ThemeOption[] = [
  fallbackOption,
  { name: 'forest', label: '森林綠', color: '#059669' },
  { name: 'sunset', label: '暖橘紅', color: '#ea580c' },
  { name: 'grape', label: '葡萄紫', color: '#7c3aed' },
]

const STORAGE_KEY = 'gradcheck_theme'
const fallbackTheme: ThemeName = 'ocean'

function isThemeName(value: string | null): value is ThemeName {
  return themeOptions.some((theme) => theme.name === value)
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    current: fallbackTheme as ThemeName,
  }),
  getters: {
    activeOption: (state) =>
      themeOptions.find((theme) => theme.name === state.current) ?? fallbackOption,
  },
  actions: {
    init() {
      if (typeof window === 'undefined') return
      const saved = window.localStorage.getItem(STORAGE_KEY)
      this.applyTheme(isThemeName(saved) ? saved : fallbackTheme)
    },
    applyTheme(theme: ThemeName) {
      this.current = theme
      if (typeof document !== 'undefined') {
        document.documentElement.dataset.theme = theme
      }
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(STORAGE_KEY, theme)
      }
    },
  },
})
