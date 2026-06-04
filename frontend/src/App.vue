<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'
import { useThemeStore } from '@/stores/theme'

const auth = useAuthStore()
const theme = useThemeStore()

theme.init()

onMounted(() => {
  if (auth.isAuthenticated && !auth.user) {
    auth.fetchStatus().catch(() => undefined)
  }
})
</script>

<template>
  <router-view />
  <ThemeSwitcher />
</template>
