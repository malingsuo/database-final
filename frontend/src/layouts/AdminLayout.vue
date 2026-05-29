<template>
  <!-- 管理员通用布局 -->
  <div class="min-h-screen bg-slate-50">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// 这个布局组件为管理员页面提供统一的框架
// 当前实现简单，每个管理员页面都包含自己的导航栏
// 如需集中式导航栏，可以在此添加共享组件
</script>
