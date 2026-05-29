<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

onMounted(() => {
  if (auth.isAuthenticated && !auth.user) {
    auth.fetchStatus().catch(() => undefined)
  }
})
</script>

<template>
  <router-view />
</template>
