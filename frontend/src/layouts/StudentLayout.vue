<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { DataLine, List, UploadFilled, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useCheckStore } from '@/stores/check'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const check = useCheckStore()

const activeMenu = computed(() => route.name as string)
const displayName = computed(() => auth.user?.account ?? '使用者')

async function handleLogout() {
  try {
    await ElMessageBox.confirm('確定要登出嗎？', '登出', {
      confirmButtonText: '登出',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  await auth.logout()
  check.reset()
  router.replace({ name: 'login' })
}
</script>

<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="brand">
        <el-icon :size="22"><DataLine /></el-icon>
        <span class="brand-text">畢業學分審核</span>
      </div>
      <el-menu :default-active="activeMenu" router class="menu">
        <el-menu-item index="overview" :route="{ name: 'overview' }">
          <el-icon><DataLine /></el-icon>
          <span>進度總覽</span>
        </el-menu-item>
        <el-menu-item index="inventory" :route="{ name: 'inventory' }">
          <el-icon><List /></el-icon>
          <span>學分盤點</span>
        </el-menu-item>
        <el-menu-item index="upload" :route="{ name: 'upload' }">
          <el-icon><UploadFilled /></el-icon>
          <span>上傳資料</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-title">學生畢業學分審核器</div>
        <div class="header-right">
          <el-tag type="info" effect="plain">學生</el-tag>
          <span class="account">{{ displayName }}</span>
          <el-button text :icon="SwitchButton" @click="handleLogout">登出</el-button>
        </div>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100vh;
}

.aside {
  background-color: #fff;
  border-right: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
}

.brand {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 20px;
  color: var(--el-color-primary);
  font-weight: 700;
  border-bottom: 1px solid var(--el-border-color-light);
}

.brand-text {
  font-size: 16px;
}

.menu {
  border-right: none;
  flex: 1;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid var(--el-border-color-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.account {
  font-weight: 500;
}

.main {
  padding: 24px;
  overflow-y: auto;
}
</style>
