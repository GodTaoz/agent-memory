import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'system'

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>('system')
  const isDark = ref(false)

  function initTheme() {
    // Load saved theme preference
    const saved = localStorage.getItem('theme-mode') as ThemeMode
    if (saved) {
      mode.value = saved
    }
    
    applyTheme()
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (mode.value === 'system') {
        applyTheme()
      }
    })
  }

  function setTheme(newMode: ThemeMode) {
    mode.value = newMode
    localStorage.setItem('theme-mode', newMode)
    applyTheme()
  }

  function toggleTheme() {
    if (mode.value === 'light') {
      setTheme('dark')
    } else if (mode.value === 'dark') {
      setTheme('light')
    } else {
      // If system, toggle to opposite of current
      setTheme(isDark.value ? 'light' : 'dark')
    }
  }

  function applyTheme() {
    let shouldBeDark = false

    if (mode.value === 'dark') {
      shouldBeDark = true
    } else if (mode.value === 'system') {
      shouldBeDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    }

    isDark.value = shouldBeDark
    
    if (shouldBeDark) {
      document.documentElement.setAttribute('data-theme', 'dark')
    } else {
      document.documentElement.removeAttribute('data-theme')
    }
  }

  return {
    mode,
    isDark,
    initTheme,
    setTheme,
    toggleTheme,
  }
})
