<template>
  <!-- 管理員通用佈局 -->
  <div class="min-h-screen bg-slate-50">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// 這個佈局元件為管理員頁面提供統一的框架
// 當前實現簡單，每個管理員頁面都包含自己的導航欄
// 如需集中式導航欄，可以在此新增共享元件
</script>
