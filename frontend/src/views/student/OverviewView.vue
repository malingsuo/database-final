<script setup lang="ts">
import CheckGate from '@/components/CheckGate.vue'
import CheckOverview from '@/components/CheckOverview.vue'
</script>

<template>
  <CheckGate v-slot="{ result }">
    <CheckOverview :result="result" />
  </CheckGate>
</template>
